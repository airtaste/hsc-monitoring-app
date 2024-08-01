from time import sleep

from selenium.webdriver import Keys, ActionChains


def cleanup_browser_cache(driver):
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
