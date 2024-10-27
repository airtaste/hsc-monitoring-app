import asyncio
import random
import sys
import time
from asyncio import Task
from datetime import datetime
from typing import Optional

import telegram.error
from loguru import logger
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from auth.authenticator import Authenticator
from captcha.captcha_resolver import CaptchaResolver
from config.configuration import TELEGRAM_BOT_TOKEN_ID, CHAT_ID, HSC_OFFICE_ID, APPROVE_RESERVATION_RETRY_THRESHOLD, \
    REAUTH_THRESHOLD_HOURS, DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS, ALLOW_LIST
from exceptions.exceptions import ReservationApprovalException, ReservationException
from monitoring.slot_reserver import SlotReserver
from notification.notifier import Notifier
from utils.driver_utils import cleanup_browser, setup_chrome_driver


# Control variable to manage the running state of the search
search_task: Optional[Task] = None


async def search_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global search_task

    logger.info(f"Received '/search_stop' command from '{update.message.from_user.full_name}' with chat id '{update.message.chat_id}'")

    try:
        if update.message.chat_id not in ALLOW_LIST:
            await update.message.reply_text(f'⛔ У вас немає прав на запуск поточної команди. Зверніться за допомогою до адміна бота.')
            logger.warning(f"'Someone '{update.message.from_user.full_name}' is trying to interact with bot without permissions")
            return None

        if search_task:
            search_task.cancel()
            search_task = None

        await update.message.reply_text(f'Пошук зупинено.')
    except telegram.error.Forbidden:
        logger.error(f"'Cannot reply to the user '{update.message.from_user.full_name}'. Reason: bot was blocked by the user'")
        return None


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global search_task

    logger.info(f"Received '/search_start' command from '{update.message.from_user.full_name}' with chat id '{update.message.chat_id}'")

    try:
        if update.message.chat_id not in ALLOW_LIST:
            await update.message.reply_text(f'⛔ У вас немає прав на запуск поточної команди. Зверніться за допомогою до адміна бота.')
            return None

        if search_task:
            await update.message.reply_text(f'Пошук вже запущено.')
            return None
    except telegram.error.Forbidden:
        logger.error(f"'Cannot reply to the user '{update.message.from_user.full_name}'. Reason: bot was blocked by the user'")
        return None

    await update.message.reply_text(f'🔛 Запускаю пошук талонів в системі електронного запису МВС України...')

    async def run_search():
        global search_task

        has_reserved_slots = False

        try:
            while True:
                if has_reserved_slots:
                    logger.success("Congratulations! Program successfully reserved slot for practice exam!")
                    break

                auth_start = time.time()
                await authenticator.try_authenticate()

                while True:
                    auth_current = time.time()

                    if (auth_current - auth_start) / 3600 > REAUTH_THRESHOLD_HOURS:
                        logger.info("Seems like authentication session time exceeded. Need to perform re-authentication.")
                        driver.delete_all_cookies()
                        break

                    free_slots = await slot_reserver.get_free_slots()

                    if free_slots:
                        try:
                            slot = random.choice(free_slots)
                            reservation = await slot_reserver.reserve_slot(slot)
                        except ReservationException as e:
                            logger.error(f"Error during slot reservation: {str(e)}. Continuing without fallback...")
                            continue

                        for i in range(APPROVE_RESERVATION_RETRY_THRESHOLD):
                            try:
                                await slot_reserver.approve_reservation(reservation)
                                has_reserved_slots = True
                                break
                            except ReservationApprovalException:
                                logger.warning(f"Cannot approve reservation '{reservation.reservation_url}'. Trying again...")
                                if datetime.now() > reservation.expired_at:
                                    reservation = await slot_reserver.reserve_slot(slot)
                                await asyncio.sleep(15)
                                continue

                        if has_reserved_slots:
                            break

                    sleep_time = random.uniform(*DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS)
                    logger.info(f"Nothing was found during search attempt. Sleep for {sleep_time:.1f} seconds until next try...")
                    await asyncio.sleep(sleep_time)
        except Exception as e:
            await notifier.notify_error(e)
            logger.error(e)
        finally:
            search_task = None
            await cleanup_browser(driver)

    search_task = asyncio.create_task(run_search())

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    driver = setup_chrome_driver()
    tg_bot = Bot(token=TELEGRAM_BOT_TOKEN_ID)
    notifier = Notifier(bot=tg_bot, chat_id=CHAT_ID)
    captcha_resolver = CaptchaResolver(driver=driver)
    authenticator = Authenticator(driver=driver, notifier=notifier, captcha_resolver=captcha_resolver)
    slot_reserver = SlotReserver(driver=driver, notifier=notifier, captcha_resolver=captcha_resolver, office_id=HSC_OFFICE_ID)

    app = ApplicationBuilder().bot(tg_bot).build()

    app.add_handler(CommandHandler("search_start", search_start))
    app.add_handler(CommandHandler("search_stop", search_stop))

    app.run_polling()
