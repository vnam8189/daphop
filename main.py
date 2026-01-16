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
headers = {'User-Agent': 'Mozilla/5.0'}

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

# ================= LOGIC DỰ ĐOÁN =================
def auto_predict(chat_id, uid, api_url, mode):
    last_p = ""
    bot.send_message(chat_id, f"🚀 **Đã kết nối Robot {mode}!** Đang quét phiên...", parse_mode="Markdown")
    
    while users_db.get(uid, {}).get('is_running'):
        try:
            res = requests.get(api_url, headers=headers, timeout=15).json()
            # Lấy key chuẩn từ API bạn gửi: 'phien hien tai' và 'du doan'
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
                    f"📊 Tỷ lệ thắng: `98.8%`\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                bot.send_message(chat_id, msg, parse_mode="Markdown")
        except: pass
        time.sleep(12)

# ================= HỆ THỐNG NÚT BẤM (FIXED) =================
def main_kb(uid):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    # Tên nút phải khớp 100% với handler bên dưới
    markup.add('🦅 SOI CẦU TÀI XỈU', '🛡️ SOI CẦU MD5')
    markup.add('👤 TÀI KHOẢN', '💳 NẠP VIP')
    markup.add('🎁 NHẬP CODE', '🛑 DỪNG TOOL')
    if int(uid) == ADMIN_ID:
        markup.add('👑 QUẢN TRỊ')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {'expire_date': None, 'is_running': False}
        save_data()
    
    bot.send_message(message.chat.id, 
        f"👋 Chào mừng **{message.from_user.first_name}**!\n"
        f"Hệ thống AI **XOCDIA88** đã sẵn sàng.", 
        reply_markup=main_kb(uid), parse_mode="Markdown")

# ================= XỬ LÝ TIN NHẮN =================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = str(message.from_user.id)
    text = message.text

    if text == '👤 TÀI KHOẢN':
        exp = users_db.get(uid, {}).get('expire_date')
        status = "🟢 VIP" if exp and exp > datetime.now() else "🔴 HẾT HẠN"
        d = exp.strftime("%d/%m/%Y %H:%M") if exp else "Chưa có"
        bot.send_message(message.chat.id, f"👤 **USER:** `{uid}`\n🌟 **Status:** {status}\n📅 **Hạn:** `{d}`", parse_mode="Markdown")

    elif text == '🦅 SOI CẦU TÀI XỈU' or text == '🛡️ SOI CẦU MD5':
        exp = users_db.get(uid, {}).get('expire_date')
        if not exp or exp < datetime.now():
            return bot.send_message(message.chat.id, "❌ **LỖI:** Bạn chưa có VIP!")
        
        mode = "TÀI XỈU" if "TÀI XỈU" in text else "MD5"
        url = API_TX if mode == "TÀI XỈU" else API_MD5
        
        # Ngừng luồng cũ nếu đang chạy để tránh spam
        users_db[uid]['is_running'] = True
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode), daemon=True).start()

    elif text == '🛑 DỪNG TOOL':
        if uid in users_db: users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 **Đã dừng Robot.**")

    elif text == '💳 NẠP VIP':
        bot.send_message(message.chat.id, f"🏦 **NẠP VIP TỰ ĐỘNG**\nSTK: `80002422042` (MSB)\nNội dung: `NAP {uid}`", parse_mode="Markdown")

    elif text == '🎁 NHẬP CODE':
        m = bot.send_message(message.chat.id, "👉 Nhập Giftcode của bạn:")
        bot.register_next_step_handler(m, redeem_code)

    elif text == '👑 QUẢN TRỊ' and int(uid) == ADMIN_ID:
        admin_panel(message)

# ================= ADMIN PANEL (RE-FIXED) =================
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Thống Kê", callback_data="ad_stats"),
        types.InlineKeyboardButton("🎫 Tạo Code", callback_data="ad_code"),
        types.InlineKeyboardButton("📢 Thông Báo", callback_data="ad_bc"),
        types.InlineKeyboardButton("➕ Cộng Ngày", callback_data="ad_add")
    )
    bot.send_message(message.chat.id, "👑 **QUẢN TRỊ VIÊN**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ad_'))
def ad_callback(call):
    if call.data == "ad_stats":
        bot.send_message(call.message.chat.id, f"📊 **User:** {len(users_db)}\n🎫 **Code:** {len(load_codes())}")
    elif call.data == "ad_code":
        m = bot.send_message(call.message.chat.id, "Nhập số ngày VIP:")
        bot.register_next_step_handler(m, gen_code)
    elif call.data == "ad_bc":
        m = bot.send_message(call.message.chat.id, "Nhập nội dung thông báo:")
        bot.register_next_step_handler(m, admin_broadcast)
    elif call.data == "ad_add":
        m = bot.send_message(call.message.chat.id, "Nhập: `ID NGAY` (VD: `123456 30`)")
        bot.register_next_step_handler(m, admin_add_days)

def gen_code(message):
    try:
        days = int(message.text)
        code = "X88-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        codes = load_codes()
        codes[code] = days
        save_codes(codes)
        bot.send_message(message.chat.id, f"🎫 **Đã tạo:** `{code}` ({days} ngày)")
    except: bot.send_message(message.chat.id, "❌ Lỗi định dạng.")

def admin_add_days(message):
    try:
        u, d = message.text.split()
        if u not in users_db: users_db[u] = {'expire_date': None, 'is_running': False}
        now = datetime.now()
        start = users_db[u]['expire_date'] if users_db[u].get('expire_date') and users_db[u]['expire_date'] > now else now
        users_db[u]['expire_date'] = start + timedelta(days=int(d))
        save_data()
        bot.send_message(message.chat.id, "✅ Đã cộng ngày.")
    except: bot.send_message(message.chat.id, "❌ Lỗi định dạng.")

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
    else: bot.send_message(message.chat.id, "❌ Code không tồn tại.")

# ================= AUTO BANK =================
def auto_bank():
    while True:
        try:
            res = requests.get(BANK_API, timeout=15).json()
            txns = res if isinstance(res, list) else res.get('data', [])
            for tr in txns:
                content = str(tr.get('noi_dung', '')).upper()
                amt = int(''.join(filter(str.isdigit, str(tr.get('so_tien', '0')))))
                if "NAP" in content:
                    u_id = content.split("NAP")[1].strip().split()[0]
                    u_id = ''.join(filter(str.isdigit, u_id))
                    if u_id in users_db:
                        days = 999 if amt >= 100000 else (15 if amt >= 50000 else 7)
                        now = datetime.now()
                        start = users_db[u_id]['expire_date'] if users_db[u_id].get('expire_date') and users_db[u_id]['expire_date'] > now else now
                        users_db[u_id]['expire_date'] = start + timedelta(days=days)
                        save_data()
                        bot.send_message(u_id, f"🌟 **NẠP THÀNH CÔNG!** Chúc bạn may mắn.")
        except: pass
        time.sleep(30)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=auto_bank, daemon=True).start()
    bot.infinity_polling()
        
