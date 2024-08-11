import random
import time
from datetime import datetime
from pathlib import Path
from time import sleep

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from auth.authenticator import Authenticator
from captcha.captcha_resolver import CaptchaResolver
from config.configuration import TELEGRAM_BOT_TOKEN_ID, CHAT_ID, HSC_OFFICE_ID, \
    REAUTH_THRESHOLD_HOURS, DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS, HEADLESS_MODE, HSC_OFFICE_LOCATION, \
    APPROVE_RESERVATION_RETRY_THRESHOLD, BROWSER_DOWNLOADS_FOLDER
from exceptions.exceptions import ReservationApprovalException
from monitoring.slot_reserver import SlotReserver
from notification.notifier import Notifier
from utils.driver_utils import cleanup_browser_cache

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    options.add_argument("--start-maximized")
    if HEADLESS_MODE:
        options.add_argument('--headless')
    options.add_argument("--disable-blink-features=AutomationControlled")
    prefs = {
        'download.default_directory': str(Path(BROWSER_DOWNLOADS_FOLDER).absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option('prefs', prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    chrome_service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=options)

    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", HSC_OFFICE_LOCATION)
    driver.execute_cdp_cmd("Browser.grantPermissions",
                           {"origin": "https://eq.hsc.gov.ua/", "permissions": ["geolocation"]})

    notifier = Notifier(token_id=TELEGRAM_BOT_TOKEN_ID, chat_id=CHAT_ID)
    captcha_resolver = CaptchaResolver(driver=driver)
    authenticator = Authenticator(driver=driver, notifier=notifier, captcha_resolver=captcha_resolver)
    slot_reserver = SlotReserver(driver=driver, notifier=notifier, captcha_resolver=captcha_resolver,
                                 office_id=HSC_OFFICE_ID)

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
                    slot = random.choice(free_slots)
                    reservation = slot_reserver.reserve_slot(slot)

                    for i in range(APPROVE_RESERVATION_RETRY_THRESHOLD):
                        try:
                            slot_reserver.approve_reservation(reservation)

                            has_reserved_slots = True
                            break
                        except ReservationApprovalException as e:
                            logger.warning(f"Cannot approve reservation '{reservation.reservation_url}'. Trying again...")
                            if datetime.now() > reservation.expired_at:
                                reservation = slot_reserver.reserve_slot(slot)

                            sleep(15)
                            continue

                    if has_reserved_slots:
                        break

                sleep_time = random.uniform(*DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS)
                logger.info(f"Nothing was found during search attempt. Sleep for {sleep_time:.1f} seconds until next try...")
                sleep(sleep_time)
    except Exception as e:
        logger.error(e)
    finally:
        cleanup_browser_cache(driver)
        driver.quit()
