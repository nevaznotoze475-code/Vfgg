# commands.py

from aiogram.types import BotCommand, BotCommandScopeDefault
from bot_instance import bot

async def set_bot_commands():
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="admin", description="⚙️ Админ-панель (только для админов)")
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())