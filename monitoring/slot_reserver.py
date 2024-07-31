import json
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver import Chrome

from model.models import Slot
from notification.notifier import Notifier
from loguru import logger


class SlotReserver:
    def __init__(
            self,
            driver: Chrome,
            notifier: Notifier,
            monitoring_date: datetime,
            office_id: int
    ):
        self.date = monitoring_date.strftime('%Y-%m-%d')
        self.notifier = notifier
        self.driver = driver
        self.driver_wait = WebDriverWait(driver=self.driver, timeout=15)
        self.get_slots_script = f"""
            var xhr = new XMLHttpRequest();
            xhr.open('POST', 'https://eq.hsc.gov.ua/site/freetimes', false);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
            xhr.setRequestHeader('Accept-Language', 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7');
            xhr.setRequestHeader('X-Csrf-Token', document.getElementsByName('csrf-token')[0].getAttribute('content'));
            xhr.setRequestHeader('Accept', '*/*');
            xhr.setRequestHeader('Cache-Control', 'no-cache');
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.send('office_id={office_id}&date_of_admission={self.date}&question_id=55&es_date=&es_time=');
            return xhr.responseText;
        """

    def get_free_slots(self) -> list[Slot]:
        response = self.driver.execute_script(self.get_slots_script)
        response_json = json.loads(response)

        logger.info(f"Get slots response JSON: {response_json}")

        return [
            Slot(
                slot_id=item['id'],
                date=self.date,
                ch_time=item['chtime']
            ) for item in response_json['rows']
        ]

    def reserve_slot_and_notify(self, slot: Slot):
        self.notifier.notify_reservation_start(slot)

        self.driver_wait.until(
            EC.visibility_of(self.driver.find_element(by=By.XPATH, value="//button[text()='Записатись']"))).click()
        self.driver_wait.until(
            EC.visibility_of(self.driver.find_element(by=By.XPATH, value="//a[text()='Практичний іспит']"))).click()
        self.driver_wait.until(EC.visibility_of(
            self.driver.find_element(by=By.XPATH, value="//button[@data-target='#ModalCenterServiceCenter']"))).click()
        self.driver_wait.until(EC.visibility_of(
            self.driver.find_element(by=By.XPATH, value="//button[@data-target='#ModalCenterServiceCenter1']"))).click()
        self.driver_wait.until(
            EC.visibility_of(self.driver.find_element(by=By.XPATH, value="//a[text()='Так']"))).click()
        self.driver_wait.until(EC.visibility_of(self.driver.find_element(by=By.XPATH,
                                                                         value="//a[text()='Практичний іспит на категорію В (з механічною коробкою передач)']"))).click()
        self.driver_wait.until(EC.visibility_of(self.driver.find_element(by=By.XPATH,
                                                                         value=f"//a[contains(@data-params, '\"chdate\":\"{self.date}\"')]"))).click()
        self.driver_wait.until(EC.element_to_be_clickable(
            self.driver.find_element(by=By.XPATH, value="//a[@title='Моє місцезнаходження']"))).click()
        displayed_icon = next(
            icon for icon in self.driver.find_elements(by=By.XPATH, value="//img[@src='/images/hsc_s.png']") if
            icon.is_displayed())
        displayed_icon.click()
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.XPATH, value="input[@value='Далі']"))).click()
        self.driver_wait.until(
            EC.element_to_be_clickable(self.driver.find_element(by=By.XPATH, value="a[text()='Підтвердити запис']"))).click()

        self.notifier.notify_slot_reserved(slot)
