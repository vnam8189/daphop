import telebot
import requests
import time
import threading
import json
import random
import os
from datetime import datetime, timedelta
from telebot import types
from flask import Flask, request

# ================= CẤU HÌNH SERVER (RENDER) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>BOT MSB AUTO IS RUNNING!</h1>"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ================= CẤU HÌNH BOT & BANK =================
API_TOKEN = '8404770438:AAHNI8xRHFlWPVNF4gL2-CShnvqgQ_OXUEI' # TOKEN CỦA BẠN
ADMIN_ID = 7816353760                                    # ID ADMIN

# API BANK (MSB - SPAYMENT)
BANK_API_URL = "https://spayment.net/msb-history?history=80002422042"
STK_BANK = '80002422042'
NAME_BANK = 'MSB (Maritime Bank)'

# API GAME
API_TX = "https://xd88-apsj.onrender.com/xd88/tx"
API_MD5 = "https://xd88-apsj.onrender.com/xd88/md5"
DB_FILE = 'users_db.json'

bot = telebot.TeleBot(API_TOKEN)

# ================= QUẢN LÝ DATA =================
def load_data():
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            for uid in data:
                if data[uid]['expire_date']:
                    data[uid]['expire_date'] = datetime.strptime(data[uid]['expire_date'], '%Y-%m-%d %H:%M:%S')
            return data
    except: return {}

def save_data():
    data_to_save = {}
    for uid, info in users_db.items():
        data_to_save[uid] = info.copy()
        if info['expire_date']:
            data_to_save[uid]['expire_date'] = info['expire_date'].strftime('%Y-%m-%d %H:%M:%S')
    with open(DB_FILE, 'w') as f:
        json.dump(data_to_save, f)

users_db = load_data()

# ================= AUTO BANK (MSB SPAYMENT) =================
def check_bank_auto():
    print("🤖 Đang kết nối API MSB...")
    processed_txns = [] # Lưu các mã giao dịch đã xử lý để tránh cộng trùng
    
    while True:
        try:
            # Gọi API
            res = requests.get(BANK_API_URL, timeout=15).json()
            
            # --- DEBUG: IN DATA ĐỂ KIỂM TRA (XÓA SAU KHI CHẠY ỔN) ---
            # print("Data Bank:", res) 
            
            # Giả định cấu trúc JSON trả về.
            # Bạn cần xem log để biết chính xác nó nằm trong key 'transactions', 'data' hay là 1 list trực tiếp.
            # Code dưới đây xử lý các trường hợp phổ biến:
            transactions = []
            if isinstance(res, list): 
                transactions = res
            elif isinstance(res, dict):
                transactions = res.get('transactions', []) or res.get('data', []) or res.get('history', [])

            for tr in transactions:
                # 1. LẤY DỮ LIỆU (Sửa key ở đây nếu API khác)
                # Ví dụ: API trả về 'amount' hay 'creditAmount'? 'content' hay 'description'?
                amount = int(tr.get('amount', 0) or tr.get('sotien', 0) or tr.get('creditAmount', 0))
                desc = str(tr.get('description', '') or tr.get('noidung', '') or tr.get('content', '')).upper()
                tid = str(tr.get('transactionId', '') or tr.get('id', '') or tr.get('refNo', ''))

                # Chỉ xử lý giao dịch nhận tiền (> 0) và chưa xử lý
                if amount > 0 and tid not in processed_txns:
                    if "NAP" in desc:
                        try:
                            # Tách ID: "NAP 123456" -> lấy 123456
                            target_id = desc.split("NAP")[1].strip().split()[0]
                            # Lọc sạch ký tự lạ
                            target_id = ''.join(filter(str.isdigit, target_id))

                            if target_id in users_db:
                                days = 0
                                if amount >= 120000: days = 9999
                                elif amount >= 60000: days = 14
                                elif amount >= 30000: days = 7
                                
                                if days > 0:
                                    now = datetime.now()
                                    start = users_db[target_id]['expire_date']
                                    if not start or start < now: start = now
                                    users_db[target_id]['expire_date'] = start + timedelta(days=days)
                                    save_data()
                                    
                                    # Đánh dấu đã xử lý
                                    processed_txns.append(tid)
                                    if len(processed_txns) > 100: processed_txns.pop(0) # Giữ list gọn nhẹ

                                    bot.send_message(target_id, f"✅ **TIỀN VỀ: {amount:,}đ**\nĐã kích hoạt {days} ngày VIP MSB Auto!")
                                    bot.send_message(ADMIN_ID, f"💰 **AUTO BANK MSB:** ID {target_id} nạp {amount:,}đ.")
                        except:
                            continue
        except Exception as e:
            print(f"Lỗi check bank: {e}")
        
        time.sleep(20) # Check mỗi 20 giây

