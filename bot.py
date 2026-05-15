import telebot
from telebot import types
import sqlite3

TOKEN = "7880504781:AAElG-W_GZ62_NlT5X70WnCgL8-8x3-R0X8" # Siziň bot tokeniňiz
bot = telebot.TeleBot(TOKEN)

# Maglumat binasyny gurnamak (Ulanyjy dilleri we ballary üçin)
def init_db():
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT,
            balance REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Tekstler (Iňlis we Rus)
TEXTS = {
    'en': {
        'welcome': "Welcome to FastAdsMoney! Select an option below to start earning TON.",
        'btn_earn': "🚀 Start Earning",
        'btn_balance': "💰 My Balance",
        'btn_lang': "🌐 Change Language",
        'balance_msg': "Your current balance: *{} TON*",
        'earn_msg': "Complete high-paying tasks, surveys, and download apps to earn TON!\n\n👉 [Click Here to Start Tasks](YOUR_MONLIX_LINK_HERE)"
    },
    'ru': {
        'welcome': "Добро пожаловать в FastAdsMoney! Выберите опцию ниже, чтобы начать зарабатывать TON.",
        'btn_earn': "🚀 Начать зарабатывать",
        'btn_balance': "💰 Мой баланс",
        'btn_lang': "🌐 Сменить язык",
        'balance_msg': "Ваш текущий баланс: *{} TON*",
        'earn_msg': "Выполняйте высокооплачиваемые задания, опросы и скачивайте приложения, чтобы заработать TON!\n\n👉 [Нажмите здесь, чтобы начать](YOUR_MONLIX_LINK_HERE)"
    }
}

# Dil saýlamak düwmeleri
def lang_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"))
    markup.add(types.InlineKeyboardButton("Русский 🇷🇺", callback_data="set_lang_ru"))
    return markup

# Esasy menýu düwmeleri
def main_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(TEXTS[lang]['btn_earn'])
    markup.row(TEXTS[lang]['btn_balance'], TEXTS[lang]['btn_lang'])
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        bot.send_message(user_id, "Please select your language / Пожалуйста, выберите язык:", reply_markup=lang_keyboard())
    else:
        lang = row[0]
        bot.send_message(user_id, TEXTS[lang]['welcome'], reply_markup=main_keyboard(lang))
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_lang_"))
def callback_lang(call):
    user_id = call.from_user.id
    lang = call.data.split("_")[2]
    
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, lang) VALUES (?, ?)", (user_id, lang))
    conn.commit()
    conn.close()
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(user_id, TEXTS[lang]['welcome'], reply_markup=main_keyboard(lang))

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT lang, balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        bot.send_message(user_id, "Please run /start", reply_markup=lang_keyboard())
        conn.close()
        return
        
    lang, balance = row
    conn.close()

    if message.text == TEXTS[lang]['btn_earn']:
        # Monlix salkynyny goşanyňyzda döräp biljek format
        user_link = f"https://monlix.com/your_id?uid={user_id}" # Muny soň anyklarys
        msg = TEXTS[lang]['earn_msg'].replace("YOUR_MONLIX_LINK_HERE", user_link)
        bot.send_message(user_id, msg, parse_mode="Markdown")
    elif message.text == TEXTS[lang]['btn_balance']:
        bot.send_message(user_id, TEXTS[lang]['balance_msg'].format(balance), parse_mode="Markdown")
    elif message.text == TEXTS[lang]['btn_lang']:
        bot.send_message(user_id, "Select language / Выберите язык:", reply_markup=lang_keyboard())

if __name__ == "__main__":
    bot.infinity_polling()
