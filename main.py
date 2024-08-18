import random
import time
from datetime import datetime
from time import sleep

from loguru import logger

from auth.authenticator import Authenticator
from captcha.captcha_resolver import CaptchaResolver
from config.configuration import TELEGRAM_BOT_TOKEN_ID, CHAT_ID, HSC_OFFICE_ID, APPROVE_RESERVATION_RETRY_THRESHOLD, \
    REAUTH_THRESHOLD_HOURS, DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS
from exceptions.exceptions import ReservationApprovalException, ReservationException
from monitoring.slot_reserver import SlotReserver
from notification.notifier import Notifier
from utils.driver_utils import cleanup_browser_cache, setup_chrome_driver


def main():
    has_reserved_slots = False

    try:
        while True:
            if has_reserved_slots:
                logger.success("Congratulations! Program successfully reserved slot for practice exam!")
                break

            auth_start = time.time()

            authenticator.try_authenticate()

            while True:
                auth_current = time.time()

                if (auth_current - auth_start) / 3600 > REAUTH_THRESHOLD_HOURS:
                    logger.info("Seems like authentication session time exceeded. Need to perform re-authentication.")
                    driver.delete_all_cookies()
                    break

                free_slots = slot_reserver.get_free_slots()

                if free_slots:
                    try:
                        slot = random.choice(free_slots)
                        reservation = slot_reserver.reserve_slot(slot)
                    except ReservationException as e:
                        logger.error(f"Error during slot reservation: {str(e)}. Continuing without fallback...")
                        continue

                    for i in range(APPROVE_RESERVATION_RETRY_THRESHOLD):
                        try:
                            slot_reserver.approve_reservation(reservation)

                            has_reserved_slots = True
                            break
                        except ReservationApprovalException:
                            logger.warning(f"Cannot approve reservation '{reservation.reservation_url}'. Trying again...")
                            if datetime.now() > reservation.expired_at:
                                reservation = slot_reserver.reserve_slot(slot)

                            sleep(15)
                            continue

                    if has_reserved_slots:
                        break

                sleep_time = random.uniform(*DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS)
                logger.info(
                    f"Nothing was found during search attempt. Sleep for {sleep_time:.1f} seconds until next try...")
                sleep(sleep_time)
    except Exception as e:
        logger.error(e)
    finally:
        cleanup_browser_cache(driver)
        driver.quit()


if __name__ == '__main__':
    driver = setup_chrome_driver()
    notifier = Notifier(token_id=TELEGRAM_BOT_TOKEN_ID, chat_id=CHAT_ID)
    captcha_resolver = CaptchaResolver(driver=driver)
    authenticator = Authenticator(driver=driver, notifier=notifier, captcha_resolver=captcha_resolver)
    slot_reserver = SlotReserver(driver=driver, notifier=notifier, captcha_resolver=captcha_resolver, office_id=HSC_OFFICE_ID)
    main()
