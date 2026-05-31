"""
FastAdsMoney Telegram Bot
Professional Version with Monetag & Channel/Bot Promotion System
"""

import telebot
from telebot import types
import sqlite3
import os
import logging
from flask import Flask, request, jsonify
from threading import Thread

# ============================================================
#  CONFIGURATION (Render Nastroykasyndan alar)
# ============================================================
TOKEN        = os.environ.get("BOT_TOKEN")
ADMIN_ID     = int(os.environ.get("ADMIN_ID", "0"))
BOT_USERNAME = "FastAdsMoneyBot"

MONETAG_LINK    = "https://omg10.com/4/11082821"
REWARD_PER_AD   = 0.0005
REFERRAL_REWARD = 0.005
MIN_WITHDRAW    = 1.5
PROMOTE_PRICE   = 0.5

START_PHOTO = "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?q=80&w=1000&auto=format&fit=crop"

# ============================================================
#  LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================
#  BOT & FLASK
# ============================================================
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ============================================================
#  DATABASE
# ============================================================
DB_PATH = "bot_users.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            lang         TEXT    DEFAULT 'en',
            balance      REAL    DEFAULT 0.0,
            referred_by  INTEGER DEFAULT 0,
            state        TEXT    DEFAULT 'NONE',
            total_earned REAL    DEFAULT 0.0,
            ads_watched  INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promotions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            link        TEXT,
            description TEXT,
            status      TEXT    DEFAULT 'pending',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized ✅")

