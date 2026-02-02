# keyboards.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from settings import settings

class AdminPanel(CallbackData, prefix="admin_panel"):
    action: str

def get_start_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="Подать заявку 🛸", callback_data="apply_request")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_accept_rules_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="✅ Принимаю", callback_data="accept_rules")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_application_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Отправить", callback_data="send_application")],
        [InlineKeyboardButton(text="✍️ Изменить", callback_data="edit_application")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

class AdminAction(CallbackData, prefix="admin"):
    action: str
    user_id: int

def get_admin_moderation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=AdminAction(action="accept", user_id=user_id).pack()),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=AdminAction(action="reject", user_id=user_id).pack())
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

class OnboardingNav(CallbackData, prefix="onboarding"):
    step: int

def get_onboarding_keyboard(step: int) -> InlineKeyboardMarkup:
    buttons = []
    nav_buttons = []

    if step > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=OnboardingNav(step=step - 1).pack()))
    
    if step < 3:
        nav_buttons.append(InlineKeyboardButton(text="Далее ➡️", callback_data=OnboardingNav(step=step + 1).pack()))
    
    buttons.append(nav_buttons)

    if step == 3:
        buttons[0].append(InlineKeyboardButton(text="✅ Завершить", callback_data="finish_onboarding"))

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_worker_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="💧 Ликвидность", callback_data="liquidity_menu"),
            InlineKeyboardButton(text="⭐ Звёзды", callback_data="stars_menu")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"),
            InlineKeyboardButton(text="ℹ️ Информация", callback_data="show_info")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_info_keyboard() -> InlineKeyboardMarkup:
    links = settings.links
    buttons = [
        [
            InlineKeyboardButton(text="📚 Мануалы", url=links.manuals),
            InlineKeyboardButton(text="💬 Чат", url=links.chat)
        ],
        [
            InlineKeyboardButton(text="💸 Выплаты", url=links.payouts),
            InlineKeyboardButton(text="🔗 Подключения", url=links.connections)
        ],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_panel_keyboard(current_mode: str) -> InlineKeyboardMarkup:
    mode_text = "Автоматический Авто" if current_mode == 'auto' else "Ручной ✍️"
    buttons = [
        [InlineKeyboardButton(text=f"Режим вывода: {mode_text}", callback_data=AdminPanel(action="toggle_mode").pack())],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)