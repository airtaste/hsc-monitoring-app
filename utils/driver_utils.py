import asyncio
from pathlib import Path
from time import sleep, time

from selenium.webdriver import Keys, ActionChains
from selenium.webdriver import Chrome
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.configuration import SCREENSHOTS_FOLDER, HSC_OFFICE_LOCATION, BROWSER_DOWNLOADS_FOLDER, HEADLESS_MODE


def setup_chrome_driver() -> Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    options.add_argument("--start-maximized")
    options.add_argument("--password-store=basic")
    if HEADLESS_MODE:
        options.add_argument('--headless')
    options.add_argument("--disable-blink-features=AutomationControlled")
    prefs = {
        'download.default_directory': str(Path(BROWSER_DOWNLOADS_FOLDER).absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    options.add_experimental_option('prefs', prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    chrome_service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=options)

    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", HSC_OFFICE_LOCATION)
    driver.execute_cdp_cmd("Browser.grantPermissions", {"origin": "https://eq.hsc.gov.ua/", "permissions": ["geolocation"]})

    return driver


async def take_screenshot(driver: Chrome) -> bool:
    ts = int(time()) * 1000
    screenshot_file_path = Path(f"{SCREENSHOTS_FOLDER}/screenshot_{ts}.png").absolute()
    return driver.save_screenshot(screenshot_file_path)


async def cleanup_browser_cache(driver: Chrome):
    # Cleanup browser cache
    driver.execute_script("window.open('');")
    await asyncio.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    await asyncio.sleep(2)
    driver.get('chrome://settings/clearBrowserData')
    await asyncio.sleep(2)
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB * 3 + Keys.DOWN * 3)
    actions.perform()
    await asyncio.sleep(2)
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB * 4 + Keys.ENTER)
    actions.perform()
    await asyncio.sleep(5)
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
