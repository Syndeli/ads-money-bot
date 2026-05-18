import telebot
from telebot import types
import sqlite3
import os
from flask import Flask, request
from threading import Thread

TOKEN = "8654803333:AAF1FNhsGXrf_IYj-ekAU0uujQyuc7vtl1w"
bot = telebot.TeleBot(TOKEN)

# 1. RENDER ÖÇMEZLIGI ÜÇIN FLASK WEB PORTY WE ADSGRAM WEBHOOK
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is running perfectly!"

# Adsgram-dan gelýän awtomatiki habarlary kabul edýän ýer (Postback)
@app.route('/adsgram_webhook', methods=['GET'])
def adsgram_webhook():
    user_id = request.args.get('user_id')  # Wideo gören ulanyjynyň Telegram ID-si
    status = request.args.get('status')   # Reklamanyň gutaranlyk statusy
    
    # Eger wideo doly görlen bolsa we baýrak statusy gelse
    if status == 'reward' and user_id:
        try:
            conn = sqlite3.connect("bot_users.db", check_same_thread=False)
            cursor = conn.cursor()
            
            # Her wideo üçin ulanyja 0.02 TON berýäris (islegiňize görä üýtgedip bilersiňiz)
            reward_amount = 0.02
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward_amount, user_id))
            conn.commit()
            conn.close()
            
            # Ulanyja göni bota gutlag hatyny ugratmak
            success_text = f"🎉 *Gözüňiz aýdyň!* Wideo reklamany ahyryna çenli göreniňiz üçin hasabyňyza `+{reward_amount} TON` goşuldy!"
            bot.send_message(user_id, success_text, parse_mode="Markdown")
            
            return "OK", 200
        except Exception as e:
            print("Postback-de ýalňyşlyk döredi:", e)
            return "Database Error", 500
            
    return "Invalid Request", 400

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

# ADSGRAM PLATFORMASYNDAN ALAN TÄZE BLOCK ID KODUŇYZ
ADSGRAM_BLOCK_ID = "bot-30505"

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
        'earn_msg': "🔥 *Click the button below to watch a short video ad and instantly earn TON!*",
        'btn_watch_ad': "📺 Watch Ad & Earn TON"
    },
    'ru': {
        'welcome': "✨ *Добро пожаловать в FastAdsMoney!* \n\nЗарабатывайте TON за выполнение заданий или приглашение друзей.",
        'btn_earn': "🚀 Начать зарабатывать",
        'btn_ref': "👥 Пригласить друзей",
        'btn_balance': "💰 Мой баланс",
        'btn_lang': "🌐 Сменить язык",
        'balance_msg': "💵 *Ваш баланс:* \n\n💰 `{} TON`",
        'ref_msg': "👥 *Реферальная программа*\n\nПоделись ссылкой и получай *0.10 TON* за каждого приглашенного друга!\n\n🔗 Твоя ссылка: https://t.me/{}?start={}",
        'earn_msg': "🔥 *Нажмите на кнопку ниже, чтобы посмотреть короткую видеорекламу и мгновенно заработать TON!*",
        'btn_watch_ad': "📺 Посмотреть видео и заработать"
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
        markup = types.InlineKeyboardMarkup()
        # Adsgram-yň Telegram Mini App-da däl-de, adaty botuň içinde göni açylmagy üçin ýörite url çykgydy
        adsgram_url = f"https://render.adsgram.ai/wvideo?bg=1&blockId={ADSGRAM_BLOCK_ID}&subid={user_id}"
        
        btn_ad = types.InlineKeyboardButton(text=TEXTS[lang]['btn_watch_ad'], url=adsgram_url)
        markup.add(btn_ad)
        
        bot.send_message(user_id, TEXTS[lang]['earn_msg'], parse_mode="Markdown", reply_markup=markup)
        
    elif message.text == TEXTS[lang]['btn_balance']:
        bot.send_message(user_id, TEXTS[lang]['balance_msg'].format(balance), parse_mode="Markdown")
    elif message.text == TEXTS[lang]['btn_ref']:
        bot.send_message(user_id, TEXTS[lang]['ref_msg'].format(bot_username, user_id), parse_mode="Markdown")
    elif message.text == TEXTS[lang]['btn_lang']:
        bot.send_message(user_id, "Select language / Выберите язык:", reply_markup=lang_keyboard())

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
