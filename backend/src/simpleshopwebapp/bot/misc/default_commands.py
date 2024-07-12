from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault


async def set_default_commands(bot: Bot, admins_ids: list[int]) -> None:
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
        scope=BotCommandScopeDefault(),
    )

    for admin_id in admins_ids:
        await bot.set_my_commands(
            [
                BotCommand(command=name, description=value)
                for name, value in commands_admins.items()
            ],
            scope=BotCommandScopeChat(chat_id=admin_id),
        )
