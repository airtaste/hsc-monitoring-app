from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import Chrome
from loguru import logger
from selenium_recaptcha_solver import RecaptchaSolver


class CaptchaResolver:
    def __init__(self, driver: Chrome):
        self.driver = driver
        self.driver_wait = WebDriverWait(driver=self.driver, timeout=30)
        self.solver = RecaptchaSolver(driver=self.driver)

    def has_captcha(self) -> bool:
        try:
            self.driver_wait.until(EC.visibility_of(self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')))
            logger.info("reCAPTCHA iframe found! Resolving captcha...")
            return True
        except NoSuchElementException:
            logger.info("No captcha found. Processing action as usual...")
            return False

    def resolve_captcha(self):
        try:
            self.driver_wait.until(EC.visibility_of(self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')))
            recaptcha_control_frame = self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

            for i in range(10):
                try:
                    self.solver.click_recaptcha_v2(recaptcha_control_frame)
                    break
                except:
                    logger.warning("Failed to resolve captcha... Trying again...")
                    pass

            self.driver_wait.until(
                EC.element_to_be_clickable(self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
            ).click()

            logger.success('Captcha resolved successfully!')
        except Exception as e:
            logger.error(e)
