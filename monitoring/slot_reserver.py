import json
import random
from datetime import datetime, timedelta
from time import sleep

from loguru import logger
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from captcha.captcha_resolver import CaptchaResolver
from config.configuration import DELAYS_BETWEEN_DAY_MONITORING_SECONDS, MONITORING_DATE_RANGE_DAYS, \
    MONITORING_DATE_RANGE_START_FROM_DELTA
from model.models import Slot, SlotReservation
from notification.notifier import Notifier


class SlotReserver:
    def __init__(self, driver: Chrome, notifier: Notifier, captcha_resolver: CaptchaResolver, office_id: int):
        self.notifier = notifier
        self.captcha_resolver = captcha_resolver
        self.driver = driver
        self.office_id = office_id
        self.driver_wait = WebDriverWait(driver=self.driver, timeout=15)

    def get_free_slots(self) -> list[Slot]:
        start_from = datetime.today() + timedelta(days=MONITORING_DATE_RANGE_START_FROM_DELTA)
        date_range = [(start_from + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(MONITORING_DATE_RANGE_DAYS)]
        logger.info(f"Trying to get free slots with date range from {date_range[0]} to {date_range[-1]}")

        for date in date_range:
            get_slots_script = f"""
                var xhr = new XMLHttpRequest();
                xhr.open('POST', 'https://eq.hsc.gov.ua/site/freetimes', false);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
                xhr.setRequestHeader('Accept-Language', 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7');
                xhr.setRequestHeader('X-Csrf-Token', document.getElementsByName('csrf-token')[0].getAttribute('content'));
                xhr.setRequestHeader('Accept', '*/*');
                xhr.setRequestHeader('Cache-Control', 'no-cache');
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.send('office_id={self.office_id}&date_of_admission={date}&question_id=55&es_date=&es_time=');
                return xhr.responseText;
            """

            response = self.driver.execute_script(get_slots_script)
            response_json = json.loads(response)

            free_slots = response_json['rows']

            logger.info(f"Available slots on date {date}: {free_slots}")

            if free_slots:
                self.notifier.notify_free_slots_found()
                logger.success(f"Found free slots on date {date}! Processing...")
                return [Slot(slot_id=item['id'], date=date, ch_time=item['chtime']) for item in response_json['rows']]

            sleep_time = random.uniform(*DELAYS_BETWEEN_DAY_MONITORING_SECONDS)
            logger.info(f"Sleep for {sleep_time:.1f} seconds after requesting free slots for {date} date...")
            sleep(sleep_time)

        return []

    def create_slot_reservation(self, slots: list[Slot]) -> SlotReservation:
        logger.info("Reserving first available slot...")

        for slot in slots:
            reserve_slots_script = f"""
                var xhr = new XMLHttpRequest();
                xhr.open('POST', 'https://eq.hsc.gov.ua/site/reservecherga', false);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
                xhr.setRequestHeader('Accept-Language', 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7');
                xhr.setRequestHeader('X-Csrf-Token', document.getElementsByName('csrf-token')[0].getAttribute('content'));
                xhr.setRequestHeader('Accept', '*/*');
                xhr.setRequestHeader('Cache-Control', 'no-cache');
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.send('id_chtime={slot.id}&question_id=55&email=m4ksymdoroshenko@gmail.com');
                
                var responseContent = xhr.responseText;
                var redirectUrl = xhr.getResponseHeader('X-Redirect');
                
                return JSON.stringify({{
                    "content": responseContent,
                    "redirect-to": redirectUrl
                }});
            """

            response = self.driver.execute_script(reserve_slots_script)
            response_json = json.loads(response)

            if response_json['content'] == 'error01':
                logger.info(f"Cannot reserve slot {slot.ch_date} {slot.ch_time}. Seems it's already taken. Continuing...")
                continue

            self.notifier.notify_reservation_start(slot)
            logger.success(f"Reserved slot on {slot.ch_date} {slot.ch_time}!")

            return SlotReservation(
                reservation_url=response_json['redirect-to'],
                slot=slot,
            )

    def approve_reservation(self, reservation: SlotReservation):
        logger.success(f"Approving reservation {reservation.slot.ch_date} {reservation.slot.ch_time}...")

        self.driver.refresh()

        if self.captcha_resolver.has_captcha():
            self.captcha_resolver.resolve_captcha()

        self.driver.execute_script(f"window.location.href = '{reservation.reservation_url}';")

        self.driver_wait.until(EC.element_to_be_clickable(
            self.driver.find_element(by=By.XPATH, value="//a[@href='/site/finish']"))
        ).click()

        self.notifier.notify_slot_reserved(reservation.slot)
        logger.success(f"Reservation {reservation.slot.ch_date} {reservation.slot.ch_time} approved!")
