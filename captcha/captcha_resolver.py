from loguru import logger
from selenium.common import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium_recaptcha_solver import RecaptchaSolver

from config.configuration import CAPTCHA_SOLVE_RETRY_THRESHOLD


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
            solved = False

            for i in range(CAPTCHA_SOLVE_RETRY_THRESHOLD):
                self.driver_wait.until(
                    EC.visibility_of(self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]'))
                )
                recaptcha_control_frame = self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

                try:
                    self.solver.click_recaptcha_v2(recaptcha_control_frame)
                    self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                    solved = True
                    break
                except:
                    logger.warning(f"[Attempt #{i + 1}] Failed to resolve captcha... Trying again...")
                    self.driver.refresh()
                    continue

            if not solved:
                raise Exception(
                    "Captcha was not solved. It may lead to unexpected errors. Processing without acknowledgment..."
                )

            self.driver_wait.until(EC.url_to_be('https://eq.hsc.gov.ua/step0'))
            logger.success('Captcha resolved successfully!')
        except Exception as e:
            logger.error(e)
