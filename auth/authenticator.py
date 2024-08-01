from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from loguru import logger

from config.configuration import AUTH_TIMER_THRESHOLD_SECONDS
from notification.notifier import Notifier


class Authenticator:

    def __init__(self, driver: Chrome, notifier: Notifier):
        self.driver = driver
        self.driver_wait = WebDriverWait(driver=self.driver, timeout=15)
        self.notifier = notifier

    def try_authenticate(self):
        authenticated = False

        while True:
            if authenticated:
                break

            try:
                self.__authenticate_and_notify()
                authenticated = True
            except (NoSuchElementException, TimeoutException):
                continue

    def __authenticate_and_notify(self):
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
