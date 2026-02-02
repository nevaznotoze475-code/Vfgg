from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from settings import settings

bot = Bot(
    token=settings.bot.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

worker_bot = Bot(token=settings.bot.worker_bot_token)

dp = Dispatcher()