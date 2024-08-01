import time

from loguru import logger
import random
from time import sleep

from selenium.webdriver import Keys, ActionChains
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from auth.authenticator import Authenticator
from captcha.captcha_resolver import CaptchaResolver
from config.configuration import TELEGRAM_BOT_TOKEN_ID, CHAT_ID, HSC_OFFICE_ID_LVIV, \
    REAUTH_TIME_WINDOW_SECONDS, DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS
from notification.notifier import Notifier
from monitoring.slot_reserver import SlotReserver
from utils.captcha_utils import perform_with_captcha_guard

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    options.add_argument("--start-maximized")
    # options.add_argument('--headless')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=options)

    driver.execute_cdp_cmd(
        "Emulation.setGeolocationOverride",
        {
            "latitude": 49.829620,
            "longitude": 23.941710,
            "accuracy": 200
        },
    )
    driver.execute_cdp_cmd(
        "Browser.grantPermissions",
        {
            "origin": "https://eq.hsc.gov.ua/",
            "permissions": ["geolocation"],
        },
    )

    notifier = Notifier(token_id=TELEGRAM_BOT_TOKEN_ID, chat_id=CHAT_ID)
    captcha_resolver = CaptchaResolver(driver=driver)
    authenticator = Authenticator(driver=driver, notifier=notifier)
    slot_reserver = SlotReserver(driver=driver, notifier=notifier, office_id=HSC_OFFICE_ID_LVIV)

    has_reserved_slots = False

    try:
        while True:
            if has_reserved_slots:
                logger.success("Congratulations! Program successfully reserved slot for practice exam!")
                break

            auth_start = time.time()

            driver.get("https://eq.hsc.gov.ua/")
            perform_with_captcha_guard(captcha_resolver, 0, authenticator.try_authenticate)

            while True:
                auth_current = time.time()
                driver.refresh()

                if (auth_current - auth_start) > REAUTH_TIME_WINDOW_SECONDS:
                    logger.info("Seems like authentication session time exceeded. Need to perform re-authentication.")
                    driver.delete_all_cookies()
                    break

                free_slots = perform_with_captcha_guard(captcha_resolver, 0, slot_reserver.get_free_slots)

                if free_slots:
                    logger.success("Found free slots! Reserving...")
                    slot = random.choice(free_slots)
                    perform_with_captcha_guard(captcha_resolver, 0, slot_reserver.reserve_slot_and_notify, slot)

                    has_reserved_slots = True
                    break

                sleep_time = random.uniform(*DELAYS_BETWEEN_SEARCH_ATTEMPT_SECONDS)
                logger.info(f"Nothing was found during search attempt. Sleep for {sleep_time:.1f} seconds until next try...")
                sleep(sleep_time)
    finally:
        # Cleanup browser cache
        driver.execute_script("window.open('');")
        sleep(2)
        driver.switch_to.window(driver.window_handles[-1])
        sleep(2)
        driver.get('chrome://settings/clearBrowserData')
        sleep(2)
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB * 3 + Keys.DOWN * 3)
        actions.perform()
        sleep(2)
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB * 4 + Keys.ENTER)
        actions.perform()
        sleep(5)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        driver.quit()
