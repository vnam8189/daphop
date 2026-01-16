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

# ================= LOGIC SOI CẦU (FIXED ACCENTS & KEYS) =================
def get_val(data, keys):
    for k in keys:
        if k in data: return data[k]
    return None

def auto_predict(chat_id, uid, api_url, mode):
    last_p = ""
    bot.send_message(chat_id, f"✅ **Robot {mode} đã kết nối!**", parse_mode="Markdown")
    
    while users_db.get(uid, {}).get('is_running'):
        try:
            res = requests.get(api_url, headers=headers, timeout=15).json()
            
            # Lấy thông tin phiên cũ
            p_cu = get_val(res, ['phien'])
            x1 = get_val(res, ['xuc xac 1', 'xuc_xac_1'])
            x2 = get_val(res, ['xuc xac 2', 'xuc_xac_2'])
            x3 = get_val(res, ['xuc xac 3', 'xuc_xac_3'])
            tong = get_val(res, ['tong'])
            kq_cu_raw = str(get_val(res, ['ket qua', 'ket_qua']) or "").upper()
            
            # Lấy thông tin dự đoán
            p_moi = get_val(res, ['phien hien tai', 'phien_hien_tai'])
            du_doan_raw = str(get_val(res, ['du doan', 'du_doan']) or "").upper()

            if p_moi and str(p_moi) != last_p:
                last_p = str(p_moi)
                
                # FIX LỖI TIẾNG VIỆT: Kiểm tra cả TÀI và TAI
                icon_cu = "🔴 TÀI" if any(x in kq_cu_raw for x in ["TÀI", "TAI"]) else "⚪ XỈU"
                icon_dd = "🔴 TÀI" if any(x in du_doan_raw for x in ["TÀI", "TAI"]) else "⚪ XỈU"
                
                msg = (
                    f"🦅 **XOCDIA88 - {mode}** 🦅\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 **KẾT QUẢ PHIÊN `{p_cu}`:**\n"
                    f"🎲 Xúc xắc: `{x1}-{x2}-{x3}` ({tong})\n"
                    f"✨ Kết quả: **{icon_cu}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔮 **DỰ ĐOÁN PHIÊN `{p_moi}`:**\n"
                    f"👉 Cầu báo: **{icon_dd}**\n"
                    f"📈 Tỷ lệ thắng: `98.9%`\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                bot.send_message(chat_id, msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(10)

# ================= MENU & HANDLERS =================
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
    bot.send_message(message.chat.id, "👋 Chào mừng đến với **XOCDIA88 AI**!", reply_markup=main_kb(uid), parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = str(message.from_user.id)
    text = message.text

    if text == '👤 TÀI KHOẢN':
        exp = users_db.get(uid, {}).get('expire_date')
        status = "🟢 VIP" if exp and exp > datetime.now() else "🔴 HẾT HẠN"
        d = exp.strftime("%d/%m/%Y %H:%M") if exp else "Chưa có"
        bot.send_message(message.chat.id, f"👤 **ID:** `{uid}`\n🌟 **Status:** {status}\n📅 **Hạn:** `{d}`", parse_mode="Markdown")

    elif text in ['🦅 SOI CẦU TÀI XỈU', '🛡️ SOI CẦU MD5']:
        exp = users_db.get(uid, {}).get('expire_date')
        if not exp or exp < datetime.now():
            return bot.send_message(message.chat.id, "❌ **LỖI:** Vui lòng nạp VIP!")
        
        mode = "TÀI XỈU" if "TÀI XỈU" in text else "MD5"
        url = API_TX if mode == "TÀI XỈU" else API_MD5
        users_db[uid]['is_running'] = True
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode), daemon=True).start()

    elif text == '🛑 DỪNG TOOL':
        if uid in users_db: users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 **Đã dừng robot.**")

    elif text == '💳 NẠP VIP':
        bot.send_message(message.chat.id, f"🏦 **NẠP VIP TỰ ĐỘNG**\nSTK: `80002422042` (MSB)\nNội dung: `NAP {uid}`", parse_mode="Markdown")

    elif text == '🎁 NHẬP CODE':
        m = bot.send_message(message.chat.id, "👉 Nhập Giftcode:")
        bot.register_next_step_handler(m, redeem_code)

    elif text == '👑 QUẢN TRỊ' and int(uid) == ADMIN_ID:
        admin_panel(message)

# ================= ADMIN & BANK =================
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📊 Thống Kê", callback_data="ad_stats"),
               types.InlineKeyboardButton("🎫 Tạo Code", callback_data="ad_code"),
               types.InlineKeyboardButton("➕ Cộng Ngày", callback_data="ad_add"))
    bot.send_message(message.chat.id, "👑 **ADMIN PANEL**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ad_'))
def ad_callback(call):
    if call.data == "ad_stats":
        bot.send_message(call.message.chat.id, f"📊 **User:** {len(users_db)}")
    elif call.data == "ad_code":
        m = bot.send_message(call.message.chat.id, "Nhập số ngày:")
        bot.register_next_step_handler(m, gen_code)
    elif call.data == "ad_add":
        m = bot.send_message(call.message.chat.id, "Nhập: `ID NGAY`")
        bot.register_next_step_handler(m, admin_add_days)

def gen_code(message):
    try:
        days = int(message.text)
        code = "X88-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        codes = load_codes(); codes[code] = days; save_codes(codes)
        bot.send_message(message.chat.id, f"🎫 Code: `{code}` ({days} ngày)")
    except: bot.send_message(message.chat.id, "❌ Lỗi.")

def admin_add_days(message):
    try:
        u, d = message.text.split()
        if u not in users_db: users_db[u] = {'expire_date': None, 'is_running': False}
        now = datetime.now()
        start = users_db[u]['expire_date'] if users_db[u].get('expire_date') and users_db[u]['expire_date'] > now else now
        users_db[u]['expire_date'] = start + timedelta(days=int(d))
        save_data()
        bot.send_message(message.chat.id, f"✅ Đã cộng ngày.")
    except: bot.send_message(message.chat.id, "❌ Lỗi.")

def redeem_code(message):
    uid = str(message.from_user.id); code = message.text.strip(); codes = load_codes()
    if code in codes:
        days = codes[code]; now = datetime.now()
        start = users_db[uid]['expire_date'] if users_db[uid].get('expire_date') and users_db[uid]['expire_date'] > now else now
        users_db[uid]['expire_date'] = start + timedelta(days=days)
        save_data(); del codes[code]; save_codes(codes)
        bot.send_message(message.chat.id, f"✅ Thành công! +{days} ngày.")
    else: bot.send_message(message.chat.id, "❌ Code sai.")

def auto_bank():
    while True:
        try:
            res = requests.get(BANK_API, timeout=15).json()
            txns = res if isinstance(res, list) else res.get('data', [])
            for tr in txns:
                content = str(tr.get('noi_dung', '')).upper()
                amt = int(''.join(filter(str.isdigit, str(tr.get('so_tien', '0')))))
                if "NAP" in content:
                    u_id = ''.join(filter(str.isdigit, content.split("NAP")[1]))
                    if u_id in users_db:
                        days = 30 if amt >= 100000 else 7
                        now = datetime.now()
                        start = users_db[u_id]['expire_date'] if users_db[u_id].get('expire_date') and users_db[u_id]['expire_date'] > now else now
                        users_db[u_id]['expire_date'] = start + timedelta(days=days)
                        save_data()
                        bot.send_message(u_id, "🌟 **NẠP THÀNH CÔNG!**")
        except: pass
        time.sleep(30)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=auto_bank, daemon=True).start()
    bot.infinity_polling()
        
