# run.py
import asyncio
import logging
from bot_instance import dp, bot
from handlers import router as handlers_router
from callbacks import router as callbacks_router
from commands import set_bot_commands
from database import init_db

async def main() -> None:
    init_db()

    dp.include_router(handlers_router)
    dp.include_router(callbacks_router)

    await set_bot_commands()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Бот запускается...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")