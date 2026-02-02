# handlers.py
from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import get_start_keyboard, get_confirm_application_keyboard, get_worker_menu_keyboard, get_admin_panel_keyboard
from bot_instance import bot
from database import is_worker, is_admin, get_setting
from settings import settings

def escape_md(text: str) -> str:
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in special_chars else char for char in text)

router = Router()

class ApplicationForm(StatesGroup):
    source_info = State()
    experience_info = State()

@router.message(Command("admin"))
async def admin_panel_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде\\.")
        return
    
    current_mode = get_setting('withdrawal_mode', 'auto')
    
    await message.answer(
        "⚙️ *Добро пожаловать в админ\\-панель\\!*",
        reply_markup=get_admin_panel_keyboard(current_mode)
    )

@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    if not settings.bot.bot_enabled:
        await message.answer("Бот на технических работах\\. Попробуйте позже\\.")
        return

    if is_worker(message.from_user.id):
        # Ставим статус "работает" для обоих сервисов
        moon_emoji = "🌕" 
        quote = "> ⏳ _Пока ты отдыхаешь, кто\\-то другой забирает твои деньги\\. Рынок не спит, и возможности уходят к тем, кто действует прямо сейчас\\._"
        
        links = settings.links
        tools_section = (
            "*Инструменты:*\n"
            f"└ [Мануалы]({links.manuals}) "
            f"\\| [Чат]({links.chat}) "
            f"\\| [Выплаты]({links.payouts}) "
            f"\\| [Подключения]({links.connections})"
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
        
        await message.answer(
            menu_text,
            reply_markup=get_worker_menu_keyboard(),
            disable_web_page_preview=True
        )
        return

    escaped_name = escape_md((await bot.get_me()).first_name)
    bot_name = f"*{escaped_name}*"
    text = f"Привет, это бот {bot_name}\\.\nЧтобы начать работу у нас, подай заявку\\."
    await message.answer(text=text, reply_markup=get_start_keyboard())

@router.message(ApplicationForm.source_info)
async def process_source_info(message: types.Message, state: FSMContext):
    await state.update_data(source=message.text)
    await state.set_state(ApplicationForm.experience_info)
    await message.answer("*У вас есть опыт работы в такой сфере\\?*")

@router.message(ApplicationForm.experience_info)
async def process_experience_info(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    data = await state.get_data()
    
    source = escape_md(data.get('source', ''))
    experience = escape_md(data.get('experience', ''))
    
    text = (
        "Ваша заявка готова к отправке на проверку\\!\n\n"
        f"1️⃣ *Откуда Вы узнали о нас:* {source}\n"
        f"2️⃣ *Ваш опыт работы:* {experience}"
    )
    await message.answer(text, reply_markup=get_confirm_application_keyboard())