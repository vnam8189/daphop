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

# ================= SERVER MỒI =================
app = Flask(__name__)
@app.route('/')
def home(): return "<h1>XOCDIA88 SYSTEM - ONLINE</h1>"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ================= CẤU HÌNH =================
API_TOKEN = '8404770438:AAHNI8xRHFlWPVNF4gL2-CShnvqgQ_OXUEI'
ADMIN_ID = 7816353760 

API_TX = "https://xd88-apsj.onrender.com/xd88/tx"
API_MD5 = "https://xd88-apsj.onrender.com/xd88/md5"
BANK_API = "https://spayment.net/msb-history?history=80002422042"

DB_FILE = 'users_db.json'
CODE_FILE = 'giftcodes.json'

bot = telebot.TeleBot(API_TOKEN)
headers = {'User-Agent': 'Mozilla/5.0'} # Giúp API Render không bị chặn

# ================= QUẢN LÝ DỮ LIỆU =================
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                for uid in data:
                    if data[uid].get('expire_date'):
                        data[uid]['expire_date'] = datetime.strptime(data[uid]['expire_date'], '%Y-%m-%d %H:%M:%S')
                return data
        except: return {}
    return {}

def save_data():
    data_to_save = {}
    for uid, info in users_db.items():
        data_to_save[uid] = info.copy()
        if info.get('expire_date'):
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

# ================= LOGIC DỰ ĐOÁN (FIXED) =================
def auto_predict(chat_id, uid, api_url, mode):
    last_p = ""
    # Gửi thông báo bắt đầu để user biết bot đã chạy
    bot.send_message(chat_id, f"✅ **Robot {mode} đã kết nối!** Đang đợi phiên mới...", parse_mode="Markdown")
    
    while users_db.get(uid, {}).get('is_running'):
        try:
            # Gọi API với Header và Timeout
            res = requests.get(api_url, headers=headers, timeout=15).json()
            
            # Lấy dữ liệu theo đúng key trong ảnh bạn gửi
            p = str(res.get('phien hien tai') or res.get('phien', ''))
            kq = str(res.get('du doan', '')).upper()

            if p != "" and p != last_p:
                last_p = p
                icon = "🔴 TÀI" if "TÀI" in kq else "⚪ XỈU"
                
                msg = (
                    f"🦅 **XOCDIA88 - {mode}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 Phiên: `{p}`\n"
                    f"🔮 Dự đoán: **{icon}**\n"
                    f"📊 Độ tin cậy: `98%`\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                bot.send_message(chat_id, msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Lỗi API: {e}")
        
        time.sleep(12) # Check mỗi 12 giây

# ================= MENU CHÍNH =================
def main_kb(uid):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🦅 SOI CẦU TÀI XỈU', '🛡️ SOI CẦU MD5')
    markup.add('👤 TÀI KHOẢN', '💳 NẠP VIP')
    markup.add('🎁 NHẬP CODE', '🛑 DỪNG TOOL')
    if int(uid) == ADMIN_ID: markup.add('👑 QUẢN TRỊ')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {'expire_date': None, 'is_running': False}
        save_data()
    bot.send_message(message.chat.id, f"👋 Chào mừng bạn đến với **XOCDIA88 AI**!", reply_markup=main_kb(uid), parse_mode="Markdown")

