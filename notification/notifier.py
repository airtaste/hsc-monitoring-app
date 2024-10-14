from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode

from model.models import Slot


class Notifier:
    def __init__(self, bot: Bot, chat_id: int):
        self.chat_id = chat_id
        self.tg_bot = bot

    async def notify_wait_auth(self, authorization_link: str):
        msg = f"""
            *Важливо:* ⚠ Вам необхідно авторизуватись у найближчий час (5-10 хвилин)! Будь-ласка, натисніть кнопку нижче, щоб завершити процес авторизації
        """

        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Авторизуватись', url=authorization_link)]]
            )
        )

    async def notify_auth_success(self):
        msg = f"""
            *Оновлення:* ✅ Вас було успішно авторизовано до сайту електронної черги МВС України!
        """
        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN
        )

    async def notify_reservation_start(self, slot: Slot):
        msg = f"""
            *Оновлення:* 📅 Знайдено талон на дату *{slot.ch_date} {slot.ch_time}*. Запустив процес резервування часу...
        """
        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN
        )

    async def notify_reservation_failed(self):
        msg = f"""
            *Оновлення:* 🚨 Нажаль виникла помилка під час резервування часу. Схоже, що талон вже був заброньований...
        """
        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN
        )

    async def notify_reservation_approved(self, slot: Slot):
        msg = f"""
            *Оновлення:* 📅 Талон на здачу практичного іспиту (механічна коробка передачі) на машині сервісного центру МВС успішно зарезервовано на дату *{slot.ch_date} {slot.ch_time}*. Щасти на іспиті!
        """

        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def notify_with_pdf(self, file, filename):
        await self.tg_bot.send_document(
            chat_id=self.chat_id,
            caption="🎉 🎉 🎉 Вітаю! Для зручності вислав талон PDF файлом! Тепер ви можете зупинити роботу бота...",
            document=file,
            filename=filename
        )

    async def notify_error(self, error: Exception):
        msg = f"""
            *Оновлення:* 🚨 Виникла помилка під час роботи бота! Детальніше про помилку: `{str(error)}`
        """

        await self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN
        )
