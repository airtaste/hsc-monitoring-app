import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from captcha_resolver import CaptchaResolver

options = webdriver.ChromeOptions()
options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=options)
driver.get('https://www.google.com/recaptcha/api2/demo')
captcha_resolver = CaptchaResolver(driver=driver)

if __name__ == '__main__':
    try:
        if captcha_resolver.has_captcha():
            captcha_resolver.resolve_captcha()

        time.sleep(10)
    finally:
        driver.quit()
