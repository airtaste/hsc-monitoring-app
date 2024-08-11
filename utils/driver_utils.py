from pathlib import Path
from time import sleep, time

from selenium.webdriver import Keys, ActionChains
from selenium.webdriver import Chrome

from config.configuration import SCREENSHOTS_FOLDER


def take_screenshot(driver: Chrome) -> bool:
    ts = int(time()) * 1000
    screenshot_file_path = Path(f"{SCREENSHOTS_FOLDER}/screenshot_{ts}.png").absolute()
    return driver.save_screenshot(screenshot_file_path)


def cleanup_browser_cache(driver: Chrome):
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
