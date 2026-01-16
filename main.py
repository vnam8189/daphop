import telebot
import requests
import time
import threading
import json
import os
import random
import string
from datetime import datetime, timedelta
from telebot import types
from flask import Flask

# ================= SERVER MỒI (RENDER) =================
app = Flask(__name__)
@app.route('/')
def home(): return "<h1>PREDICT VIP V4 - STATUS: ONLINE</h1>"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ================= CẤU HÌNH HỆ THỐNG =================
API_TOKEN = '8404770438:AAHNI8xRHFlWPVNF4gL2-CShnvqgQ_OXUEI'
ADMIN_ID = 7816353760 

BANK_API_URL = "https://spayment.net/msb-history?history=80002422042"
API_TX = "https://xd88-apsj.onrender.com/xd88/tx"
API_MD5 = "https://xd88-apsj.onrender.com/xd88/md5"
DB_FILE = 'users_db.json'
CODE_FILE = 'giftcodes.json'

bot = telebot.TeleBot(API_TOKEN)

# ================= QUẢN LÝ DỮ LIỆU =================
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                for uid in data:
                    if data[uid]['expire_date']:
                        data[uid]['expire_date'] = datetime.strptime(data[uid]['expire_date'], '%Y-%m-%d %H:%M:%S')
                return data
        except: return {}
    return {}

def save_data():
    data_to_save = {}
    for uid, info in users_db.items():
        data_to_save[uid] = info.copy()
        if info['expire_date']:
            data_to_save[uid]['expire_date'] = info['expire_date'].strftime('%Y-%m-%d %H:%M:%S')
    with open(DB_FILE, 'w') as f:
        json.dump(data_to_save, f, indent=4)

def load_codes():
    if os.path.exists(CODE_FILE):
        try:
            with open(CODE_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_codes(codes):
    with open(CODE_FILE, 'w') as f: json.dump(codes, f, indent=4)

users_db = load_data()
gift_codes = load_codes()

# ================= AUTO BANK MSB =================
def check_bank_auto():
    processed_txns = [] 
    while True:
        try:
            res = requests.get(BANK_API_URL, timeout=15).json()
            transactions = res if isinstance(res, list) else res.get('data', [])
            for tr in transactions:
                amount_str = str(tr.get('so_tien') or tr.get('amount', '0'))
                amount = int(''.join(filter(str.isdigit, amount_str)))
                content = str(tr.get('noi_dung') or tr.get('description', '')).upper()
                tid = str(tr.get('ma_gd') or tr.get('transactionId', ''))

                if amount > 0 and tid not in processed_txns:
                    if "NAP" in content:
                        try:
                            u_id = content.split("NAP")[1].strip().split()[0]
                            u_id = ''.join(filter(str.isdigit, u_id))
                            if u_id not in users_db: users_db[u_id] = {'expire_date': None, 'is_running': False}
                            days = 999 if amount >= 100000 else (15 if amount >= 50000 else (7 if amount >= 20000 else 0))
                            if days > 0:
                                now = datetime.now()
                                start = users_db[u_id]['expire_date'] if users_db[u_id]['expire_date'] and users_db[u_id]['expire_date'] > now else now
                                users_db[u_id]['expire_date'] = start + timedelta(days=days)
                                save_data()
                                processed_txns.append(tid)
                                bot.send_message(u_id, f"🌟 **NẠP VIP THÀNH CÔNG**\n+ {days} ngày VIP.")
                                bot.send_message(ADMIN_ID, f"💰 **BANK:** `{u_id}` +{amount}đ")
                        except: continue
        except: pass
        time.sleep(25)

# ================= MENU & START =================
def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🔴 SOI CẦU XÓC ĐĨA', '🛡️ SOI CẦU MD5')
    markup.add('👤 TÀI KHOẢN', '💳 NẠP VIP')
    markup.add('🎁 NHẬP CODE', '🛑 DỪNG TOOL')
    if int(user_id) == ADMIN_ID:
        markup.add('👑 QUẢN TRỊ')
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {'expire_date': None, 'is_running': False}
        save_data()
    
    welcome_text = (
        f"👋 **Chào mừng {message.from_user.first_name}!**\n"
        f"Hệ thống **PREDICT VIP AI** - Soi cầu đẳng cấp 🦅\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Nhấn **💳 NẠP VIP** hoặc **🎁 NHẬP CODE** để bắt đầu."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(uid), parse_mode="Markdown")

# ================= XỬ LÝ TIN NHẮN =================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = str(message.from_user.id)
    
    if message.text == '👤 TÀI KHOẢN':
        exp = users_db.get(uid, {}).get('expire_date')
        status = "🟢 VIP" if exp and exp > datetime.now() else "🔴 HẾT HẠN"
        d = exp.strftime("%d/%m/%Y %H:%M") if exp else "Chưa có VIP"
        bot.send_message(message.chat.id, f"🆔 ID: `{uid}`\n🌟 Status: {status}\n📅 Hạn: `{d}`", parse_mode="Markdown")

    elif message.text == '💳 NẠP VIP':
        bot.send_message(message.chat.id, f"🏦 **NẠP TỰ ĐỘNG**\nSTK: `80002422042` (MSB)\nNội dung: `NAP {uid}`", parse_mode="Markdown")

    elif message.text == '🎁 NHẬP CODE':
        m = bot.send_message(message.chat.id, "👉 Vui lòng nhập Giftcode của bạn:")
        bot.register_next_step_handler(m, process_redeem_code)

    elif message.text == '👑 QUẢN TRỊ' and int(uid) == ADMIN_ID:
        admin_panel(message)

    elif "SOI CẦU" in message.text:
        exp = users_db.get(uid, {}).get('expire_date')
        if not exp or exp < datetime.now():
            return bot.send_message(message.chat.id, "❌ Yêu cầu VIP để sử dụng!")
        mode = "THƯỜNG" if "XÓC ĐĨA" in message.text else "MD5"
        url = API_TX if mode == "THƯỜNG" else API_MD5
        users_db[uid]['is_running'] = True
        bot.send_message(message.chat.id, f"🚀 Khởi động AI {mode}...")
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode), daemon=True).start()

    elif message.text == '🛑 DỪNG TOOL':
        if uid in users_db: users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 Đã dừng.")

