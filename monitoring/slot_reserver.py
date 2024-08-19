import asyncio
import json
import os
import random
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Optional

from loguru import logger
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from captcha.captcha_resolver import CaptchaResolver
from config.configuration import DELAYS_BETWEEN_DAY_MONITORING_SECONDS, BROWSER_DOWNLOADS_FOLDER, USER_EMAIL
from exceptions.exceptions import ReservationException, ReservationApprovalException
from model.models import Slot, SlotReservation
from notification.notifier import Notifier
from utils.driver_utils import take_screenshot


class SlotReserver:
    def __init__(self, driver: Chrome, notifier: Notifier, captcha_resolver: CaptchaResolver, office_id: int):
        self.notifier = notifier
        self.captcha_resolver = captcha_resolver
        self.driver = driver
        self.office_id = office_id
        self.available_dates_map = {}
        self.driver_wait = WebDriverWait(driver=self.driver, timeout=30)

    async def _propagate_available_dates(self):
        self.driver.refresh()

        if await self.captcha_resolver.has_captcha():
            await self.captcha_resolver.resolve_captcha_code()

        go_to_dates_url_script = """
            location.href = 'https://eq.hsc.gov.ua/site/step1?value=55'
        """

        self.driver.execute_script(go_to_dates_url_script)
        self.driver_wait.until(EC.url_to_be('https://eq.hsc.gov.ua/site/step1?value=55'))

        get_available_dates_script = """
            const dates = [];
            const links = document.querySelectorAll('a[data-params]');
            
            links.forEach(link => {
                const dataParamsStr = link.getAttribute('data-params');
                let dataParamsObj;
                try {
                    dataParamsObj = JSON.parse(dataParamsStr.replace(/&quot;/g, '"'));
                } catch (e) {
                    console.error('Error parsing JSON:', e);
                    return;
                }
                const date = dataParamsObj.chdate;
                if (date) {
                    dates.push(date);
                }
            });
            
            return JSON.stringify(dates);
        """

        response = self.driver.execute_script(get_available_dates_script)
        self.available_dates_map[datetime.today().strftime('%Y-%m-%d')] = json.loads(response)

        go_to_base_url_back_script = """
            location.href = 'https://eq.hsc.gov.ua/site/step0'
        """

        self.driver.execute_script(go_to_base_url_back_script)
        self.driver_wait.until(EC.url_to_be('https://eq.hsc.gov.ua/site/step0'))

    async def get_free_slots(self) -> list[Slot]:
        today = datetime.today().strftime('%Y-%m-%d')

        if today in self.available_dates_map:
            date_range = self.available_dates_map[today]
        else:
            await self._propagate_available_dates()
            date_range = self.available_dates_map[today]

        logger.info(f"Trying to get free slots with date range from {date_range[0]} to {date_range[-1]}")
        for date in date_range:
            try:
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
                    logger.success(f"Found free slots on date {date}! Processing...")
                    return [Slot(slot_id=item['id'], date=date, ch_time=item['chtime']) for item in
                            response_json['rows']]

                sleep_time = random.uniform(*DELAYS_BETWEEN_DAY_MONITORING_SECONDS)
                logger.info(f"Sleep for {sleep_time:.1f} seconds after requesting free slots for {date} date...")
                await asyncio.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Failed to fetch free slots on date {date}. Unexpected error '{str(e)}'. Continuing...")
                continue

        return []

    async def reserve_slot(self, slot: Slot) -> SlotReservation:
        sleep_time = random.uniform(*DELAYS_BETWEEN_DAY_MONITORING_SECONDS)
        logger.info(f"Reserving first available slot... Sleep {sleep_time} seconds first...")
        sleep(sleep_time)

        reservation = await self._get_reservation(slot)

        if not reservation:
            raise ReservationException(f"Cannot reserve slot {slot.ch_date} {slot.ch_time}. Seems it's already taken.")
        else:
            logger.success(f"Reserved slot on {slot.ch_date} {slot.ch_time}!")
            await self.notifier.notify_reservation_start(slot)
            return reservation

    async def approve_reservation(self, reservation: SlotReservation):
        try:
            if await self.captcha_resolver.has_captcha():
                await self.captcha_resolver.resolve_captcha_code()

            logger.info(f"Approving reservation {reservation.slot.ch_date} {reservation.slot.ch_time}...")

            self.driver.execute_script(f"window.location.href = '{reservation.reservation_url}';")

            self.driver_wait.until(EC.url_to_be(reservation.reservation_url))

            self.driver.implicitly_wait(60)
            self.driver_wait.until(EC.visibility_of(
                self.driver.find_element(by=By.CLASS_NAME, value="btn-hsc-green"))
            ).click()
            await self.notifier.notify_reservation_approved(slot=reservation.slot)
            await self._download_file(slot=reservation.slot)
            self.driver.implicitly_wait(0)

            logger.success(f"Reservation {reservation.slot.ch_date} {reservation.slot.ch_time} approved!")
        except Exception as e:
            logger.error(f"Error during reservation approval: {str(e)}")
            await take_screenshot(self.driver)
            raise ReservationApprovalException(e)

    async def _get_reservation(self, slot: Slot) -> Optional[SlotReservation]:
        reserve_slots_script = f"""
            var xhr = new XMLHttpRequest();
            xhr.open('POST', 'https://eq.hsc.gov.ua/site/reservecherga', false);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
            xhr.setRequestHeader('Accept-Language', 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7');
            xhr.setRequestHeader('X-Csrf-Token', document.getElementsByName('csrf-token')[0].getAttribute('content'));
            xhr.setRequestHeader('Accept', '*/*');
            xhr.setRequestHeader('Cache-Control', 'no-cache');
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.send('id_chtime={slot.id}&question_id=55&email={USER_EMAIL}');

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
            logger.warning(f"Cannot reserve slot {slot.ch_date} {slot.ch_time}. Seems it's already taken.")
            return None
        else:
            return SlotReservation(reserved_at=datetime.now(), reservation_url=response_json['redirect-to'], slot=slot)

    async def _download_file(self, slot: Slot):
        slot_date = datetime.strptime(slot.ch_date, "%Y-%m-%d").strftime("%d.%m.%y")
        file_path = Path(f"{BROWSER_DOWNLOADS_FOLDER}/Талон.pdf").absolute()
        search_text = f"ДАТА {slot_date}"

        try:
            self.driver_wait.until(
                EC.presence_of_element_located((By.XPATH, f"//div[.//strong[contains(text(), '{search_text}')]]"))
            ).find_element(By.XPATH, ".//a[contains(@href, '/site/mpdf')]").click()

            with open(file_path, 'rb') as file:
                file_name = f"Талон_{slot.ch_date.replace('-', '_')}.pdf"
                await self.notifier.notify_with_pdf(file, file_name)
        except Exception as e:
            logger.error(f"Error during file downloading: {str(e)}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