init_db()
# ============================================================
#  TEXTS  (EN / RU)
# ============================================================
TEXTS = {
    'en': {
        'welcome'       : "✨ *Welcome to FastAdsMoney!*\n\nEarn real TON crypto by watching short ads or inviting friends.",
        'btn_earn'      : "🚀 Start Earning",
        'btn_balance'   : "💰 Balance",
        'btn_ref'       : "👥 Invite Friends",
        'btn_withdraw'  : "💳 Withdraw TON",
        'btn_lang'      : "🌐 Language",
        'btn_promote'   : "📢 Promote My Channel/Bot",
        'btn_stats'     : "📊 My Stats",
        'balance_msg'   : "💵 *Your Balance*\n\n💰 `{:.4f} TON`\n📺 Ads watched: *{}*\n🏆 Total earned: `{:.4f} TON`",
        'earn_msg'      : "🔥 *Watch a short ad and earn {:.4f} TON instantly!*\n\nClick the button below to open the ad player.",
        'btn_watch_ad'  : "📺 Watch Ad & Earn TON",
        'ref_msg'       : "👥 *Referral Program*\n\nInvite friends and earn *{} TON* per person!\n\n🔗 Your link:\n`https://t.me/{}?start={}`",
        'withdraw_low'  : "❌ Minimum withdrawal is *{} TON* (~$3).\n\n💡 Keep watching ads to reach the limit!",
        'withdraw_req'  : "📝 Send your *TON wallet address* (e.g. Tonkeeper) to withdraw `{:.4f} TON`:",
        'withdraw_sent' : "⏳ Your withdrawal request has been sent to admin!\nPlease wait for confirmation.",
        'admin_withdraw': "🚨 *New Withdrawal Request!*\n\n👤 User: `{}`\n💰 Amount: `{:.4f} TON`\n👛 Wallet: `{}`",
        'promote_info'  : "📢 *Promote Your Channel or Bot*\n\nYour channel/bot will be shown to all our users!\n\n💰 Price: *{} TON* (deducted from balance)\n\nDo you want to continue?",
        'promote_low'   : "❌ You need at least *{} TON* to promote.\n\n💡 Watch more ads to earn enough!",
        'promote_link'  : "🔗 Send your *channel or bot link*\n(e.g. @mychannel or https://t.me/mybot):",
        'promote_desc'  : "📝 Send a *short description* of your channel/bot (max 200 chars):",
        'promote_sent'  : "✅ Your promotion request has been sent!\n\nAdmin will review and publish it soon.",
        'admin_promote' : "📢 *New Promotion Request!*\n\n👤 User: `{}`\n🔗 Link: {}\n📝 Desc: {}\n\n✅ /approve_{}\n❌ /reject_{}",
        'stats_msg'     : "📊 *Your Statistics*\n\n👤 User ID: `{}`\n💰 Balance: `{:.4f} TON`\n📺 Ads watched: *{}*\n🏆 Total earned: `{:.4f} TON`\n👥 Referrals: *{}*",
        'ad_reward'     : "🎉 *Congrats!* You earned `+{} TON` for watching an ad!",
        'ref_bonus'     : "🎉 Someone joined using your link! You earned `+{} TON`!",
        'cancel'        : "❌ Cancelled.",
        'btn_cancel'    : "❌ Cancel",
        'btn_confirm'   : "✅ Confirm",
    },
    'ru': {
        'welcome'       : "✨ *Добро пожаловать в FastAdsMoney!*\n\nЗарабатывайте реальные TON, просматривая рекламу или приглашая друзей.",
        'btn_earn'      : "🚀 Начать зарабатывать",
        'btn_balance'   : "💰 Мой баланс",
        'btn_ref'       : "👥 Пригласить друзей",
        'btn_withdraw'  : "💳 Вывести TON",
        'btn_lang'      : "🌐 Сменить язык",
        'btn_promote'   : "📢 Реклама моего канала/бота",
        'btn_stats'     : "📊 Моя статистика",
        'balance_msg'   : "💵 *Ваш баланс*\n\n💰 `{:.4f} TON`\n📺 Просмотров рекламы: *{}*\n🏆 Всего заработано: `{:.4f} TON`",
        'earn_msg'      : "🔥 *Посмотрите короткую рекламу и получите {:.4f} TON мгновенно!*\n\nНажмите кнопку ниже для просмотра.",
        'btn_watch_ad'  : "📺 Смотреть рекламу и зарабатывать",
        'ref_msg'       : "👥 *Реферальная программа*\n\nПриглашай друзей и получай *{} TON* за каждого!\n\n🔗 Твоя ссылка:\n`https://t.me/{}?start={}`",
        'withdraw_low'  : "❌ Минимальная сумма вывода — *{} TON* (~$3).\n\n💡 Смотрите больше рекламы!",
        'withdraw_req'  : "📝 Отправьте адрес вашего *TON кошелька* (например, Tonkeeper) для вывода `{:.4f} TON`:",
        'withdraw_sent' : "⏳ Ваша заявка отправлена администратору!\nОжидайте подтверждения.",
        'admin_withdraw': "🚨 *Новая заявка на вывод!*\n\n👤 Юзер: `{}`\n💰 Сумма: `{:.4f} TON`\n👛 Кошелёк: `{}`",
        'promote_info'  : "📢 *Реклама вашего канала или бота*\n\nВаш канал/бот увидят все наши пользователи!\n\n💰 Стоимость: *{} TON* (спишется с баланса)\n\nПродолжить?",
        'promote_low'   : "❌ Для рекламы нужно минимум *{} TON*.\n\n💡 Смотрите больше рекламы!",
        'promote_link'  : "🔗 Отправьте ссылку на *канал или бот*\n(например @mychannel или https://t.me/mybot):",
        'promote_desc'  : "📝 Отправьте *краткое описание* канала/бота (до 200 символов):",
        'promote_sent'  : "✅ Ваша заявка на рекламу отправлена!\n\nАдмин рассмотрит её в ближайшее время.",
        'admin_promote' : "📢 *Новая заявка на рекламу!*\n\n👤 Юзер: `{}`\n🔗 Ссылка: {}\n📝 Описание: {}\n\n✅ /approve_{}\n❌ /reject_{}",
        'stats_msg'     : "📊 *Ваша статистика*\n\n👤 ID: `{}`\n💰 Баланс: `{:.4f} TON`\n📺 Просмотров: *{}*\n🏆 Заработано: `{:.4f} TON`\n👥 Рефералов: *{}*",
        'ad_reward'     : "🎉 *Отлично!* На ваш счёт зачислено `+{} TON` за просмотр рекламы!",
        'ref_bonus'     : "🎉 По вашей ссылке зарегистрировался новый пользователь! +{} TON!",
        'cancel'        : "❌ Отменено.",
        'btn_cancel'    : "❌ Отмена",
        'btn_confirm'   : "✅ Подтвердить",
    }
}

# ============================================================
#  HELPERS
# ============================================================
def get_user(user_id):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT lang, balance, state, total_earned, ads_watched FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def set_state(user_id, state):
    conn = get_conn()
    conn.execute("UPDATE users SET state=? WHERE user_id=?", (state, user_id))
    conn.commit()
    conn.close()

def count_referrals(user_id):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def main_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(TEXTS[lang]['btn_earn'])
    markup.row(TEXTS[lang]['btn_balance'], TEXTS[lang]['btn_ref'])
    markup.row(TEXTS[lang]['btn_withdraw'], TEXTS[lang]['btn_promote'])
    markup.row(TEXTS[lang]['btn_stats'],   TEXTS[lang]['btn_lang'])
    return markup

def lang_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"))
    markup.add(types.InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"))
    return markup

def confirm_keyboard(lang, action):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(TEXTS[lang]['btn_confirm'], callback_data=f"confirm_{action}"),
        types.InlineKeyboardButton(TEXTS[lang]['btn_cancel'],  callback_data="cancel_action")
    )
    return markup
    # ============================================================
#  FLASK ROUTES
# ============================================================
@app.route('/')
def home():
    return "FastAdsMoney Bot is running! ✅"

