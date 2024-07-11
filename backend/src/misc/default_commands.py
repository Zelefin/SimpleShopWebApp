from aiogram import Bot, types
from aiogram.types import BotCommand


async def set_default_commands(bot: Bot):
    commands_members = {
        "start": "Розпочати роботу з ботом",
    }

    commands_admins = {
        "admin": "Адмін меню",
        **commands_members,
    }

    await bot.set_my_commands(
        [
            BotCommand(command=name, description=value)
            for name, value in commands_members.items()
        ],
        scope=types.BotCommandScopeAllGroupChats(),
    )
    await bot.set_my_commands(
        [
            BotCommand(command=name, description=value)
            for name, value in commands_admins.items()
        ],
        scope=types.BotCommandScopeAllChatAdministrators(),
    )
