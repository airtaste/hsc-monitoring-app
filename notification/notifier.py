import json
import requests

from model.models import Slot


class Notifier:
    def __init__(self, token_id: str, chat_id: str):
        self.token_id = token_id
        self.chat_id = chat_id

    def notify_wait_auth(self, authorization_link: str):
        msg = f"""
            <b>Important:</b> You need to authenticate ASAP within the next 5 minutes! Please click the link below to complete the authentication process:
        """
        payload = {
            'chat_id': self.chat_id,
            'text': msg,
            'parse_mode': 'html',
            'reply_markup': json.dumps({
                'inline_keyboard': [
                    [
                        {
                            'text': 'Authenticate Now',
                            'url': authorization_link
                        }
                    ]
                ]
            })
        }

        requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=self.token_id), data=payload)


    def notify_auth_success(self):
        msg = f"""
            <b>Update:</b> Authorized to https://eq.hsc.gov.ua/ successfully!
        """
        payload = {
            'chat_id': self.chat_id,
            'text': msg,
            'parse_mode': 'html'
        }

        requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=self.token_id), data=payload)

    def notify_reservation_start(self, slot: Slot):
        msg = f"""
            <b>Update:</b> A slot reservation started <b>{slot.ch_date} {slot.ch_time}</b>.
            Once slot would be reserved you would retrieve notification about reservation!
        """
        payload = {
            'chat_id': self.chat_id,
            'text': msg,
            'parse_mode': 'html'
        }

        requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=self.token_id), data=payload)

    def notify_slot_reserved(self, slot: Slot):
        msg = f"""
            <b>Update:</b> A slot has been reserved for you on <b>{slot.ch_date} {slot.ch_time}</b>.
            Please confirm your reservation within the next 1 minute to secure it. Time is running out, so please act quickly!
        """
        payload = {
            'chat_id': self.chat_id,
            'text': msg,
            'parse_mode': 'html'
        }

        requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=self.token_id), data=payload)
