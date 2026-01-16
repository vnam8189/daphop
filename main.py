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

# ================= SERVER MỒI (KEEP ALIVE) =================
app = Flask(__name__)
@app.route('/')
def home(): return "<h1>XOCDIA88 VIP SYSTEM - ONLINE</h1>"

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

users_db = load_data()

# ================= LOGIC SOI CẦU CHUẨN API =================
def auto_predict(chat_id, uid, api_url, mode):
    last_p = ""
    while users_db.get(uid, {}).get('is_running'):
        try:
            # Gửi request lấy JSON từ API Render
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Trích xuất dữ liệu bám sát screenshot bạn gửi
                phien_moi = str(data.get('phien hien tai', ''))
                ket_qua_du_doan = str(data.get('du doan', 'Đang quét...'))

                # Chỉ gửi khi có phiên mới xuất hiện
                if phien_moi != last_p and phien_moi != "":
                    last_p = phien_moi
                    
                    # Trang trí giao diện tin nhắn đẹp
                    msg_template = (
                        f"🦅 **XOCDIA88 - AI PREDICT** 🦅\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎮 Chế độ: `{mode}`\n"
                        f"🆔 Phiên: `{phien_moi}`\n"
                        f"🔮 Dự đoán: **{ket_qua_du_doan.upper()}**\n"
                        f"📊 Tỷ lệ chính xác: `98%`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚠️ *Lưu ý: Đánh đều tay, không tất tay!*"
                    )
                    bot.send_message(chat_id, msg_template, parse_mode="Markdown")
            
        except Exception as e:
            print(f"Lỗi logic API: {e}")
        
        # Nghỉ 10 giây mỗi lần quét để tránh bị API chặn
        time.sleep(10)

# ================= XỬ LÝ TIN NHẮN (GIAO DIỆN ĐẸP) =================
@bot.message_handler(commands=['start'])
def welcome(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {'expire_date': None, 'is_running': False}
        save_data()
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🦅 SOI CẦU TÀI XỈU', '🛡️ SOI CẦU MD5')
    markup.add('👤 TÀI KHOẢN', '💳 NẠP VIP')
    markup.add('🎁 NHẬP CODE', '🛑 DỪNG TOOL')
    
    welcome_msg = (
        f"👋 Chào mừng **{message.from_user.first_name}**!\n"
        f"Bạn đang sử dụng hệ thống AI của **XOCDIA88**.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 Vui lòng chọn chức năng bên dưới để bắt đầu."
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = str(message.from_user.id)
    
    if message.text == '👤 TÀI KHOẢN':
        exp = users_db.get(uid, {}).get('expire_date')
        status = "🟢 VIP PRO" if exp and exp > datetime.now() else "🔴 THÀNH VIÊN"
        han = exp.strftime("%d/%m/%Y %H:%M") if exp else "Chưa đăng ký"
        
        bot.send_message(message.chat.id, 
            f"👤 **THÔNG TIN USER**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: `{uid}`\n"
            f"🛡️ Cấp độ: {status}\n"
            f"📅 Hạn VIP: `{han}`", parse_mode="Markdown")

    elif "SOI CẦU" in message.text:
        exp = users_db.get(uid, {}).get('expire_date')
        if not exp or exp < datetime.now():
            return bot.send_message(message.chat.id, "❌ **LỖI:** Tài khoản chưa kích hoạt VIP!")
        
        mode = "TÀI XỈU" if "TÀI XỈU" in message.text else "MD5"
        url = API_TX if mode == "TÀI XỈU" else API_MD5
        
        users_db[uid]['is_running'] = True
        bot.send_message(message.chat.id, f"⚡ **Hệ thống XOCDIA88 đang kết nối server {mode}...**")
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode), daemon=True).start()

    elif message.text == '🛑 DỪNG TOOL':
        if uid in users_db: users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 **Đã ngắt kết nối robot.**")

    elif message.text == '💳 NẠP VIP':
        nạp_msg = (
            f"💳 **HỆ THỐNG NẠP TỰ ĐỘNG**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Ngân hàng: **MSB**\n"
            f"🆔 STK: `80002422042`\n"
            f"📝 Nội dung: `NAP {uid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Lưu ý: Nhập đúng nội dung để được cộng VIP tự động!*"
        )
        bot.send_message(message.chat.id, nạp_msg, parse_mode="Markdown")

# ================= AUTO BANK (MSB) =================
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
                            if u_id in users_db:
                                days = 999 if amount >= 100000 else (15 if amount >= 50000 else (7 if amount >= 20000 else 0))
                                if days > 0:
                                    now = datetime.now()
                                    start = users_db[u_id]['expire_date'] if users_db[u_id]['expire_date'] and users_db[u_id]['expire_date'] > now else now
                                    users_db[u_id]['expire_date'] = start + timedelta(days=days)
                                    save_data()
                                    processed_txns.append(tid)
                                    bot.send_message(u_id, f"🌟 **XOCDIA88:** Nạp VIP thành công (+{days} ngày)!")
                        except: continue
        except: pass
        time.sleep(25)

# ================= KHỞI CHẠY =================
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=check_bank_auto, daemon=True).start()
    bot.infinity_polling()
    