threading.Thread(target=check_bank_auto, daemon=True).start()

# ================= LOGIC GAME & BOT =================
def get_prediction(url):
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except: return None

def check_expired(user_id):
    uid = str(user_id)
    if uid not in users_db or users_db[uid]['expire_date'] is None: return False
    return datetime.now() < users_db[uid]['expire_date']

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🔴 SOI CẦU XÓC ĐĨA', '🛡️ SOI CẦU MD5')
    markup.add('👤 TÀI KHOẢN', '💳 NẠP VIP', '🛑 DỪNG TOOL')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {'expire_date': None, 'is_running': False}
        save_data()
    bot.send_message(message.chat.id, "🦅 **BOT XOCDIA88 PREDICT MSB** 🦅", reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    uid = str(message.from_user.id)
    if uid not in users_db: users_db[uid] = {'expire_date': None, 'is_running': False}

    if message.text == '👤 TÀI KHOẢN':
        exp = users_db[uid]['expire_date']
        status = "🟢 VIP ACTIVE" if check_expired(uid) else "🔴 HẾT HẠN"
        d = exp.strftime("%d/%m/%Y") if exp else "Chưa ĐK"
        bot.send_message(message.chat.id, f"🆔 `{uid}`\nTrạng thái: {status}\nHạn: {d}", parse_mode="Markdown")

    elif message.text == '💳 NẠP VIP':
        msg = (
            f"🏦 **CỔNG THANH TOÁN TỰ ĐỘNG MSB**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 Ngân hàng: **{NAME_BANK}**\n"
            f"🔹 STK: `{STK_BANK}`\n"
            f"🔹 Nội dung: `NAP {uid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Hệ thống tự động check API MSB mỗi 20s.*"
        )
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

    elif message.text in ['🔴 SOI CẦU XÓC ĐĨA', '🛡️ SOI CẦU MD5']:
        if not check_expired(uid): return bot.send_message(message.chat.id, "❌ Vui lòng Nạp VIP để sử dụng.")
        mode = "THƯỜNG" if "XÓC ĐĨA" in message.text else "MD5"
        url = API_TX if mode == "THƯỜNG" else API_MD5
        users_db[uid]['is_running'] = True
        bot.send_message(message.chat.id, f"🚀 Đang khởi động AI {mode}...")
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode)).start()

    elif message.text == '🛑 DỪNG TOOL':
        users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 Đã dừng tool.")

# --- DỰ ĐOÁN ---
def auto_predict(chat_id, uid, api_url, mode_name):
    last_phien = ""
    while users_db.get(uid, {}).get('is_running') and check_expired(uid):
        res = get_prediction(api_url)
        if res and str(res.get('phien')) != last_phien:
            last_phien = str(res.get('phien'))
            du_doan = (res.get('du doan') or "").upper()
            icon = "🔴 CHẴN" if "CHẴN" in du_doan or "TÀI" in du_doan else "⚪ LẺ"
            bot.send_message(chat_id, f"🦅 {mode_name}: {last_phien}\nKQ: **{icon}**")
        time.sleep(10)

# --- XỬ LÝ ẢNH BILL (Backup) ---
@bot.message_handler(content_types=['photo'])
def handle_bill(message):
    uid = str(message.from_user.id)
    bot.send_message(uid, "✅ Đã gửi bill cho Admin check tay.")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Duyệt 7 Ngày", callback_data=f"add_7_{uid}"))
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"Bill từ `{uid}`", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if 'add' in call.data:
        uid = call.data.split('_')[2]
        users_db[uid] = {'expire_date': datetime.now() + timedelta(days=7), 'is_running': False}
        save_data()
        bot.send_message(uid, "✅ Admin đã kích hoạt VIP.")
        bot.edit_message_caption("✅ Đã duyệt", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_web_server).start()
    bot.infinity_polling()
          
