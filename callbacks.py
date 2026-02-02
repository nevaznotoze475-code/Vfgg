# callbacks.py
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto
from keyboards import (
    get_accept_rules_keyboard, get_admin_moderation_keyboard, AdminAction,
    get_worker_menu_keyboard, get_onboarding_keyboard, OnboardingNav,
    get_back_to_menu_keyboard, get_info_keyboard,
    get_admin_panel_keyboard, AdminPanel
)
from handlers import ApplicationForm, escape_md
from bot_instance import bot
from settings import settings
from database import add_worker, get_worker_data, get_setting, set_setting, is_admin
from datetime import datetime

router = Router()

def get_onboarding_content():
    links = settings.links
    # Экранируем символы для ссылок
    manuals_link = links.manuals.replace('-', r'\-')
    cryptobot_link = links.cryptobot.replace('-', r'\-')
    info_channel_link = links.info_channel.replace('-', r'\-')

    return [
        {
            "text": (
                "*👋 Приветствую тебя, мой дорогой друг\\.*\n\n"
                "• Ты попал к нам, но не знаешь, с чего начать\\?\n\n"
                "• Наша задача сделать работу максимально комфортной для тебя и именно поэтому был сделан гайд\\.\n\n"
                "• Обязательно ознакомься со всем, чтобы у тебя не возникало проблем во время ворка\\."
            ),
            "photo_id": links.main_image
        },
        {
            "text": (
                "*📚 Также вы получаете всевозможный материал для упрощения работы:*\n\n"
                f"1\\. Мануалы \\- это весь обучающий контент по всем сферам, он находится [здесь]({manuals_link})\n"
            ),
            "photo_id": links.main_image
        },
        {
            "text": (
                "*💸Быстрые и удобные выплаты\\.*\n\n"
                "• Как происходит выплата\\?\n\n"
                f"1\\. Выплата приходит в @юзернейм бота в течение шести часов после профита, в виде чека для [@CryptoBot]({cryptobot_link})\\.\n"
                f"2\\. Мануал по выводу можно найти [здесь]({manuals_link})\\.\n\n"
                "Сама выплата приходит в криптовалюте USDT по курсу Bestchange на момент выплаты\\!"
            ),
            "photo_id": links.main_image
        },
        {
            "text": (
                "*🐳 Вот ты и закончил вводное обучение\\.*\n\n"
                "Мы рады, что ты вступил в наши ряды и всегда готовы тебе помочь, поэтому ты всегда можешь задавать вопросы в чате или в лс менеджеру\\.\n"
                f"• Также, советуем подписаться на наш [инфо канал]({info_channel_link}), чтобы не пропускать новости и обновления\\.\n\n"
                "*🩵 Удачного, а также комфортного ворка\\.*"
            ),
            "photo_id": links.main_image
        }
    ]

@router.callback_query(AdminPanel.filter(F.action == "toggle_mode"))
async def toggle_withdrawal_mode_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return

    current_mode = get_setting('withdrawal_mode', 'auto')
    new_mode = 'manual' if current_mode == 'auto' else 'auto'
    set_setting('withdrawal_mode', new_mode)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_admin_panel_keyboard(new_mode)
    )
    mode_name = "Ручной" if new_mode == 'manual' else "Автоматический"
    await callback.answer(f"Режим вывода изменен на: {mode_name}")

@router.callback_query(F.data == "apply_request")
async def show_rules_handler(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "> *_Для комфорта каждого в нашем сообществе, просим соблюдать несколько простых правил:_*\n\n"
        "*Запрещено:*\n\n"
        "🚫 Распространять *18\\+ материалы* в любом виде\\.\n"
        "🚫 Проявлять *неуважение* к участникам или администрации\\.\n"
        "🚫 Заниматься *попрошайничеством или спамом*\\.\n"
        "🚫 *Рекламировать* сторонние проекты и услуги\\.\n"
        "🚫 *Принимать платежи* на свои личные реквизиты\\.\n"
        "🚫 *Дезинформировать* о проекте или его команде\\.\n\n"
        "> *\\> _Я ознакомился и принимаю эти условия_*"
    )
    await callback.message.edit_text(text=text, reply_markup=get_accept_rules_keyboard())

@router.callback_query(F.data == "accept_rules")
async def start_application_form(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ApplicationForm.source_info)
    await callback.message.edit_text("Отлично\\! Начнем\\.\n\n*Откуда Вы узнали о нас\\?*")
    await callback.answer()

@router.callback_query(F.data == "edit_application")
async def edit_application_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ApplicationForm.source_info)
    await callback.message.edit_text("Вы решили изменить данные\\. Давайте начнем заново\\.\n\n*Откуда Вы узнали о нас\\?*")
    await callback.answer()

