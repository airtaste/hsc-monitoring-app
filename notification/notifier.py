from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

from model.models import Slot


class Notifier:
    def __init__(self, bot: Bot, chat_id: int):
        self.chat_id = chat_id
        self.tg_bot = bot

    async def notify_wait_auth(self, authorization_link: str):
        msg = f"""
            <b>Важливо:</b> Вам необхідно авторизуватись у найближчий час (5-10 хвилин)! Будь-ласка, натисніть кнопку нижче, щоб завершити процес авторизації
        """

        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode='html',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Авторизуватись', url=authorization_link)]]
            )
        )

    async def notify_auth_success(self):
        msg = f"""
            <b>Оновлення:</b> Вас було успішно авторизовано до сайту електронної черги МВС України!
        """
        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode='html'
        )

    async def notify_reservation_start(self, slot: Slot):
        msg = f"""
            <b>Оновлення:</b> Знайдено талон на дату <b>{slot.ch_date} {slot.ch_time}</b>. Запустив процес бронювання часу...
        """
        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode='html'
        )

    async def notify_reservation_approved(self, slot: Slot):
        msg = f"""
            <b>Оновлення:</b> Талон на здачу практичного іспиту (механічна коробка передачі) на машині сервісного центру МВС успішно взято на дату <b>{slot.ch_date} {slot.ch_time}</b>. Щасти на іспиті!
        """

        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode='html',
        )

    async def notify_with_pdf(self, slot_pdf):

        await self.tg_bot.send_document(
            chat_id=self.chat_id,
            caption="Для зручності вислав талон файлом!",
            document=slot_pdf
        )
