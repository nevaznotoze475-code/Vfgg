TOKEN = "8297296486:AAGyMV3Mir10Ja0aXMIY2aFJGb13-n6keAI" # токен бота
ADMIN_IDS = [5858391454] # ид админа

import telebot
from telebot import types
from tinydb import TinyDB, Query
import time
import random
import os
from datetime import datetime, timedelta

bot = telebot.TeleBot(TOKEN)
db = TinyDB("data.jsuon")
users = db.table("users")
media_db = db.table("media")
promocodes = db.table("promocodes")
settings = db.table("settings")
user_states = db.table("user_states")
payments = db.table("payments")
channels = db.table("channels")  # Новая таблица для каналов

def initialize_settings():
    if not settings.all():
        settings.insert({
            "bonus_amount": 1, 
            "bonus_cooldown": 3600, 
            "referral_reward": 12,
            "subscription_required": False
        })

initialize_settings()

def create_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📸 Фото (1💰)", "🎥 Видео (2💰)")
    markup.add("👤 Профиль", "🎁 Бонус")
    markup.add("🔑 Промокод", "💸 Пополнить баланс")
    markup.add("🤝 Реферальная система")
    return markup

def create_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🖼 Добавить фото", callback_data="admin_add_photo"),
        types.InlineKeyboardButton("🎬 Добавить видео", callback_data="admin_add_video"),
        types.InlineKeyboardButton("🔑 Промокоды", callback_data="admin_promocodes_menu"),
        types.InlineKeyboardButton("📢 Каналы", callback_data="admin_channels_menu"),
        types.InlineKeyboardButton("⚙ Настройки", callback_data="admin_settings")
    )
    return markup

def create_channels_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Добавить канал", callback_data="admin_add_channel"),
        types.InlineKeyboardButton("➖ Удалить канал", callback_data="admin_delete_channel"),
        types.InlineKeyboardButton("📋 Список каналов", callback_data="admin_list_channels"),
        types.InlineKeyboardButton("✅ Проверить доступ бота", callback_data="admin_check_bot_access"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back")
    )
    return markup

def create_promocodes_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Добавить промокод", callback_data="admin_add_promo"),
        types.InlineKeyboardButton("➖ Удалить промокод", callback_data="admin_delete_promo"),
        types.InlineKeyboardButton("📋 Список промокодов", callback_data="admin_list_promocodes"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back")
    )
    return markup