@router.callback_query(F.data == "send_application")
async def send_application_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    user_info = callback.from_user
    raw_username = user_info.username
    username = f"@{escape_md(raw_username)}" if raw_username else "Нет"
    
    source = escape_md(data.get('source', ''))
    experience = escape_md(data.get('experience', ''))
    full_name = escape_md(user_info.full_name)

    text_for_channel = (
        f"*Новая заявка\\!*\n\n"
        f"*От:* {username} \\(ID: `{user_info.id}`\\)\n"
        f"*Имя:* {full_name}\n\n"
        f"*1\\. Откуда узнал:*\n{source}\n\n"
        f"*2\\. Опыт работы:*\n{experience}"
    )
    
    await bot.send_message(
        chat_id=settings.bot.channel_id,
        text=text_for_channel,
        reply_markup=get_admin_moderation_keyboard(user_id=user_info.id)
    )
    
    source_for_user = escape_md(data.get('source', ''))
    experience_for_user = escape_md(data.get('experience', ''))
    new_confirmation_text = (
        "🛸 *Ваша заявка на проверке*\\.\n\n"
        "Бот скажет когда тебя примут\\!\n\n"
        f"1️⃣ *Откуда Вы узнали о нас:* {source_for_user}\n"
        f"2️⃣ *Ваш опыт работы:* {experience_for_user}"
    )
    await callback.message.edit_text(text=new_confirmation_text)
    await callback.answer()

@router.callback_query(AdminAction.filter(F.action == "accept"))
async def admin_accept_handler(callback: types.CallbackQuery, callback_data: AdminAction):
    user_id = callback_data.user_id
    user_info = await bot.get_chat(user_id)

    add_worker(
        user_id=user_id,
        username=user_info.username,
        first_name=user_info.first_name
    )

    original_text_html = callback.message.html_text
    admin_username = callback.from_user.username or 'админ'
    new_text = f"{original_text_html}\n\n<b>✅ Принята администратором @{admin_username}</b>"
    await callback.message.edit_text(new_text, parse_mode="HTML")
    await callback.answer()

    await bot.send_message(user_id, "💫")
    
    onboarding_content = get_onboarding_content()
    step_0_content = onboarding_content[0]
    await bot.send_photo(
        chat_id=user_id,
        photo=step_0_content["photo_id"],
        caption=step_0_content["text"],
        reply_markup=get_onboarding_keyboard(step=0)
    )

