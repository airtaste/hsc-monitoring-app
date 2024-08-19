from loguru import logger
from selenium.common import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium_recaptcha_solver import RecaptchaSolver, RecaptchaException
from twocaptcha import TwoCaptcha

from config.configuration import CAPTCHA_SOLVE_RETRY_THRESHOLD, TWOCAPTCHA_API_KEY, HSC_SITE_KEY
from exceptions.exceptions import CaptchaSolverException


class CaptchaResolver:
    def __init__(self, driver: Chrome):
        self.driver = driver
        self.driver_wait = WebDriverWait(driver=self.driver, timeout=30)
        self.recaptcha_solver = RecaptchaSolver(driver=self.driver)
        self.twocaptcha_solver = TwoCaptcha(apiKey=TWOCAPTCHA_API_KEY)

    async def has_captcha(self) -> bool:
        try:
            self.driver.refresh()
            self.driver_wait.until(EC.visibility_of(self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')))
            logger.info("reCAPTCHA iframe found! Resolving captcha...")
            return True
        except NoSuchElementException:
            logger.info("No captcha found. Processing action as usual...")
            return False

    async def resolve_captcha_audio(self):
        solved = False

        for i in range(CAPTCHA_SOLVE_RETRY_THRESHOLD):
            self.driver_wait.until(
                EC.visibility_of(self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]'))
            )
            recaptcha_control_frame = self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

            try:
                self.recaptcha_solver.click_recaptcha_v2(recaptcha_control_frame)
                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                solved = True
                break
            except RecaptchaException as e:
                if str(e) == 'Speech recognition API could not understand audio, try again':
                    logger.warning(f"[Attempt #{i + 1}] Failed to resolve captcha... Trying again...")
                    self.driver.refresh()
                    continue
                else:
                    logger.error(f"Error during captcha resolve: {str(e)}")
                    raise e

        if not solved:
            raise CaptchaSolverException("Captcha was not solved. Check logs for more details.")

        self.driver_wait.until(EC.url_to_be('https://eq.hsc.gov.ua/step0'))
        logger.success('Captcha resolved successfully!')

    async def resolve_captcha_code(self):
        solved = False

        for i in range(CAPTCHA_SOLVE_RETRY_THRESHOLD):
            try:
                response = self.twocaptcha_solver.recaptcha(sitekey=HSC_SITE_KEY, url=self.driver.current_url)
                code = response['code']

                recaptcha_response_element = self.driver.find_element(By.ID, 'g-recaptcha-response')
                self.driver.execute_script(f'arguments[0].value = "{code}";', recaptcha_response_element)

                recaptcha_hidden_input_element = self.driver.find_element(By.ID, 'captcha-recaptcha')
                self.driver.execute_script(f'arguments[0].value = "{code}";', recaptcha_hidden_input_element)

                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                solved = True
                break
            except Exception as e:
                logger.error(f"Error during captcha resolve: {str(e)}. Trying again...")
                continue

        if not solved:
            raise CaptchaSolverException("Captcha was not solved. Check logs for more details.")

        self.driver_wait.until(EC.url_to_be('https://eq.hsc.gov.ua/step0'))
        logger.success('Captcha resolved successfully!')
