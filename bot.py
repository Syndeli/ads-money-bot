import telebot
from telebot import types
import sqlite3
import os
from flask import Flask
from threading import Thread

TOKEN = "7880504781:AAElG-W_GZ62_NlT5X70WnCgL8-8x3-R0X8"
bot = telebot.TeleBot(TOKEN)

# 1. RENDER ÖÇMEZLIGI ÜÇIN FLASK WEB PORTY
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. BOTUŇ BAŞYNDAKY OWADAN SURAT
START_PHOTO = "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?q=80&w=1000&auto=format&fit=crop"

# 3. MAGLUMAT BINASY (Diller, Ballar we Çakylyklar)
def init_db():
    conn = sqlite3.connect("bot_users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT,
            balance REAL DEFAULT 0.0,
            referred_by INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 4. IŇLIS WE RUS DILLERINDE TEKSTLER
TEXTS = {
    'en': {
        'welcome': "✨ *Welcome to FastAdsMoney!* \n\nEarn TON crypto by completing easy tasks or inviting friends.",
        'btn_earn': "🚀 Start Earning",
        'btn_ref': "👥 Invite Friends",
        'btn_balance': "💰 Balance",
        'btn_lang': "🌐 Language",
        'balance_msg': "💵 *Your Balance:* \n\n💰 `{} TON`",
        'ref_msg': "👥 *Referral Program*\n\nShare your link and earn *0.10 TON* for every friend you invite!\n\n🔗 Your link: https://t.me/{}?start={}",
        'earn_msg': "🔥 *Choose Earning Method:*\n\n1️⃣ [CPALead Tasks](https://www.cpalead.com) — Fast ads & shortlinks\n2️⃣ [Monlix Offers](https://monlix.com) — High paying apps & surveys\n\n*(Note: Complete tasks and balance updates automatically!)*"
    },
    'ru': {
        'welcome': "✨ *Добро пожаловать в FastAdsMoney!* \n\nЗарабатывайте TON за выполнение заданий или приглашение друзей.",
        'btn_earn': "🚀 Начать зарабатывать",
        'btn_ref': "👥 Пригласить друзей",
        'btn_balance': "💰 Мой баланс",
        'btn_lang': "🌐 Сменить язык",
        'balance_msg': "💵 *Ваш баланс:* \n\n💰 `{} TON`",
        'ref_msg': "👥 *Реферальная программа*\n\nПоделись ссылкой и получай *0.10 TON* за каждого приглашенного друга!\n\n🔗 Твоя ссылка: https://t.me/{}?start={}",
        'earn_msg': "🔥 *Выберите способ заработка:*\n\n1️⃣ [CPALead Задания](https://www.cpalead.com) — Быстрые объявления\n2️⃣ [Monlix Офферы](https://monlix.com) — Высокооплачиваемые опросы\n\n*(Задания обновляются автоматически!)*"
    }
}

def lang_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"))
    markup.add(types.InlineKeyboardButton("Русский 🇷🇺", callback_data="set_lang_ru"))
    return markup

def main_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(TEXTS[lang]['btn_earn'])
    markup.row(TEXTS[lang]['btn_balance'], TEXTS[lang]['btn_ref'])
    markup.row(TEXTS[lang]['btn_lang'])
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    conn = sqlite3.connect("bot_users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        # Referal barlagy (biri çagyrsa bonus bermek)
        ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        cursor.execute("INSERT OR REPLACE INTO users (user_id, lang, referred_by) VALUES (?, ?, ?)", (user_id, 'en', ref_id))
        
        if ref_id != 0 and ref_id != user_id:
            cursor.execute("UPDATE users SET balance = balance + 0.10 WHERE user_id = ?", (ref_id,))
            try: 
                bot.send_message(ref_id, "🎉 Someone joined using your link! You received +0.10 TON.")
            except: 
                pass
            
        conn.commit()
        bot.send_message(user_id, "Select your language / Выберите язык:", reply_markup=lang_keyboard())
    else:
        lang = row[0]
        bot.send_photo(user_id, START_PHOTO, caption=TEXTS[lang]['welcome'], reply_markup=main_keyboard(lang), parse_mode="Markdown")
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_lang_"))
def callback_lang(call):
    user_id = call.from_user.id
    lang = call.data.split("_")[2]
    
    conn = sqlite3.connect("bot_users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()
    
    try: 
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: 
        pass
    bot.send_photo(user_id, START_PHOTO, caption=TEXTS[lang]['welcome'], reply_markup=main_keyboard(lang), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT lang, balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        bot.send_message(user_id, "Please run /start", reply_markup=lang_keyboard())
        conn.close()
        return
        
    lang, balance = row
    conn.close()

    bot_username = bot.get_me().username

    if message.text == TEXTS[lang]['btn_earn']:
        bot.send_message(user_id, TEXTS[lang]['earn_msg'], parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text == TEXTS[lang]['btn_balance']:
        bot.send_message(user_id, TEXTS[lang]['balance_msg'].format(balance), parse_mode="Markdown")
    elif message.text == TEXTS[lang]['btn_ref']:
        bot.send_message(user_id, TEXTS[lang]['ref_msg'].format(bot_username, user_id), parse_mode="Markdown")
    elif message.text == TEXTS[lang]['btn_lang']:
        bot.send_message(user_id, "Select language / Выберите язык:", reply_markup=lang_keyboard())

if __name__ == "__main__":
    # Flask portuny we Boty arka fonda bir wagtda işletmek
    Thread(target=run_flask).start()
    bot.infinity_polling()