def create_settings_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    settings_data = settings.all()[0]
    subscription_status = "✅ ВКЛ" if settings_data.get("subscription_required", False) else "❌ ВЫКЛ"
    
    markup.add(
        types.InlineKeyboardButton("🎁 Изменить бонус", callback_data="admin_change_bonus"),
        types.InlineKeyboardButton("⏱ Изменить время бонуса", callback_data="admin_change_cooldown"),
        types.InlineKeyboardButton("🤝 Изменить реф. награду", callback_data="admin_change_referral"),
        types.InlineKeyboardButton(f"📢 Подписка на каналы: {subscription_status}", 
                                  callback_data="admin_toggle_subscription"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back")
    )
    return markup

def create_referral_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Топ 10 рефералов", callback_data="top_referrals"))
    return markup

def create_users_keyboard(page=0, per_page=10):
    all_users = users.all()
    total_pages = (len(all_users) + per_page - 1) // per_page
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_users = all_users[start_idx:end_idx]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_users_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Вперёд ➡️", callback_data=f"admin_users_page_{page+1}"))
    
    if nav_buttons:
        markup.add(*nav_buttons)
    
    markup.add(types.InlineKeyboardButton("📥 Экспорт в TXT", callback_data="admin_export_users"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    
    return markup, page_users, total_pages

def check_user_subscription(user_id):
    """Проверка подписки пользователя на все каналы"""
    all_channels = channels.all()
    settings_data = settings.all()[0]
    
    if not settings_data.get("subscription_required", False) or not all_channels:
        return True, []
    
    not_subscribed = []
    
    for channel in all_channels:
        try:
            chat_member = bot.get_chat_member(channel["channel_id"], user_id)
            if chat_member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except Exception as e:
            print(f"Ошибка проверки подписки для {user_id} в канале {channel['channel_id']}: {e}")
            not_subscribed.append(channel)
    
    return len(not_subscribed) == 0, not_subscribed

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    try:
        bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        print(f"Ошибка отправки сообщения {chat_id}: {e}")

def get_user_stats():
    now = datetime.now()
    periods = {"day": now - timedelta(days=1), "week": now - timedelta(days=7), "month": now - timedelta(days=30)}
    stats = {
        "users": {"total": len(users.all())}, 
        "payments": {"total": len(payments.all())},
        "channels": {"total": len(channels.all())}
    }
    
    for period, date in periods.items():
        stats["users"][period] = len(users.search(Query().registration_date.test(lambda x: datetime.strptime(x, "%Y-%m-%d") >= date)))
        stats["payments"][period] = len(payments.search(Query().timestamp.test(lambda x: datetime.fromtimestamp(x) >= date)))
    
    return stats

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    try:
                        if chat.username:
                            invite_link = f"https://t.me/{chat.username}"
                        elif str(channel["channel_id"]).startswith('-100'):
                            invite_link = f"https://t.me/c/{str(channel['channel_id'])[4:]}"
                        else:
                            invite_link = f"https://t.me/{channel['channel_id']}"
                    except:
                        pass
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_start"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    user = users.get(Query().id == user_id)
    
    if not user:
        referrer_id = message.text.split(" ")[1] if " " in message.text and message.text.split(" ")[1].isdigit() else None
        registration_date = datetime.now().strftime("%Y-%m-%d")
        users.insert({
            "id": user_id, 
            "balance": 0, 
            "last_bonus": 0, 
            "invited": 0, 
            "registration_date": registration_date, 
            "used_promocodes": [], 
            "username": username, 
            "first_name": message.from_user.first_name or "",
            "last_name": message.from_user.last_name or ""
        })
        
        if referrer_id and int(referrer_id) != user_id:
            referrer = users.get(Query().id == int(referrer_id))
            if referrer:
                reward = settings.all()[0]["referral_reward"]
                users.update({"balance": referrer["balance"] + reward, "invited": referrer["invited"] + 1}, Query().id == int(referrer_id))
                send_message(int(referrer_id), f"🎉 @{referrer.get('username', 'друг')}, по твоей ссылке зарегистрировался новый пользователь!\n\n"
                                             f"Ты получил <b><code>{reward}</code></b> 💰!")
    else:
        registration_date = user["registration_date"]
    
    send_message(user_id, "⚡️")
    send_message(user_id, f"<b>🎉 Привет, @{username}, спасибо что заглянул ко мне!</b>\n\n"
                         f"<b>😎 Кстати, ты с нами уже с</b> <code>{registration_date}</code>", create_main_keyboard())

@bot.message_handler(commands=["admin"])
def admin_menu(message):
    user_id = message.chat.id
    if user_id in ADMIN_IDS:
        send_message(user_id, "<b>👨‍💻 Админ-панель</b>\n\nВыберите действие:", create_admin_keyboard())
    else:
        username = message.from_user.username or "друг"
        send_message(user_id, f"🚫 @{username}, доступ запрещен!")

@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_profile"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    user = users.get(Query().id == user_id)
    if user:
        ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        send_message(user_id, f"👤 <b>Профиль @{username}</b>\n\n"
                            f"🧑 <b>Твой ID:</b> <code>{user['id']}</code>\n"
                            f"📅 <b>С нами с:</b> <code>{user['registration_date']}</code>\n"
                            f"💰 <b>Баланс:</b> <code>{user['balance']}</code> монет\n"
                            f"🤝 <b>Приглашено:</b> <code>{user['invited']}</code>\n\n"
                            f"🔗 <b>Твоя реф. ссылка:</b> <code>{ref_link}</code>")

@bot.message_handler(func=lambda message: message.text == "🎁 Бонус")
def bonus(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_bonus"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    user = users.get(Query().id == user_id)
    if user:
        current_time = int(time.time())
        settings_data = settings.all()[0]
        remaining_time = settings_data["bonus_cooldown"] - (current_time - user["last_bonus"])
        if remaining_time <= 0:
            users.update({"balance": user["balance"] + settings_data["bonus_amount"], "last_bonus": current_time}, Query().id == user_id)
            send_message(user_id, f"🎉 @{username}, ты получил <b><code>{settings_data['bonus_amount']}</code> 💰</b>!")
        else:
            hours = remaining_time // 3600
            minutes = (remaining_time % 3600) // 60
            send_message(user_id, f"⏳ @{username}, бонус будет через <b><code>{hours}</code> ч. <code>{minutes}</code> мин.</b>")

@bot.message_handler(func=lambda message: message.text == "🔑 Промокод")
def promo_start(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_promo"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    user_states.upsert({"id": user_id, "state": "enter_promo"}, Query().id == user_id)
    send_message(user_id, f"🔑 @{username}, введи промокод для активации!")

@bot.message_handler(func=lambda message: user_states.get(Query().id == message.chat.id) and user_states.get(Query().id == message.chat.id).get("state") == "enter_promo")
def activate_promo(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    code = message.text.strip()
    user = users.get(Query().id == user_id)
    promo = promocodes.get(Query().name == code)
    
    if not promo:
        send_message(user_id, f"😕 @{username}, промокод не найден!")
    elif code in user.get("used_promocodes", []):
        send_message(user_id, f"🚫 @{username}, ты уже использовал этот промокод!")
    elif promo["activations"] <= 0:
        send_message(user_id, f"😔 @{username}, промокод исчерпан!")
    else:
        used_promocodes = user.get("used_promocodes", [])
        used_promocodes.append(code)
        users.update({"balance": user["balance"] + promo["reward"], "used_promocodes": used_promocodes}, Query().id == user_id)
        promocodes.update({"activations": promo["activations"] - 1}, Query().name == code)
        send_message(user_id, f"🎉 @{username}, промокод активирован!\n\n"
                            f"💰 Ты получил <b><code>{promo['reward']}</code> монет</b>!")
    
    user_states.remove(Query().id == user_id)

@bot.message_handler(func=lambda message: message.text == "💸 Пополнить баланс")
def top_up_balance(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_topup"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    user_states.upsert({"id": user_id, "state": "enter_topup_amount"}, Query().id == user_id)
    send_message(user_id, f"💸 @{username}, введи сумму для пополнения!\n\n"
                        f"⭐ <b>1 монета = 1 звезда</b>")

@bot.message_handler(func=lambda message: user_states.get(Query().id == message.chat.id) and user_states.get(Query().id == message.chat.id).get("state") == "enter_topup_amount")
def process_topup_amount(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    if not message.text.isdigit() or int(message.text) <= 0:
        send_message(user_id, f"😕 @{username}, введи корректное число!")
        return
    
    amount = int(message.text)
    user_states.update({"state": "awaiting_payment", "amount": amount}, Query().id == user_id)
    
    prices = [types.LabeledPrice(label="Пополнение баланса", amount=amount)]
    bot.send_invoice(
        chat_id=user_id,
        title="Пополнение баланса",
        description=f"Пополнение на {amount} монет",
        invoice_payload=f"topup_{user_id}_{amount}",
        provider_token="",
        currency="XTR",
        prices=prices,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    payment = message.successful_payment
    payload = payment.invoice_payload
    
    if payload.startswith("topup_"):
        _, user_id_from_payload, amount = payload.split("_")
        user_id_from_payload = int(user_id_from_payload)
        amount = int(amount)
        
        if user_id == user_id_from_payload:
            user = users.get(Query().id == user_id)
            users.update({"balance": user["balance"] + amount}, Query().id == user_id)
            payments.insert({"user_id": user_id, "amount": amount, "timestamp": int(time.time()), "payment_id": payment.telegram_payment_charge_id})
            send_message(user_id, f"🎉 @{username}, баланс пополнен!\n\n"
                                f"💰 Ты получил <b><code>{amount}</code> монет</b>!")
    
    user_states.remove(Query().id == user_id)

@bot.message_handler(func=lambda message: message.text == "📸 Фото (1💰)")
def send_photo(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_photo"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    user = users.get(Query().id == user_id)
    if user and user["balance"] >= 1:
        photos = media_db.search(Query().type == "photo")
        if photos:
            photo = random.choice(photos)
            try:
                bot.send_photo(user_id, photo["file_id"])
                users.update({"balance": user["balance"] - 1}, Query().id == user_id)
                send_message(user_id, f"📸 @{username}, вот твоё фото!\n\n"
                                    f"💰 Баланс: <b><code>{user['balance'] - 1}</code></b> монет")
                return
            except:
                media_db.remove(Query().file_id == photo["file_id"])
        send_message(user_id, f"😔 @{username}, нет доступных фото!")
    else:
        send_message(user_id, f"🚫 @{username}, недостаточно монет!")

@bot.message_handler(func=lambda message: message.text == "🎥 Видео (2💰)")
def send_video(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_video"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    user = users.get(Query().id == user_id)
    if user and user["balance"] >= 2:
        videos = media_db.search(Query().type == "video")
        if videos:
            video = random.choice(videos)
            try:
                bot.send_video(user_id, video["file_id"])
                users.update({"balance": user["balance"] - 2}, Query().id == user_id)
                send_message(user_id, f"🎥 @{username}, вот твоё видео!\n\n"
                                    f"💰 Баланс: <b><code>{user['balance'] - 2}</code></b> монет")
                return
            except:
                media_db.remove(Query().file_id == video["file_id"])
        send_message(user_id, f"😔 @{username}, нет доступных видео!")
    else:
        send_message(user_id, f"🚫 @{username}, недостаточно монет!")

@bot.message_handler(func=lambda message: message.text == "🤝 Реферальная система")
def referral_system(message):
    user_id = message.chat.id
    username = message.from_user.username or "друг"
    
    subscribed, not_subscribed_channels = check_user_subscription(user_id)
    settings_data = settings.all()[0]
    
    if not subscribed and settings_data.get("subscription_required", False):
        text = "📢 <b>Для использования бота необходимо подписаться на каналы:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                channel_name = chat.title
                invite_link = channel.get("invite_link", "")
                
                if not invite_link:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                
                text += f"• {channel_name}\n"
                if invite_link:
                    markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
            except:
                text += f"• Канал ID: {channel['channel_id']}\n"
        
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_ref"))
        
        send_message(user_id, text, reply_markup=markup)
        return
    
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    reward = settings.all()[0]["referral_reward"]
    send_message(user_id, f"🤝 <b>Реферальная система для @{username}</b>\n\n"
                        f"🔥 Приглашай друзей и получай <b><code>{reward}</code></b> монет за каждого, кто зарегистрируется по твоей ссылке!\n\n"
                        f"🔗 <b>Твоя реф. ссылка:</b> <code>{ref_link}</code>", create_referral_keyboard())

@bot.message_handler(content_types=['photo'], func=lambda message: message.chat.id in ADMIN_IDS and user_states.get(Query().id == message.chat.id) and user_states.get(Query().id == message.chat.id).get("state") == "awaiting_photo")
def handle_admin_photo(message):
    user_id = message.chat.id
    file_id = message.photo[-1].file_id
    media_db.insert({"file_id": file_id, "type": "photo", "added_by": user_id, "timestamp": int(time.time())})
    user_states.remove(Query().id == user_id)
    send_message(user_id, f"✅ Фото успешно добавлено в базу!\n\n"
                         f"📊 Всего фото: {len(media_db.search(Query().type == 'photo'))}")

@bot.message_handler(content_types=['video'], func=lambda message: message.chat.id in ADMIN_IDS and user_states.get(Query().id == message.chat.id) and user_states.get(Query().id == message.chat.id).get("state") == "awaiting_video")
def handle_admin_video(message):
    user_id = message.chat.id
    file_id = message.video.file_id
    media_db.insert({"file_id": file_id, "type": "video", "added_by": user_id, "timestamp": int(time.time())})
    user_states.remove(Query().id == user_id)
    send_message(user_id, f"✅ Видео успешно добавлено в базу!\n\n"
                         f"📊 Всего видео: {len(media_db.search(Query().type == 'video'))}")

@bot.message_handler(func=lambda message: message.chat.id in ADMIN_IDS and user_states.get(Query().id == message.chat.id) and user_states.get(Query().id == message.chat.id).get("state") == "awaiting_channel")
def handle_admin_channel(message):
    user_id = message.chat.id
    text = message.text.strip()
    channel_id = None
    
    if text.startswith('@'):
        try:
            chat = bot.get_chat(text)
            if chat.type in ['channel', 'supergroup']:
                channel_id = chat.id
                channel_name = chat.title
                invite_link = f"https://t.me/{chat.username}" if chat.username else None
            else:
                send_message(user_id, "❌ Это не канал или супергруппа!")
                return
        except Exception as e:
            send_message(user_id, f"❌ Ошибка: {e}")
            return
    elif text.startswith('https://t.me/'):
        try:
            username = text.split('/')[-1]
            if username.startswith('@'):
                username = username[1:]
            chat = bot.get_chat(f"@{username}")
            if chat.type in ['channel', 'supergroup']:
                channel_id = chat.id
                channel_name = chat.title
                invite_link = text
            else:
                send_message(user_id, "❌ Это не канал или супергруппа!")
                return
        except Exception as e:
            send_message(user_id, f"❌ Ошибка: {e}")
            return
    elif text.lstrip('-').isdigit():
        channel_id = int(text)
        try:
            chat = bot.get_chat(channel_id)
            if chat.type in ['channel', 'supergroup']:
                channel_name = chat.title
                invite_link = f"https://t.me/{chat.username}" if chat.username else None
            else:
                send_message(user_id, "❌ Это не канал или супергруппа!")
                return
        except Exception as e:
            send_message(user_id, f"❌ Ошибка: {e}")
            return
    else:
        send_message(user_id, "❌ Неверный формат! Используйте:\n• @username\n• https://t.me/username\n• ID канала")
        return
    
    existing_channel = channels.get(Query().channel_id == channel_id)
    if existing_channel:
        send_message(user_id, f"❌ Канал {channel_name} уже добавлен!")
        return
    
    channels.insert({
        "channel_id": channel_id,
        "channel_name": channel_name,
        "invite_link": invite_link,
        "added_by": user_id,
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    user_states.remove(Query().id == user_id)
    send_message(user_id, f"✅ Канал <b>{channel_name}</b> успешно добавлен!\n\n"
                         f"ID: <code>{channel_id}</code>\n"
                         f"Ссылка: {invite_link if invite_link else 'Недоступна'}", 
                         create_channels_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data.startswith("check_subscription_"):
        action = call.data.replace("check_subscription_", "")
        
        subscribed, not_subscribed_channels = check_user_subscription(user_id)
        
        if not subscribed:
            bot.answer_callback_query(call.id, "❌ Вы не подписались на все каналы!", show_alert=True)
            
            text = "📢 <b>Вы не подписались на все каналы:</b>\n\n"
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            for channel in not_subscribed_channels:
                try:
                    chat = bot.get_chat(channel["channel_id"])
                    channel_name = chat.title
                    invite_link = channel.get("invite_link", "")
                    if not invite_link:
                        if chat.username:
                            invite_link = f"https://t.me/{chat.username}"
                    
                    text += f"• {channel_name}\n"
                    if invite_link:
                        markup.add(types.InlineKeyboardButton(f"📢 {channel_name}", url=invite_link))
                except:
                    text += f"• Канал ID: {channel['channel_id']}\n"
            
            markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data=f"check_subscription_{action}"))
            
            try:
                bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
            except:
                pass
            return
        
        bot.answer_callback_query(call.id, "✅ Отлично! Вы подписаны на все каналы!")
        
        if action == "start":
            username = call.from_user.username or "друг"
            user = users.get(Query().id == user_id)
            
            if user:
                registration_date = user["registration_date"]
            else:
                registration_date = datetime.now().strftime("%Y-%m-%d")
                users.insert({"id": user_id, "balance": 0, "last_bonus": 0, "invited": 0, 
                            "registration_date": registration_date, "used_promocodes": [], 
                            "username": username, "first_name": call.from_user.first_name or "",
                            "last_name": call.from_user.last_name or ""})
            
            try:
                bot.delete_message(user_id, message_id)
            except:
                pass
            
            send_message(user_id, "⚡️")
            send_message(user_id, f"<b>🎉 Привет, @{username}, спасибо что заглянул ко мне!</b>\n\n"
                                f"<b>😎 Кстати, ты с нами уже с</b> <code>{registration_date}</code>", create_main_keyboard())
        
        elif action == "profile":
            user = users.get(Query().id == user_id)
            if user:
                ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
                try:
                    bot.delete_message(user_id, message_id)
                except:
                    pass
                send_message(user_id, f"👤 <b>Профиль @{call.from_user.username or 'друг'}</b>\n\n"
                                    f"🧑 <b>Твой ID:</b> <code>{user['id']}</code>\n"
                                    f"📅 <b>С нами с:</b> <code>{user['registration_date']}</code>\n"
                                    f"💰 <b>Баланс:</b> <code>{user['balance']}</code> монет\n"
                                    f"🤝 <b>Приглашено:</b> <code>{user['invited']}</code>\n\n"
                                    f"🔗 <b>Твоя реф. ссылка:</b> <code>{ref_link}</code>")
        
        elif action == "bonus":
            username = call.from_user.username or "друг"
            user = users.get(Query().id == user_id)
            if user:
                current_time = int(time.time())
                settings_data = settings.all()[0]
                remaining_time = settings_data["bonus_cooldown"] - (current_time - user["last_bonus"])
                if remaining_time <= 0:
                    users.update({"balance": user["balance"] + settings_data["bonus_amount"], "last_bonus": current_time}, Query().id == user_id)
                    try:
                        bot.delete_message(user_id, message_id)
                    except:
                        pass
                    send_message(user_id, f"🎉 @{username}, ты получил <b><code>{settings_data['bonus_amount']}</code> 💰</b>!")
                else:
                    hours = remaining_time // 3600
                    minutes = (remaining_time % 3600) // 60
                    try:
                        bot.delete_message(user_id, message_id)
                    except:
                        pass
                    send_message(user_id, f"⏳ @{username}, бонус будет через <b><code>{hours}</code> ч. <code>{minutes}</code> мин.</b>")
        
        elif action == "promo":
            username = call.from_user.username or "друг"
            user_states.upsert({"id": user_id, "state": "enter_promo"}, Query().id == user_id)
            try:
                bot.delete_message(user_id, message_id)
            except:
                pass
            send_message(user_id, f"🔑 @{username}, введи промокод для активации!")
        
        elif action == "topup":
            username = call.from_user.username or "друг"
            user_states.upsert({"id": user_id, "state": "enter_topup_amount"}, Query().id == user_id)
            try:
                bot.delete_message(user_id, message_id)
            except:
                pass
            send_message(user_id, f"💸 @{username}, введи сумму для пополнения!\n\n"
                                f"⭐ <b>1 монета = 1 звезда</b>")
        
        elif action == "photo":
            username = call.from_user.username or "друг"
            user = users.get(Query().id == user_id)
            if user and user["balance"] >= 1:
                photos = media_db.search(Query().type == "photo")
                if photos:
                    photo = random.choice(photos)
                    try:
                        bot.delete_message(user_id, message_id)
                    except:
                        pass
                    try:
                        bot.send_photo(user_id, photo["file_id"])
                        users.update({"balance": user["balance"] - 1}, Query().id == user_id)
                        send_message(user_id, f"📸 @{username}, вот твоё фото!\n\n"
                                            f"💰 Баланс: <b><code>{user['balance'] - 1}</code></b> монет")
                        return
                    except:
                        media_db.remove(Query().file_id == photo["file_id"])
                try:
                    bot.delete_message(user_id, message_id)
                except:
                    pass
                send_message(user_id, f"😔 @{username}, нет доступных фото!")
            else:
                try:
                    bot.delete_message(user_id, message_id)
                except:
                    pass
                send_message(user_id, f"🚫 @{username}, недостаточно монет!")
        
        elif action == "video":
            username = call.from_user.username or "друг"
            user = users.get(Query().id == user_id)
            if user and user["balance"] >= 2:
                videos = media_db.search(Query().type == "video")
                if videos:
                    video = random.choice(videos)
                    try:
                        bot.delete_message(user_id, message_id)
                    except:
                        pass
                    try:
                        bot.send_video(user_id, video["file_id"])
                        users.update({"balance": user["balance"] - 2}, Query().id == user_id)
                        send_message(user_id, f"🎥 @{username}, вот твоё видео!\n\n"
                                            f"💰 Баланс: <b><code>{user['balance'] - 2}</code></b> монет")
                        return
                    except:
                        media_db.remove(Query().file_id == video["file_id"])
                try:
                    bot.delete_message(user_id, message_id)
                except:
                    pass
                send_message(user_id, f"😔 @{username}, нет доступных видео!")
            else:
                try:
                    bot.delete_message(user_id, message_id)
                except:
                    pass
                send_message(user_id, f"🚫 @{username}, недостаточно монет!")
        
        elif action == "ref":
            username = call.from_user.username or "друг"
            ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
            reward = settings.all()[0]["referral_reward"]
            try:
                bot.delete_message(user_id, message_id)
            except:
                pass
            send_message(user_id, f"🤝 <b>Реферальная система для @{username}</b>\n\n"
                                f"🔥 Приглашай друзей и получай <b><code>{reward}</code></b> монет за каждого, кто зарегистрируется по твоей ссылке!\n\n"
                                f"🔗 <b>Твоя реф. ссылка:</b> <code>{ref_link}</code>", create_referral_keyboard())
        
        return
    
    if call.data == "top_referrals":
        top_users = sorted(users.all(), key=lambda x: x.get("invited", 0), reverse=True)[:10]
        if not top_users or all(u["invited"] == 0 for u in top_users):
            bot.edit_message_text("😔 <b>Пока нет рефералов!</b>", user_id, message_id, parse_mode="HTML")
            return
        
        text = "👥 <b>ТОП-10 пользователей по кол-ву рефералов</b>\n\n№ | Кол-во рефералов | Реферер\n"
        text += "\n".join(f"<code>{i+1}</code> | <code>{u['invited']}</code> | @{u.get('username', 'друг')}"
                         for i, u in enumerate(top_users) if u["invited"] > 0)
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML")
        return
    
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "🚫 Доступ запрещен!", show_alert=True)
        return
    
    if call.data == "admin_back":
        bot.edit_message_text("<b>👨‍💻 Админ-панель</b>\n\nВыберите действие:", user_id, message_id, 
                            parse_mode="HTML", reply_markup=create_admin_keyboard())
    
    elif call.data == "admin_stats":
        stats = get_user_stats()
        media_stats = media_db.all()
        photos = len([m for m in media_stats if m["type"] == "photo"])
        videos = len([m for m in media_stats if m["type"] == "video"])
        settings_data = settings.all()[0]
        subscription_status = "✅ ВКЛ" if settings_data.get("subscription_required", False) else "❌ ВЫКЛ"
        
        text = f"""
📊 <b>Статистика бота</b>

👥 <b>Пользователи</b>
За сутки: <code>{stats['users']['day']}</code>
За неделю: <code>{stats['users']['week']}</code>
За месяц: <code>{stats['users']['month']}</code>
Всего: <code>{stats['users']['total']}</code>

💳 <b>Пополнения</b>
За сутки: <code>{stats['payments']['day']}</code>
За неделю: <code>{stats['payments']['week']}</code>
За месяц: <code>{stats['payments']['month']}</code>
Всего: <code>{stats['payments']['total']}</code>

📢 <b>Каналы</b>
Всего каналов: <code>{stats['channels']['total']}</code>
Обязательная подписка: {subscription_status}

📁 <b>Медиа</b>
Фото: <code>{photos}</code>
Видео: <code>{videos}</code>
Всего: <code>{photos + videos}</code>

⚙️ <b>Настройки</b>
Бонус: <code>{settings_data['bonus_amount']} монет</code>
Время бонуса: <code>{settings_data['bonus_cooldown'] // 3600} часов</code>
Реферальная награда: <code>{settings_data['referral_reward']} монет</code>
        """
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data == "admin_users":
        markup, page_users, total_pages = create_users_keyboard()
        if not page_users:
            bot.edit_message_text("😔 <b>Пока нет пользователей</b>", user_id, message_id, parse_mode="HTML", reply_markup=markup)
            return
        
        text = f"👥 <b>Пользователи (Страница 1/{total_pages})</b>\n\n"
        text += "\n".join(f"{i+1}. @{u.get('username', 'Нет юзернейма')} | ID: <code>{u['id']}</code> | Баланс: <code>{u['balance']}</code> 💰"
                         for i, u in enumerate(page_users))
        
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data.startswith("admin_users_page_"):
        page = int(call.data.split("_")[-1])
        markup, page_users, total_pages = create_users_keyboard(page)
        
        text = f"👥 <b>Пользователи (Страница {page+1}/{total_pages})</b>\n\n"
        text += "\n".join(f"{i+1}. @{u.get('username', 'Нет юзернейма')} | ID: <code>{u['id']}</code> | Баланс: <code>{u['balance']}</code> 💰"
                         for i, u in enumerate(page_users))
        
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data == "admin_export_users":
        all_users = users.all()
        if not all_users:
            bot.answer_callback_query(call.id, "😔 Нет пользователей для экспорта", show_alert=True)
            return
        
        filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ID | Username | Имя | Фамилия | Баланс | Приглашено | Дата регистрации\n")
            f.write("-" * 80 + "\n")
            for user in all_users:
                f.write(f"{user['id']} | @{user.get('username', 'Нет')} | {user.get('first_name', '')} | "
                       f"{user.get('last_name', '')} | {user['balance']} | {user.get('invited', 0)} | "
                       f"{user.get('registration_date', 'Нет данных')}\n")
        
        try:
            with open(filename, 'rb') as f:
                bot.send_document(user_id, f, caption="📥 <b>Экспорт пользователей</b>")
            os.remove(filename)
            bot.answer_callback_query(call.id, "✅ Файл отправлен!")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Ошибка: {e}", show_alert=True)
    
    elif call.data == "admin_broadcast":
        user_states.upsert({"id": user_id, "state": "awaiting_broadcast"}, Query().id == user_id)
        bot.edit_message_text("<b>📢 Рассылка сообщений</b>\n\n"
                            "Отправьте сообщение для рассылки всем пользователям.\n"
                            "Поддерживается HTML разметка.\n\n"
                            "❌ Для отмены отправьте /cancel", user_id, message_id, parse_mode="HTML")
    
    elif call.data == "admin_add_photo":
        user_states.upsert({"id": user_id, "state": "awaiting_photo"}, Query().id == user_id)
        bot.edit_message_text("<b>🖼 Добавление фото</b>\n\n"
                            "Отправьте фото, которое нужно добавить в базу.\n"
                            "❌ Для отмены отправьте /cancel", user_id, message_id, parse_mode="HTML")
    
    elif call.data == "admin_add_video":
        user_states.upsert({"id": user_id, "state": "awaiting_video"}, Query().id == user_id)
        bot.edit_message_text("<b>🎬 Добавление видео</b>\n\n"
                            "Отправьте видео, которое нужно добавить в базу.\n"
                            "❌ Для отмены отправьте /cancel", user_id, message_id, parse_mode="HTML")
    
    elif call.data == "admin_channels_menu":
        bot.edit_message_text("<b>📢 Управление каналами</b>", user_id, message_id, 
                            parse_mode="HTML", reply_markup=create_channels_keyboard())
    
    elif call.data == "admin_add_channel":
        user_states.upsert({"id": user_id, "state": "awaiting_channel"}, Query().id == user_id)
        bot.edit_message_text("<b>➕ Добавление канала</b>\n\n"
                            "Отправьте ссылку на канал, @username или ID канала:\n\n"
                            "Примеры:\n"
                            "• @channel_username\n"
                            "• https://t.me/channel_username\n"
                            "• -1001234567890\n\n"
                            "❌ Для отмены отправьте /cancel", user_id, message_id, parse_mode="HTML")
    
    elif call.data == "admin_delete_channel":
        all_channels = channels.all()
        if not all_channels:
            bot.edit_message_text("<b>😔 Нет каналов для удаления</b>", user_id, message_id, 
                                parse_mode="HTML", reply_markup=create_channels_keyboard())
            return
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in all_channels:
            markup.add(types.InlineKeyboardButton(
                f"📢 {channel.get('channel_name', 'Без названия')}",
                callback_data=f"delete_channel_{channel['channel_id']}"
            ))
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_channels_menu"))
        
        bot.edit_message_text("<b>➖ Удаление канала</b>\n\nВыберите канал для удаления:", 
                            user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data.startswith("delete_channel_"):
        channel_id = int(call.data.replace("delete_channel_", ""))
        channel = channels.get(Query().channel_id == channel_id)
        
        if channel:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("✅ Да", callback_data=f"confirm_delete_channel_{channel_id}"),
                types.InlineKeyboardButton("❌ Нет", callback_data="admin_delete_channel")
            )
            bot.edit_message_text(f"<b>❓ Точно удалить канал {channel.get('channel_name', 'Без названия')}?</b>", 
                                user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data.startswith("confirm_delete_channel_"):
        channel_id = int(call.data.replace("confirm_delete_channel_", ""))
        channel = channels.get(Query().channel_id == channel_id)
        
        if channel:
            channels.remove(Query().channel_id == channel_id)
            bot.answer_callback_query(call.id, f"✅ Канал {channel.get('channel_name', 'Без названия')} удален!")
            bot.edit_message_text("<b>📢 Управление каналов</b>", user_id, message_id, 
                                parse_mode="HTML", reply_markup=create_channels_keyboard())
    
    elif call.data == "admin_list_channels":
        all_channels = channels.all()
        if not all_channels:
            bot.edit_message_text("<b>😔 Нет добавленных каналов</b>", user_id, message_id, 
                                parse_mode="HTML", reply_markup=create_channels_keyboard())
            return
        
        text = "<b>📋 Список каналов</b>\n\n"
        for i, channel in enumerate(all_channels, 1):
            text += f"{i}. <b>{channel.get('channel_name', 'Без названия')}</b>\n"
            text += f"   • ID: <code>{channel['channel_id']}</code>\n"
            text += f"   • Ссылка: {channel.get('invite_link', 'Недоступна')}\n"
            text += f"   • Добавлен: {channel.get('added_date', 'Неизвестно')}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_channels_menu"))
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data == "admin_check_bot_access":
        all_channels = channels.all()
        if not all_channels:
            bot.answer_callback_query(call.id, "😔 Нет каналов для проверки", show_alert=True)
            return
        
        text = "<b>🔍 Проверка доступа бота к каналам</b>\n\n"
        
        for channel in all_channels:
            try:
                chat = bot.get_chat(channel["channel_id"])
                bot_member = bot.get_chat_member(channel["channel_id"], bot.get_me().id)
                
                if bot_member.status in ['administrator', 'creator']:
                    text += f"✅ {chat.title}\n"
                    text += f"   • Бот: администратор\n"
                else:
                    text += f"⚠️ {chat.title}\n"
                    text += f"   • Бот: {bot_member.status}\n"
                    text += f"   • <i>Бот должен быть администратором для проверки подписок</i>\n"
                
                channels.update({
                    "channel_name": chat.title,
                    "invite_link": f"https://t.me/{chat.username}" if chat.username else channel.get("invite_link", "")
                }, Query().channel_id == channel["channel_id"])
                
            except Exception as e:
                text += f"❌ Канал ID: {channel['channel_id']}\n"
                text += f"   • Ошибка: {str(e)[:50]}...\n"
            
            text += "\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_channels_menu"))
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data == "admin_promocodes_menu":
        bot.edit_message_text("<b>🔑 Управление промокодами</b>", user_id, message_id, 
                            parse_mode="HTML", reply_markup=create_promocodes_keyboard())
    
    elif call.data == "admin_add_promo":
        user_states.upsert({"id": user_id, "state": "add_promo_name"}, Query().id == user_id)
        bot.edit_message_text("<b>➕ Добавление промокода</b>\n\n"
                            "Введите название промокода:", user_id, message_id, parse_mode="HTML")
    
    elif call.data == "admin_delete_promo":
        all_promos = promocodes.all()
        if not all_promos:
            bot.edit_message_text("<b>😔 Нет промокодов для удаления</b>", user_id, message_id, 
                                parse_mode="HTML", reply_markup=create_promocodes_keyboard())
            return
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for promo in all_promos:
            markup.add(types.InlineKeyboardButton(
                f"{promo['name']} ({promo['activations']} активаций, {promo['reward']} монет)",
                callback_data=f"delete_promo_{promo['name']}"
            ))
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_promocodes_menu"))
        
        bot.edit_message_text("<b>➖ Удаление промокода</b>\n\nВыберите промокод для удаления:", 
                            user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data == "admin_list_promocodes":
        all_promos = promocodes.all()
        if not all_promos:
            bot.edit_message_text("<b>😔 Нет активных промокодов</b>", user_id, message_id, 
                                parse_mode="HTML", reply_markup=create_promocodes_keyboard())
            return
        
        text = "<b>📋 Список промокодов</b>\n\n"
        for i, promo in enumerate(all_promos, 1):
            text += f"{i}. <code>{promo['name']}</code>\n"
            text += f"   • Награда: {promo['reward']} монет\n"
            text += f"   • Осталось активаций: {promo['activations']}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_promocodes_menu"))
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data.startswith("delete_promo_"):
        promo_name = call.data.replace("delete_promo_", "")
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Да", callback_data=f"confirm_delete_{promo_name}"),
            types.InlineKeyboardButton("❌ Нет", callback_data="admin_delete_promo")
        )
        bot.edit_message_text(f"<b>❓ Точно удалить промокод {promo_name}?</b>", 
                            user_id, message_id, parse_mode="HTML", reply_markup=markup)
    
    elif call.data.startswith("confirm_delete_"):
        promo_name = call.data.replace("confirm_delete_", "")
        promocodes.remove(Query().name == promo_name)
        bot.answer_callback_query(call.id, f"✅ Промокод {promo_name} удален!")
        bot.edit_message_text("<b>🔑 Управление промокодов</b>", user_id, message_id, 
                            parse_mode="HTML", reply_markup=create_promocodes_keyboard())
    
    elif call.data == "admin_settings":
        bot.edit_message_text("<b>⚙ Настройки бота</b>", user_id, message_id, 
                            parse_mode="HTML", reply_markup=create_settings_keyboard())
    
    elif call.data == "admin_toggle_subscription":
        settings_data = settings.all()[0]
        new_status = not settings_data.get("subscription_required", False)
        settings.update({"subscription_required": new_status}, doc_ids=[1])
        
        status_text = "✅ ВКЛЮЧЕНА" if new_status else "❌ ВЫКЛЮЧЕНА"
        bot.answer_callback_query(call.id, f"Обязательная подписка {status_text}")
        bot.edit_message_text("<b>⚙ Настройки бота</b>", user_id, message_id, 
                            parse_mode="HTML", reply_markup=create_settings_keyboard())
    
    elif call.data == "admin_change_bonus":
        user_states.upsert({"id": user_id, "state": "change_bonus"}, Query().id == user_id)
        current = settings.all()[0]["bonus_amount"]
        bot.edit_message_text(f"<b>🎁 Изменение бонуса</b>\n\n"
                            f"Текущее значение: <code>{current}</code> монет\n"
                            f"Введите новое количество монет за бонус:", 
                            user_id, message_id, parse_mode="HTML")
    
    elif call.data == "admin_change_cooldown":
        user_states.upsert({"id": user_id, "state": "change_cooldown"}, Query().id == user_id)
        current = settings.all()[0]["bonus_cooldown"] // 3600
        bot.edit_message_text(f"<b>⏱ Изменение времени бонуса</b>\n\n"
                            f"Текущее значение: <code>{current}</code> часов\n"
                            f"Введите новое время бонуса (в часах):", 
                            user_id, message_id, parse_mode="HTML")
    
    elif call.data == "admin_change_referral":
        user_states.upsert({"id": user_id, "state": "change_referral"}, Query().id == user_id)
        current = settings.all()[0]["referral_reward"]
        bot.edit_message_text(f"<b>🤝 Изменение реферальной награды</b>\n\n"
                            f"Текущее значение: <code>{current}</code> монет\n"
                            f"Введите новое количество монет за реферала:", 
                            user_id, message_id, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.chat.id in ADMIN_IDS and user_states.get(Query().id == message.chat.id))
def handle_admin_states(message):
    user_id = message.chat.id
    state_data = user_states.get(Query().id == user_id)
    state = state_data.get("state")
    
    if message.text and message.text.strip() == "/cancel":
        user_states.remove(Query().id == user_id)
        send_message(user_id, "❌ Действие отменено.", create_admin_keyboard())
        return
    
    if state == "awaiting_broadcast":
        broadcast_text = message.text or (message.caption if message.content_type != 'text' else "")
        if not broadcast_text:
            send_message(user_id, "❌ Сообщение пустое!")
            return
        
        # Используем простой ID для callback
        broadcast_id = str(hash(broadcast_text) % 1000000).replace('-', '')
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Начать рассылку", callback_data=f"confirm_broadcast_{broadcast_id}"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="admin_back")
        )
        
        user_states.update({
            "state": "confirm_broadcast", 
            "broadcast_text": broadcast_text,
            "broadcast_id": broadcast_id
        }, Query().id == user_id)
        
        send_message(user_id, f"<b>📢 Подтверждение рассылки</b>\n\n"
                            f"Сообщение:\n"
                            f"<code>{broadcast_text[:200]}...</code>\n\n"
                            f"Кол-во получателей: <code>{len(users.all())}</code>\n\n"
                            f"Начать рассылку?", reply_markup=markup)
    
    elif state == "add_promo_name":
        promo_name = message.text.strip()
        if promocodes.get(Query().name == promo_name):
            send_message(user_id, f"<b>❌ Промокод {promo_name} уже существует</b>")
            return
        user_states.update({"state": "add_promo_activations", "promo_name": promo_name}, Query().id == user_id)
        send_message(user_id, f"<b>Сколько активаций для {promo_name}?</b>")
    
    elif state == "add_promo_activations":
        if not message.text.isdigit() or int(message.text) <= 0:
            send_message(user_id, "<b>❌ Введите корректное число!</b>")
            return
        user_states.update({"state": "add_promo_reward", "activations": int(message.text)}, Query().id == user_id)
        send_message(user_id, f"<b>Сколько монет давать за {state_data['promo_name']}?</b>")
    
    elif state == "add_promo_reward":
        if not message.text.isdigit() or int(message.text) <= 0:
            send_message(user_id, "<b>❌ Введите корректное число!</b>")
            return
        promocodes.insert({
            "name": state_data["promo_name"], 
            "activations": state_data["activations"], 
            "reward": int(message.text)
        })
        user_states.remove(Query().id == user_id)
        send_message(user_id, f"<b>✅ Промокод {state_data['promo_name']} создан!</b>\n\n"
                            f"• Активаций: {state_data['activations']}\n"
                            f"• Награда: {message.text} монет", 
                            create_admin_keyboard())
    
    elif state == "change_bonus":
        if not message.text.isdigit() or int(message.text) < 0:
            send_message(user_id, "<b>❌ Введите корректное число!</b>")
            return
        settings.update({"bonus_amount": int(message.text)}, doc_ids=[1])
        user_states.remove(Query().id == user_id)
        send_message(user_id, f"<b>✅ Бонус изменен на {message.text} монет</b>", create_admin_keyboard())
    
    elif state == "change_cooldown":
        if not message.text.isdigit() or int(message.text) < 0:
            send_message(user_id, "<b>❌ Введите корректное число!</b>")
            return
        settings.update({"bonus_cooldown": int(message.text) * 3600}, doc_ids=[1])
        user_states.remove(Query().id == user_id)
        send_message(user_id, f"<b>✅ Кулдаун бонуса изменен на {message.text} часов</b>", create_admin_keyboard())
    
    elif state == "change_referral":
        if not message.text.isdigit() or int(message.text) < 0:
            send_message(user_id, "<b>❌ Введите корректное число!</b>")
            return
        settings.update({"referral_reward": int(message.text)}, doc_ids=[1])
        user_states.remove(Query().id == user_id)
        send_message(user_id, f"<b>✅ Реферальная награда изменена на {message.text} монет</b>", create_admin_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_broadcast_"))
def handle_confirm_broadcast(call):
    user_id = call.message.chat.id
    state_data = user_states.get(Query().id == user_id)
    
    if not state_data or state_data.get("state") != "confirm_broadcast":
        bot.answer_callback_query(call.id, "❌ Рассылка уже обработана или отменена")
        return
    
    broadcast_text = state_data.get("broadcast_text", "")
    broadcast_id = call.data.replace("confirm_broadcast_", "")
    
    # Проверка ID для безопасности
    if state_data.get("broadcast_id") != broadcast_id:
        bot.answer_callback_query(call.id, "❌ Ошибка проверки рассылки")
        return
    
    all_users = users.all()
    total_users = len(all_users)
    
    if total_users == 0:
        bot.answer_callback_query(call.id, "❌ Нет пользователей для рассылки")
        return
    
    # Обновляем статус рассылки
    bot.edit_message_text(f"<b>📢 Начинаю рассылку...</b>\n\n"
                         f"Всего получателей: <code>{total_users}</code>\n"
                         f"Отправлено: <code>0/{total_users}</code>\n"
                         f"Успешно: <code>0</code>\n"
                         f"Ошибок: <code>0</code>", 
                         user_id, call.message.message_id, parse_mode="HTML")
    
    success = 0
    errors = 0
    blocked = 0
    
    for i, user in enumerate(all_users, 1):
        try:
            bot.send_message(user["id"], broadcast_text, parse_mode="HTML")
            success += 1
        except telebot.apihelper.ApiTelegramException as e:
            error_msg = str(e).lower()
            if "blocked" in error_msg or "chat not found" in error_msg or "user is deactivated" in error_msg:
                blocked += 1
            else:
                errors += 1
                print(f"Ошибка отправки {user['id']}: {e}")
        except Exception as e:
            errors += 1
            print(f"Ошибка отправки {user['id']}: {e}")
        
        # Обновляем прогресс каждые 10 отправок или в конце
        if i % 10 == 0 or i == total_users:
            try:
                bot.edit_message_text(f"<b>📢 Рассылка в процессе...</b>\n\n"
                                     f"Всего получателей: <code>{total_users}</code>\n"
                                     f"Отправлено: <code>{i}/{total_users}</code>\n"
                                     f"Успешно: <code>{success}</code>\n"
                                     f"Заблокировали: <code>{blocked}</code>\n"
                                     f"Ошибок: <code>{errors}</code>", 
                                     user_id, call.message.message_id, parse_mode="HTML")
            except:
                pass
        
        # Небольшая задержка, чтобы не превысить лимиты Telegram
        if i % 20 == 0:
            time.sleep(0.5)
    
    # Завершаем рассылку
    user_states.remove(Query().id == user_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_back"))
    
    final_text = f"<b>✅ Рассылка завершена!</b>\n\n" \
                 f"<b>Итоги:</b>\n" \
                 f"• Всего получателей: <code>{total_users}</code>\n" \
                 f"• Успешно отправлено: <code>{success}</code>\n" \
                 f"• Заблокировали бота: <code>{blocked}</code>\n" \
                 f"• Ошибок отправки: <code>{errors}</code>\n\n" \
                 f"<i>Рассылку получили {success} пользователей</i>"
    
    try:
        bot.edit_message_text(final_text, user_id, call.message.message_id, 
                            parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при завершении рассылки: {e}")
        send_message(user_id, final_text, reply_markup=markup)

def run_bot():
    while True:
        try:
            print("✅ Бот запущен...")
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
