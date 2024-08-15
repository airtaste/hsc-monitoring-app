import json
import requests

from model.models import Slot


class Notifier:
    def __init__(self, token_id: str, chat_id: str):
        self.token_id = token_id
        self.chat_id = chat_id

    def notify_wait_auth(self, authorization_link: str):
        msg = f"""
            <b>Важливо:</b> Вам необхідно авторизуватись у найближчий час (5-10 хвилин)! Будь-ласка, натисніть кнопку нижче, щоб завершити процес авторизації
        """
        payload = {
            'chat_id': self.chat_id,
            'text': msg,
            'parse_mode': 'html',
            'reply_markup': json.dumps({
                'inline_keyboard': [
                    [
                        {
                            'text': 'Авторизуватись',
                            'url': authorization_link
                        }
                    ]
                ]
            })
        }

        requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=self.token_id), data=payload)

    def notify_auth_success(self):
        msg = f"""
            <b>Оновлення:</b> Вас було успішно авторизовано до сайту електронної черги МВС України!
        """
        payload = {
            'chat_id': self.chat_id,
            'text': msg,
            'parse_mode': 'html'
        }

        requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=self.token_id), data=payload)

    def notify_reservation_start(self, slot: Slot):
        msg = f"""
            <b>Оновлення:</b> Знайдено талон на дату <b>{slot.ch_date} {slot.ch_time}</b>. Намагаюсь забронювати час та підтвердити взяття талону... Як тільки мені це вдасться - я обов'язково вас повідомлю про це!
        """
        payload = {
            'chat_id': self.chat_id,
            'text': msg,
            'parse_mode': 'html'
        }

        requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=self.token_id), data=payload)

    def notify_slot_reserved(self, slot: Slot, slot_pdf):
        msg = f"""
            <b>Оновлення:</b> Талон на здачу практичного іспиту (механічна коробка передачі) на машині сервісного центру МВС успішно взято на дату <b>{slot.ch_date} {slot.ch_time}</b>. Щасти на іспиті!
        """
        payload = {
            'chat_id': self.chat_id,
            'caption': msg,
            'parse_mode': 'html'
        }

        requests.post("https://api.telegram.org/bot{token}/sendDocument"
                      .format(token=self.token_id), data=payload, files={'document': slot_pdf})
