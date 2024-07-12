from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from simpleshopwebapp.bot.filters.admin import AdminFilter

admin_router = Router()


@admin_router.message(CommandStart(), AdminFilter())
async def user_start(message: Message):
    await message.reply("Вітаю, адміне!")