@router.callback_query(AdminAction.filter(F.action == "reject"))
async def admin_reject_handler(callback: types.CallbackQuery, callback_data: AdminAction):
    user_id = callback_data.user_id
    await bot.send_message(user_id, "❌ К сожалению, ваша заявка была отклонена\\.")

    original_text_html = callback.message.html_text
    admin_username = callback.from_user.username or 'админ'
    new_text = f"{original_text_html}\n\n<b>❌ Отклонена администратором @{admin_username}</b>"
    
    await callback.message.edit_text(new_text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(OnboardingNav.filter())
async def onboarding_navigation_handler(callback: types.CallbackQuery, callback_data: OnboardingNav):
    current_step = callback_data.step
    onboarding_content = get_onboarding_content()
    content = onboarding_content[current_step]
    
    media_to_edit = InputMediaPhoto(
        media=content["photo_id"],
        caption=content["text"]
    )
    
    await callback.message.edit_media(
        media=media_to_edit,
        reply_markup=get_onboarding_keyboard(step=current_step)
    )
    await callback.answer()

@router.callback_query(F.data == "finish_onboarding")
async def finish_onboarding_handler(callback: types.CallbackQuery):
    await callback.answer()
    
    final_caption_html = f"{callback.message.html_text}\n\n<b>Завершено</b>"
    await callback.message.edit_caption(
        caption=final_caption_html,
        reply_markup=None,
        parse_mode="HTML"
    )

    await callback.message.answer("💫")
    
    moon_emoji = "🌕"
    quote = "> ⏳ _Пока ты отдыхаешь, кто\\-то другой забирает твои деньги\\. Рынок не спит, и возможности уходят к тем, кто действует прямо сейчас\\._"
    
    links = settings.links
    # Экранируем символы для ссылок
    manuals_link = links.manuals.replace('-', r'\-')
    chat_link = links.chat.replace('-', r'\-')
    payouts_link = links.payouts.replace('-', r'\-')
    connections_link = links.connections.replace('-', r'\-')

    tools_section = (
        "*Инструменты:*\n"
        f"└ [Мануалы]({manuals_link}) "
        f"\\| [Чат]({chat_link}) "
        f"\\| [Выплаты]({payouts_link}) "
        f"\\| [Подключения]({connections_link})"
        f"\\| [Профиты](https://t.me/+2kjzE41I1yswNzJi)"
    )
    
    menu_text = (
        "*🚀 Главное меню*\n\n"
        "*Статусы:*\n"
        f"Ликвидность: {moon_emoji}\n"
        f"Звёзды: {moon_emoji}\n\n"
        f"{tools_section}\n\n"
        f"{quote}"
    )
    
    await callback.message.answer(
        menu_text,
        reply_markup=get_worker_menu_keyboard(),
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "liquidity_menu")
async def show_liquidity_menu_handler(callback: types.CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    bot_username = "NFTScanero_Bot"
    
    referral_link = f"`https://t.me/{bot_username}?start={user_id}`"
    
    # Экранируем дефис в URL
    instruction_link = settings.links.drainer_instruction.replace('-', r'\-')

    liquidity_text = (
        "*Управление ликвидностью* 💧\n\n"
        f"📝 *Инструкция к боту:* [ТЫК]({instruction_link})\n\n"
        f"📋 *Ваш код:* `{user_id}`\n"
        f"🔗 *Ваша реферальная ссылка:*\n{referral_link}\n\n"
        f"> _Главный секрет успеха — начать действовать, а не размышлять о действиях\\._"
    )
    
    await callback.message.edit_text(
        liquidity_text,
        reply_markup=get_back_to_menu_keyboard(),
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "stars_menu")
async def show_stars_menu_handler(callback: types.CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    bot_username = "CheckForStarsBot"
    
    referral_link = f"`https://t.me/{bot_username}?start={user_id}`"

    # Экранируем дефис в URL
    instruction_link = settings.links.drainer_instruction.replace('-', r'\-')

    # ИСПРАВЛЕНИЕ: Экранируем скобки вокруг юзернейма
    stars_text = (
        "*Сервис по работе со звёздами* ⭐\n\n"
        f"📝 *Инструкция к боту:* [ТЫК]({instruction_link})\n\n"
        f"📋 *Ваш код:* `{user_id}`\n"
        f"🔗 *Ваша реферальная ссылка:*\n{referral_link}\n\n"
        f"> _Используйте инлайн\\-режим \\(`@{bot_username}`\\) для создания чеков на звёзды\\._"
    )
    
    await callback.message.edit_text(
        stars_text,
        reply_markup=get_back_to_menu_keyboard(),
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "show_profile")
async def show_profile_handler(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    worker_data = get_worker_data(user_id)
    if not worker_data:
        await callback.message.edit_text("Не удалось найти ваши данные\\.")
        return

    db_user_id, username, first_name, join_date_str = worker_data
    
    join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S")
    days_in_team = (datetime.now() - join_date).days

    safe_username = f"@{escape_md(username)}" if username else "Нет"
    
    profile_text = (
        "*Профиль Воркера* 🪪\n\n"
        f"├ *ID:* `{db_user_id}`\n"
        f"├ *Никнейм:* {safe_username}\n"
        f"└ *В команде:* {days_in_team} дней\n\n"
        f"> _Каждый новый день — это шанс стать лучше, чем вчера\\. Не упускай его\\._"
    )

    await callback.message.edit_text(profile_text, reply_markup=get_back_to_menu_keyboard())

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: types.CallbackQuery):
    await callback.answer()
    
    moon_emoji = "🌕"
    quote = "> ⏳ _Пока ты отдыхаешь, кто\\-то другой забирает твои деньги\\. Рынок не спит, и возможности уходят к тем, кто действует прямо сейчас\\._"
    
    links = settings.links
    # Экранируем символы для ссылок
    manuals_link = links.manuals.replace('-', r'\-')
    chat_link = links.chat.replace('-', r'\-')
    payouts_link = links.payouts.replace('-', r'\-')
    connections_link = links.connections.replace('-', r'\-')

    tools_section = (
        "*Инструменты:*\n"
        f"└ [Мануалы]({manuals_link}) "
        f"\\| [Чат]({chat_link}) "
        f"\\| [Выплаты]({payouts_link}) "
        f"\\| [Подключения]({connections_link})"
        f"\\| [Профиты](https://t.me/+2kjzE41I1yswNzJi)"
    )
    
    menu_text = (
        "*🚀 Главное меню*\n\n"
        "*Статусы:*\n"
        f"Ликвидность: {moon_emoji}\n"
        f"Звёзды: {moon_emoji}\n\n"
        f"{tools_section}\n\n"
        f"{quote}"
    )
    
    await callback.message.edit_text(
        menu_text,
        reply_markup=get_worker_menu_keyboard(),
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "show_info")
async def show_info_handler(callback: types.CallbackQuery):
    await callback.answer()
    
    info_text = (
    "*💁‍♀️ Информация о проекте*\n\n"
    "*Статистика:*\n"
    "├ Мы открылись: `27\\.07\\.2025`\n"
    "├ Количество профитов: `5`\n"
    "└ Общая сумма профитов: `30$`\n\n"
    
    "*Выплаты проекта:*\n"
    "• Профит \\- 70%\n"
    "• Профит с помощью тех\\. поддержки \\- 60%\n\n"
    
    "*Состояние сервисов:*\n"
    "├ 🌕 Ликвидность\n"
    "├ 🌕 Звёзды\n"
    "└ 🌕 Общий статус: Ворк\n\n"
    
    "> _Знание — это сила, которая всегда с тобой\\. Используй её\\._"
	)
    
    await callback.message.edit_text(
        info_text,
        reply_markup=get_info_keyboard()
    )