import asyncio
import random
import threading
import time
from datetime import datetime

from loguru import logger
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from auth.authenticator import Authenticator
from captcha.captcha_resolver import CaptchaResolver
from config.configuration import TELEGRAM_BOT_TOKEN_ID, CHAT_ID, HSC_OFFICE_ID, APPROVE_RESERVATION_RETRY_THRESHOLD, \
    REAUTH_THRESHOLD_HOURS, DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS
from exceptions.exceptions import ReservationApprovalException, ReservationException
from monitoring.slot_reserver import SlotReserver
from notification.notifier import Notifier
from utils.driver_utils import cleanup_browser_cache, setup_chrome_driver


# Control variable to manage the running state of the search
is_search_running = False
search_thread = None


async def search_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global is_search_running
    is_search_running = False
    logger.info(f"Received '/search_stop' command from '{update.message.from_user.full_name}' with chat id '{update.message.chat_id}'")
    await update.message.reply_text(f'Пошук зупинено.')


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global is_search_running, search_thread

    logger.info(f"Received '/search_start' command from '{update.message.from_user.full_name}' with chat id '{update.message.chat_id}'")

    if update.message.chat_id != CHAT_ID:
        await update.message.reply_text(f'У вас немає прав на запуск поточної команди. Зверніться за допомогою до адміна бота.')
        return

    if is_search_running:
        await update.message.reply_text(f'Пошук вже запущено.')
        return

    await update.message.reply_text(f'Запускаю пошук талонів в системі електронного запису МВС України...')
    is_search_running = True

    async def run_search():
        global is_search_running
        has_reserved_slots = False

        try:
            while is_search_running:
                if has_reserved_slots:
                    logger.success("Congratulations! Program successfully reserved slot for practice exam!")
                    break

                auth_start = time.time()
                await authenticator.try_authenticate()

                while is_search_running:
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
                            if not is_search_running:
                                break
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

                        if has_reserved_slots or not is_search_running:
                            break

                    if not is_search_running:
                        break
                    sleep_time = random.uniform(*DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS)
                    logger.info(f"Nothing was found during search attempt. Sleep for {sleep_time:.1f} seconds until next try...")
                    await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.error(e)
        finally:
            await cleanup_browser_cache(driver)
            driver.delete_all_cookies()

    # Start the search in a separate thread
    loop = asyncio.get_event_loop()

    def run_search_in_thread():
        asyncio.run_coroutine_threadsafe(run_search(), loop)

    search_thread = threading.Thread(target=run_search_in_thread)
    search_thread.start()

if __name__ == '__main__':
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
