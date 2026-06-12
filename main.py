
import asyncio
import logging
from bot import web_app
from config import TOKEN, API_ID, API_HASH, DB_URI, DB_CHANNEL

logger = logging.getLogger(__name__)


async def start_bot():
    from bot import Bot
    from pyrogram import compose
    from config import (
        SESSION, WORKERS, FSUBS, ADMINS, MESSAGES,
        AUTO_DEL, DB_NAME, PROTECT, DISABLE_BTN
    )
    app = Bot(
        SESSION, WORKERS, DB_CHANNEL, FSUBS, TOKEN,
        ADMINS, MESSAGES, AUTO_DEL, DB_URI, DB_NAME,
        API_ID, API_HASH, PROTECT, DISABLE_BTN
    )
    await compose([app])


async def runner():
    missing = []
    if not TOKEN:
        missing.append("BOT_TOKEN")
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not DB_URI:
        missing.append("DB_URI")
    if not DB_CHANNEL:
        missing.append("DB_CHANNEL")

    if missing:
        logger.warning(
            f"Bot credentials not configured. Missing: {', '.join(missing)}. "
            "Set them as environment variables/secrets to start the bot. "
            "Starting web server only..."
        )
        await web_app()
        # Keep running indefinitely
        await asyncio.Event().wait()
    else:
        await asyncio.gather(
            start_bot(),
            web_app()
        )


asyncio.run(runner())
