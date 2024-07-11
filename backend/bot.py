import asyncio

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
    ip_filter_middleware,
)
from aiogram.webhook.security import IPFilter
from aiohttp import web
import logging

import betterlogging as bl
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage

from backend.infrastructure.database.setup import create_engine, create_session_pool
from backend.config_reader import Config, load_config
from backend.src.handlers import routers_list

from backend.src.middlewares.database import DatabaseMiddleware
from backend.src.misc.default_commands import set_default_commands
from backend.src.services import broadcaster


async def on_startup(bot: Bot, config: Config, dp: Dispatcher) -> None:
    if config.bot.use_webhook:
        await set_webhook(bot, dp, config)
    await broadcaster.broadcast(bot, [config.admin.id], "Bot started")
    await set_default_commands(bot)


async def start_dispatcher(bot: Bot, dp: Dispatcher) -> None:
    await dp.start_polling(bot)


async def set_webhook(bot: Bot, dp: Dispatcher, config: Config) -> None:
    me = await bot.get_me()
    url = f"{config.web.domain}{config.bot.webhook_path}"
    logging.info(
        f"Run webhook for bot https://t.me/{me.username} "
        f'id={bot.id} - "{me.full_name}" on {url}'
    )
    await bot.set_webhook(
        url=url,
        drop_pending_updates=True,
        allowed_updates=dp.resolve_used_update_types(),
        secret_token=config.bot.webhook_secret,
    )


def register_global_middlewares(
    dp: Dispatcher,
    session_pool,
):
    """
    Register global middlewares for the given dispatcher.
    Global middlewares here are the ones that are applied to all the handlers (you specify the type of update)

    :param dp: The dispatcher instance.
    :type dp: Dispatcher
    :param session_pool: Optional session pool object for the database using SQLAlchemy.
    :return: None
    """
    dp.update.outer_middleware(DatabaseMiddleware(session_pool))


def setup_logging():
    """
    Set up logging configuration for the application.

    This method initializes the logging configuration for the application.
    It sets the log level to INFO and configures a basic colorized log for
    output. The log format includes the filename, line number, log level,
    timestamp, logger name, and log message.

    Returns:
        None

    Example usage:
        setup_logging()
    """
    log_level = logging.INFO
    bl.basic_colorized_config(level=log_level)

    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting bot")
    return logger


def main():
    logger = setup_logging()

    config = load_config(".env")
    if config.bot.use_redis:
        storage = RedisStorage.from_url(
            config.redis.make_connection_string(),
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    engine = create_engine(config.postgres.construct_sqlalchemy_url())
    session_pool = create_session_pool(engine)

    bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    dp.include_routers(*routers_list)

    register_global_middlewares(dp, session_pool)

    dp.workflow_data.update(
        config=config,
        dp=dp,
    )

    dp.message.filter(F.chat.id.in_({config.chat.prod, config.chat.debug}))

    dp.startup.register(on_startup)

    if config.bot.use_webhook:
        # Run webhook
        app = web.Application()
        app["bot"] = bot
        app["config"] = config
        app["session_pool"] = session_pool

        webhook_request_handler = SimpleRequestHandler(
            dispatcher=dp, bot=bot, secret_token=config.bot.webhook_secret
        )

        webhook_request_handler.register(app, path=config.bot.webhook_path)
        setup_application(app, dp, bot=bot)

        ip_filter_middleware(ip_filter=IPFilter.default())

        logger.info(f"Running app on {config.web.host}:{config.web.port}")
        web.run_app(app, host=config.web.host, port=config.web.port)
    else:
        asyncio.run(start_dispatcher(bot=bot, dp=dp))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