@app.route('/index.html')
def serve_index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return f"HTML File Error: {e}", 500

@app.route('/monetag_reward', methods=['GET', 'POST'])
def monetag_reward():
    user_id = request.args.get('user_id') or (request.json or {}).get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    try:
        conn = get_conn()
        conn.execute(
            "UPDATE users SET balance=balance+?, total_earned=total_earned+?, ads_watched=ads_watched+1 WHERE user_id=?",
            (REWARD_PER_AD, REWARD_PER_AD, user_id)
        )
        conn.commit()
        conn.close()
        row = get_user(user_id)
        lang = row[0] if row else 'en'
        bot.send_message(user_id, TEXTS[lang]['ad_reward'].format(REWARD_PER_AD), parse_mode="Markdown")
        logger.info(f"Reward sent to user {user_id}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Monetag reward error: {e}")
        return jsonify({"error": str(e)}), 500

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ============================================================
#  /start
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    args    = message.text.split()
    conn    = get_conn()
    cur     = conn.cursor()
    cur.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if row is None:
        ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        cur.execute(
            "INSERT INTO users (user_id, lang, referred_by, state) VALUES (?,?,?,'NONE')",
            (user_id, 'en', ref_id)
        )
        if ref_id and ref_id != user_id:
            cur.execute(
                "UPDATE users SET balance=balance+?, total_earned=total_earned+ WHERE user_id=?",
                (REFERRAL_REWARD, REFERRAL_REWARD, ref_id)
            )
            try:
                bot.send_message(ref_id, TEXTS['en']['ref_bonus'].format(REFERRAL_REWARD), parse_mode="Markdown")
            except Exception:
                pass
        conn.commit()
        conn.close()
        bot.send_message(user_id, "🌐 Select your language / Выберите язык:", reply_markup=lang_keyboard())
    else:
        lang = row[0]
        conn.execute("UPDATE users SET state='NONE' WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        bot.send_photo(user_id, START_PHOTO,
                       caption=TEXTS[lang]['welcome'],
                       reply_markup=main_keyboard(lang),
                       parse_mode="Markdown")

# ============================================================
#  ADMIN COMMANDS
# ============================================================
@bot.message_handler(commands=['stats'])
def cmd_admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM promotions WHERE status='pending'")
    pending = cur.fetchone()[0]
    cur.execute("SELECT SUM(ads_watched) FROM users")
    total_ads = cur.fetchone()[0] or 0
    conn.close()
    bot.send_message(ADMIN_ID,
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total users: *{total_users}*\n"
        f"📺 Total ads watched: *{total_ads}*\n"
        f"📢 Pending promotions: *{pending}*",
        parse_mode="Markdown")

@bot.message_handler(regexp=r'^/(approve|reject)_\d+$')
def cmd_approve_reject(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts    = message.text.lstrip('/').split('_', 1)
    action   = parts[0]
    promo_id = int(parts[1])

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT user_id, link, description FROM promotions WHERE id=?", (promo_id,))
    row = cur.fetchone()
    if not row:
        bot.send_message(ADMIN_ID, "❌ Promotion not found.")
        conn.close()
        return

    uid, link, desc = row
    if action == 'approve':
        conn.execute("UPDATE promotions SET status='approved' WHERE id=?", (promo_id,))
        conn.commit()
        users = conn.execute("SELECT user_id FROM users").fetchall()
        conn.close()
        for (u,) in users:
            try:
                bot.send_message(u, f"📢 *Sponsored*\n\n{desc}\n\n🔗 {link}", parse_mode="Markdown")
            except Exception:
                pass
        bot.send_message(ADMIN_ID, f"✅ Promotion #{promo_id} sent to all users!")
        try:
            bot.send_message(uid, "✅ Your promotion has been approved and sent to all users!")
        except Exception:
            pass
    else:
        conn.execute("UPDATE promotions SET status='rejected' WHERE id=?", (promo_id,))
        conn.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (PROMOTE_PRICE, uid))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, f"❌ Promotion #{promo_id} rejected. {PROMOTE_PRICE} TON refunded.")
        try:
            bot.send_message(uid, f"❌ Your promotion was rejected. *{PROMOTE_PRICE} TON* refunded.", parse_mode="Markdown")
        except Exception:
            pass