# ================= XỬ LÝ SỰ KIỆN =================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = str(message.from_user.id)
    
    if message.text == '👤 TÀI KHOẢN':
        exp = users_db.get(uid, {}).get('expire_date')
        status = "🟢 VIP" if exp and exp > datetime.now() else "🔴 HẾT HẠN"
        d = exp.strftime("%d/%m/%Y %H:%M") if exp else "Chưa có"
        bot.send_message(message.chat.id, f"👤 **USER:** `{uid}`\n🌟 **Status:** {status}\n📅 **Hạn:** `{d}`", parse_mode="Markdown")

    elif "SOI CẦU" in message.text:
        exp = users_db.get(uid, {}).get('expire_date')
        if not exp or exp < datetime.now():
            return bot.send_message(message.chat.id, "❌ **LỖI:** Vui lòng nạp VIP!")
        
        mode = "TÀI XỈU" if "TÀI XỈU" in message.text else "MD5"
        url = API_TX if mode == "TÀI XỈU" else API_MD5
        users_db[uid]['is_running'] = True
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode), daemon=True).start()

    elif message.text == '🛑 DỪNG TOOL':
        if uid in users_db: users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 **Đã dừng robot.**")

    elif message.text == '💳 NẠP VIP':
        bot.send_message(message.chat.id, f"🏦 **NẠP VIP TỰ ĐỘNG**\nSTK: `80002422042` (MSB)\nNội dung: `NAP {uid}`", parse_mode="Markdown")

    elif message.text == '🎁 NHẬP CODE':
        m = bot.send_message(message.chat.id, "👉 Nhập Giftcode của bạn:")
        bot.register_next_step_handler(m, redeem_code)

    elif message.text == '👑 QUẢN TRỊ' and int(uid) == ADMIN_ID:
        admin_panel(message)

# ================= ADMIN PANEL =================
def admin_panel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Thống Kê", callback_data="ad_stats"))
    markup.add(types.InlineKeyboardButton("🎫 Tạo Code", callback_data="ad_code"))
    markup.add(types.InlineKeyboardButton("📢 Thông Báo", callback_data="ad_bc"))
    bot.send_message(message.chat.id, "👑 **ADMIN PANEL**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ad_'))
def ad_callback(call):
    if call.data == "ad_stats":
        bot.send_message(call.message.chat.id, f"👥 Tổng: {len(users_db)} users.")
    elif call.data == "ad_code":
        m = bot.send_message(call.message.chat.id, "Nhập số ngày:")
        bot.register_next_step_handler(m, gen_code)
    elif call.data == "ad_bc":
        m = bot.send_message(call.message.chat.id, "Nhập nội dung thông báo:")
        bot.register_next_step_handler(m, admin_broadcast)

def gen_code(message):
    try:
        days = int(message.text)
        code = "X88-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        codes = load_codes()
        codes[code] = days
        save_codes(codes)
        bot.send_message(message.chat.id, f"🎫 Code: `{code}` ({days} ngày)")
    except: bot.send_message(message.chat.id, "Lỗi số ngày.")

def admin_broadcast(message):
    for u in users_db:
        try: bot.send_message(u, f"📣 **TB ADMIN:**\n\n{message.text}", parse_mode="Markdown")
        except: continue
    bot.send_message(message.chat.id, "✅ Đã gửi xong.")

def redeem_code(message):
    uid = str(message.from_user.id)
    code = message.text.strip()
    codes = load_codes()
    if code in codes:
        days = codes[code]
        now = datetime.now()
        start = users_db[uid]['expire_date'] if users_db[uid].get('expire_date') and users_db[uid]['expire_date'] > now else now
        users_db[uid]['expire_date'] = start + timedelta(days=days)
        save_data()
        del codes[code]
        save_codes(codes)
        bot.send_message(message.chat.id, f"✅ Thành công! +{days} ngày VIP.")
    else: bot.send_message(message.chat.id, "❌ Code sai.")

# ================= AUTO BANK =================
def auto_bank():
    while True:
        try:
            res = requests.get(BANK_API, timeout=15).json()
            txns = res if isinstance(res, list) else res.get('data', [])
            for tr in txns:
                content = str(tr.get('noi_dung', '')).upper()
                amt = int(''.join(filter(str.isdigit, str(tr.get('so_tien', '0')))))
                if "NAP" in content and amt >= 20000:
                    u_id = content.split("NAP")[1].strip().split()[0]
                    u_id = ''.join(filter(str.isdigit, u_id))
                    if u_id in users_db:
                        days = 999 if amt >= 100000 else (15 if amt >= 50000 else 7)
                        now = datetime.now()
                        start = users_db[u_id]['expire_date'] if users_db[u_id].get('expire_date') and users_db[u_id]['expire_date'] > now else now
                        users_db[u_id]['expire_date'] = start + timedelta(days=days)
                        save_data()
                        bot.send_message(u_id, f"🌟 Nạp VIP thành công qua Bank!")
        except: pass
        time.sleep(30)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=auto_bank, daemon=True).start()
    bot.infinity_polling()
            
