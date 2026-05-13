import telebot
from telebot import types

# ⚠️ ÜNS BERIŇ: 'SIZIN_BOT_TOKENINIZ' ýerine BotFather-dan alan kodyňyzy goýuň
API_TOKEN = '8654803333:AAF1FNhsGXrf_IYj-ekAU0uujQyuc7vtl1w'
WEB_APP_URL = 'https://google.com' 
ADMIN_ID = 6027574184

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url=WEB_APP_URL)
    btn = types.InlineKeyboardButton(text="🚀 Начать зарабатывать", web_app=web_app)
    markup.add(btn)
    
    bot.send_message(message.chat.id, 
                     f"Salam {message.from_user.first_name}!\n\n"
                     "Mahabat görüp TON gazanmak üçin aşakdaky düwmä basyň.", 
                     reply_markup=markup)

    if message.from_user.id != ADMIN_ID:
        bot.send_message(ADMIN_ID, f"🔔 Täze ulanyjy: {message.from_user.first_name}")

if __name__ == "__main__":
    bot.polling(none_stop=True)