# ============================================================
#  CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    user_id = call.from_user.id
    data    = call.data

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        conn = get_conn()
        conn.execute("UPDATE users SET lang=?, state='NONE' WHERE user_id=?", (lang, user_id))
        conn.commit()
        conn.close()
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(user_id, START_PHOTO,
                       caption=TEXTS[lang]['welcome'],
                       reply_markup=main_keyboard(lang),
                       parse_mode="Markdown")

    elif data == "confirm_promote":
        row = get_user(user_id)
        if not row: return
        lang, balance, _, _, _ = row
        if balance < PROMOTE_PRICE:
            bot.send_message(user_id, TEXTS[lang]['promote_low'].format(PROMOTE_PRICE), parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            return
        conn = get_conn()
        conn.execute("UPDATE users SET balance=balance-?, state='PROMO_LINK' WHERE user_id=?", (PROMOTE_PRICE, user_id))
        conn.commit()
        conn.close()
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(user_id, TEXTS[lang]['promote_link'], parse_mode="Markdown")

    elif data == "cancel_action":
        row  = get_user(user_id)
        lang = row[0] if row else 'en'
        set_state(user_id, 'NONE')
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(user_id, TEXTS[lang]['cancel'])

    bot.answer_callback_query(call.id)

# ============================================================
#  MESSAGE HANDLER
# ============================================================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.from_user.id
    row = get_user(user_id)
    if not row:
        bot.send_message(user_id, "Please run /start")
        return

    lang, balance, state, total_earned, ads_watched = row

    if state == 'WAITING_WALLET':
        wallet = message.text.strip()
        conn = get_conn()
        conn.execute("UPDATE users SET balance=0.0, state='NONE' WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID,
            TEXTS[lang]['admin_withdraw'].format(user_id, balance, wallet),
            parse_mode="Markdown")
        bot.send_message(user_id, TEXTS[lang]['withdraw_sent'], parse_mode="Markdown")
        return

    if state == 'PROMO_LINK':
        conn = get_conn()
        conn.execute("UPDATE users SET state='PROMO_DESC' WHERE user_id=?", (user_id,))
        conn.execute("INSERT INTO promotions (user_id, link) VALUES (?,?)", (user_id, message.text.strip()))
        conn.commit()
        conn.close()
        bot.send_message(user_id, TEXTS[lang]['promote_link'], parse_mode="Markdown")
        return

    if state == 'PROMO_DESC':
        desc = message.text.strip()[:200]
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT id, link FROM promotions WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
        promo = cur.fetchone()
        if promo:
            conn.execute("UPDATE promotions SET description=? WHERE id=?", (desc, promo[0]))
        conn.execute("UPDATE users SET state='NONE' WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        bot.send_message(user_id, TEXTS[lang]['promote_sent'], parse_mode="Markdown",
                         reply_markup=main_keyboard(lang))
        if promo:
            bot.send_message(ADMIN_ID,
                TEXTS[lang]['admin_promote'].format(user_id, promo[1], desc, promo[0], promo[0]),
                parse_mode="Markdown")
        return

    txt = message.text

    if txt == TEXTS[lang]['btn_earn']:
        webapp = types.WebAppInfo(url=f"https://fastadsmoney.onrender.com/index.html?user_id={user_id}")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text=TEXTS[lang]['btn_watch_ad'], web_app=webapp))
        bot.send_message(user_id,
            TEXTS[lang]['earn_msg'].format(REWARD_PER_AD),
            parse_mode="Markdown",
            reply_markup=markup)

    elif txt == TEXTS[lang]['btn_balance']:
        bot.send_message(user_id,
            TEXTS[lang]['balance_msg'].format(balance, ads_watched, total_earned),
            parse_mode="Markdown")

    elif txt == TEXTS[lang]['btn_ref']:
        bot.send_message(user_id,
            TEXTS[lang]['ref_msg'].format(REFERRAL_REWARD, BOT_USERNAME, user_id),
            parse_mode="Markdown")

    elif txt == TEXTS[lang]['btn_withdraw']:
        if balance < MIN_WITHDRAW:
            bot.send_message(user_id, TEXTS[lang]['withdraw_low'].format(MIN_WITHDRAW), parse_mode="Markdown")
        else:
            set_state(user_id, 'WAITING_WALLET')
            bot.send_message(user_id, TEXTS[lang]['withdraw_req'].format(balance), parse_mode="Markdown")

    elif txt == TEXTS[lang]['btn_promote']:
        bot.send_message(user_id, TEXTS[lang]['promote_info'].format(PROMOTE_PRICE),
                         reply_markup=confirm_keyboard(lang, "promote"), parse_mode="Markdown")

    elif txt == TEXTS[lang]['btn_stats']:
        ref_count = count_referrals(user_id)
        bot.send_message(user_id, TEXTS[lang]['stats_msg'].format(user_id, balance, ads_watched, total_earned, ref_count),
                         parse_mode="Markdown")

    elif txt == TEXTS[lang]['btn_lang']:
        bot.send_message(user_id, "🌐 Select language / Выберите язык:", reply_markup=lang_keyboard())

# ============================================================
#  START SERVER & BOT
# ============================================================
if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    logger.info("Bot polling başlaýar... 🚀")
    bot.infinity_polling()
    
