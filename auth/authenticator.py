from pathlib import Path

from loguru import logger
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from config.configuration import AUTH_TIMER_THRESHOLD_SECONDS, AUTHENTICATOR_MODE, EUID_KEY_PASSWORD, EUID_KEY_PATH
from notification.notifier import Notifier


class Authenticator:

    def __init__(self, driver: Chrome, notifier: Notifier):
        self.driver = driver
        self.driver_wait = WebDriverWait(driver=self.driver, timeout=30)
        self.notifier = notifier

    def try_authenticate(self):
        self.driver.get("https://eq.hsc.gov.ua/")
        if AUTHENTICATOR_MODE == 'BANK_ID':
            self.bank_id_authenticate()
        else:
            self.euid_authenticate()

    def bank_id_authenticate(self):
        # Authorize via bank id
        self.driver_wait.until(
            EC.element_to_be_clickable(
                self.driver.find_element(by=By.CSS_SELECTOR, value="input[type=checkbox]"))).click()
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.CLASS_NAME, value="btn-hsc-green_s"))).click()
        self.driver_wait.until(EC.element_to_be_clickable(
            self.driver.find_element(by=By.CSS_SELECTOR, value="a[href='/bankid-nbu-auth']"))).click()
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.ID, value="selBankConnect-button"))).click()
        self.driver_wait.until(EC.element_to_be_clickable(self.driver.find_element(by=By.ID, value="ui-id-4"))).click()
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.ID, value="btnBankIDChoose"))).click()
        authentication_link = self.driver_wait.until(
            EC.visibility_of(self.driver.find_element(by=By.ID, value="qrcode"))).get_attribute("title")
        # Send authorization link via telegram bot
        self.notifier.notify_wait_auth(authentication_link)
        logger.info("Sent authentication link via telegram bot! Waiting for approval...")
        # Wait until button would be ready
        self.driver.implicitly_wait(AUTH_TIMER_THRESHOLD_SECONDS)
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.ID, value="btnAcceptUserDataAgreement"))
        ).click()
        self.driver.implicitly_wait(0)
        logger.success("Authorized to https://eq.hsc.gov.ua/ successfully!")
        self.notifier.notify_auth_success()

    def euid_authenticate(self):
        # Authorize via euid key
        self.driver_wait.until(
            EC.element_to_be_clickable(
                self.driver.find_element(by=By.CSS_SELECTOR, value="input[type=checkbox]")
            )
        ).click()
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.CLASS_NAME, value="btn-hsc-green_s"))).click()

        self.driver_wait.until(EC.element_to_be_clickable(
            self.driver.find_element(by=By.CSS_SELECTOR, value="a[href='/euid-auth-js']"))).click()

        # Upload key file
        key_file_path = Path(EUID_KEY_PATH).absolute().__str__()
        # Somehow this action trick id-gov system, and it thinks that something was uploaded in natural way
        self.driver_wait.until(
            EC.visibility_of(
                self.driver.find_element(by=By.XPATH, value="//span[text()='оберіть його на своєму носієві']")
            )
        ).click()
        key_input = self.driver.find_element(by=By.ID, value="PKeyFileInput")
        key_input.send_keys(key_file_path)

        # Input password for key
        pwd_input = self.driver.find_element(by=By.ID, value="PKeyPassword")
        pwd_input.send_keys(EUID_KEY_PASSWORD)

        self.driver_wait.until(
            EC.element_to_be_clickable(
                self.driver.find_element(by=By.ID, value="id-app-login-sign-form-file-key-sign-button")
            )
        ).click()

        # Wait until button would be ready
        self.driver.implicitly_wait(AUTH_TIMER_THRESHOLD_SECONDS)
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.ID, value="btnAcceptUserDataAgreement"))
        ).click()
        self.driver.implicitly_wait(0)

        logger.success("Authorized to https://eq.hsc.gov.ua/ successfully!")
        self.notifier.notify_auth_success()