# ================= LOGIC GIFTCODE =================
def process_redeem_code(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    codes = load_codes()
    if code in codes:
        days = codes[code]
        now = datetime.now()
        start = users_db[uid]['expire_date'] if users_db[uid]['expire_date'] and users_db[uid]['expire_date'] > now else now
        users_db[uid]['expire_date'] = start + timedelta(days=days)
        save_data()
        del codes[code]
        save_codes(codes)
        bot.send_message(message.chat.id, f"✅ Thành công! Bạn được cộng {days} ngày VIP.")
    else:
        bot.send_message(message.chat.id, "❌ Code không tồn tại hoặc đã sử dụng.")

# ================= SOI CẦU =================
def auto_predict(chat_id, uid, api_url, mode):
    last_p = ""
    while users_db.get(uid, {}).get('is_running'):
        try:
            res = requests.get(api_url, timeout=10).json()
            p = str(res.get('phien', ''))
            if p != last_p:
                last_p = p
                kq = str(res.get('du doan', 'N/A')).upper()
                icon = "🔴 CHẴN" if "CHẴN" in kq or "TÀI" in kq else "⚪ LẺ"
                bot.send_message(chat_id, f"🦅 **{mode}** | Phiên: `{p}`\n🔮 Dự đoán: **{icon}**", parse_mode="Markdown")
        except: pass
        time.sleep(12)

# ================= ADMIN PANEL =================
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Thống Kê", callback_data="ad_stats"),
        types.InlineKeyboardButton("🎫 Tạo Code", callback_data="ad_gen_code"),
        types.InlineKeyboardButton("➕ Cộng Ngày", callback_data="ad_add_day"),
        types.InlineKeyboardButton("📢 Thông Báo", callback_data="ad_bc")
    )
    bot.send_message(message.chat.id, "👑 **ADMIN PANEL**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ad_'))
def callback_admin(call):
    if call.data == "ad_stats":
        bot.send_message(call.message.chat.id, f"👥 User: {len(users_db)}\n🎫 Code trống: {len(load_codes())}")
    elif call.data == "ad_gen_code":
        m = bot.send_message(call.message.chat.id, "👉 Nhập số ngày cho code này:")
        bot.register_next_step_handler(m, process_gen_code)
    elif call.data == "ad_add_day":
        m = bot.send_message(call.message.chat.id, "👉 Nhập: `ID SO_NGAY` (VD: `7816353760 30`)")
        bot.register_next_step_handler(m, process_admin_add)
    elif call.data == "ad_bc":
        m = bot.send_message(call.message.chat.id, "📣 Nhập nội dung thông báo:")
        bot.register_next_step_handler(m, process_admin_bc)

def process_gen_code(message):
    try:
        days = int(message.text)
        code = "VIP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        codes = load_codes()
        codes[code] = days
        save_codes(codes)
        bot.send_message(message.chat.id, f"🎫 Code mới: `{code}`\n⏳ Hạn: {days} ngày", parse_mode="Markdown")
    except: bot.send_message(message.chat.id, "❌ Lỗi.")

def process_admin_add(message):
    try:
        u, d = message.text.split()
        if u not in users_db: users_db[u] = {'expire_date': None, 'is_running': False}
        now = datetime.now()
        start = users_db[u]['expire_date'] if users_db[u]['expire_date'] and users_db[u]['expire_date'] > now else now
        users_db[u]['expire_date'] = start + timedelta(days=int(d))
        save_data()
        bot.send_message(message.chat.id, "✅ Xong.")
        bot.send_message(u, f"🎁 Admin tặng bạn {d} ngày VIP!")
    except: bot.send_message(message.chat.id, "❌ Sai định dạng.")

def process_admin_bc(message):
    for u in users_db:
        try: bot.send_message(u, f"📣 **TB ADMIN:**\n\n{message.text}")
        except: continue
    bot.send_message(message.chat.id, "✅ Đã gửi.")

# ================= RUN =================
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=check_bank_auto, daemon=True).start()
    bot.infinity_polling()
    
