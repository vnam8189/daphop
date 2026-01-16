import telebot
import requests
import time
import threading
import json
import os
from datetime import datetime, timedelta
from telebot import types
from flask import Flask

# ================= SERVER MỒI (GIỮ BOT SỐNG TRÊN RENDER) =================
app = Flask(__name__)
@app.route('/')
def home(): return "<h1>BOT PREDICT VIP V3 IS ONLINE!</h1>"

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

# ================= HỆ THỐNG AUTO BANK (FIX LỖI CỘNG TIỀN) =================
def check_bank_auto():
    processed_txns = [] 
    while True:
        try:
            res = requests.get(BANK_API_URL, timeout=15).json()
            transactions = res if isinstance(res, list) else res.get('data', [])

            for tr in transactions:
                # Lọc sạch số tiền (Xử lý chuỗi "2.000 VNĐ" từ API)
                amount_str = str(tr.get('so_tien') or tr.get('amount', '0'))
                amount = int(''.join(filter(str.isdigit, amount_str)))
                
                content = str(tr.get('noi_dung') or tr.get('description', '')).upper()
                tid = str(tr.get('ma_gd') or tr.get('transactionId', ''))

                if amount > 0 and tid not in processed_txns:
                    if "NAP" in content:
                        try:
                            user_id = content.split("NAP")[1].strip().split()[0]
                            user_id = ''.join(filter(str.isdigit, user_id))

                            if user_id not in users_db:
                                users_db[user_id] = {'expire_date': None, 'is_running': False}

                            days = 0
                            if amount >= 100000: days = 999 
                            elif amount >= 50000: days = 15
                            elif amount >= 20000: days = 7
                            
                            if days > 0:
                                now = datetime.now()
                                current_exp = users_db[user_id]['expire_date']
                                start_point = current_exp if current_exp and current_exp > now else now
                                
                                users_db[user_id]['expire_date'] = start_point + timedelta(days=days)
                                save_data()
                                processed_txns.append(tid)

                                # Thông báo khách hàng
                                bot.send_message(user_id, f"🌟 **NẠP VIP THÀNH CÔNG** 🌟\n━━━━━━━━━━━━━━━━━━━━\n💰 Số tiền: `+{amount:,} VNĐ`\n🎁 Gói VIP: `+{days} Ngày`\n📅 Hạn mới: `{users_db[user_id]['expire_date'].strftime('%d/%m/%Y %H:%M')}`\n━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
                                bot.send_message(ADMIN_ID, f"💰 **TIỀN VỀ:** ID `{user_id}` nạp `{amount:,}đ` thành công!")
                        except: continue
        except: pass
        time.sleep(25)

# ================= GIAO DIỆN /START CHUYÊN NGHIỆP =================
@bot.message_handler(commands=['start'])
def welcome(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {'expire_date': None, 'is_running': False}
        save_data()
    
    welcome_text = (
        f"👋 **Chào mừng {message.from_user.first_name} đã quay trở lại!**\n"
        f"Hệ thống **PREDICT VIP AI** - Đỉnh cao soi cầu 🦅\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 **Ưu điểm vượt trội:**\n"
        f"✅ AI phân tích cầu chuẩn xác 85-95%.\n"
        f"✅ Không độ trễ, báo kết quả tức thì.\n"
        f"✅ Tự động kích hoạt VIP 24/7.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **Các bước sử dụng:**\n"
        f"1️⃣ Nhấn **💳 NẠP VIP** để đăng ký.\n"
        f"2️⃣ Chọn loại cầu muốn soi (Xóc Đĩa/MD5).\n"
        f"3️⃣ Nhận kết quả và vào lệnh.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 *Chúc bạn có một ngày đại thắng!*"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

# ================= MENU CHÍNH =================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🔴 SOI CẦU XÓC ĐĨA', '🛡️ SOI CẦU MD5')
    markup.add('👤 TÀI KHOẢN', '💳 NẠP VIP')
    markup.add('🛑 DỪNG TOOL')
    return markup

# ================= XỬ LÝ LỆNH NGƯỜI DÙNG =================
@bot.message_handler(func=lambda m: True)
def handle_user(message):
    uid = str(message.from_user.id)
    if message.text == '👤 TÀI KHOẢN':
        exp = users_db.get(uid, {}).get('expire_date')
        status = "🟢 VIP ACTIVE" if exp and exp > datetime.now() else "🔴 HẾT HẠN"
        d = exp.strftime("%d/%m/%Y %H:%M") if exp else "Chưa có gói VIP"
        bot.send_message(message.chat.id, f"👤 **THÔNG TIN TÀI KHOẢN**\n━━━━━━━━━━━━━\n🆔 ID: `{uid}`\n🌟 Trạng thái: {status}\n📅 Hết hạn: `{d}`", parse_mode="Markdown")

    elif message.text == '💳 NẠP VIP':
        msg = (
            f"🏦 **CỔNG NẠP TỰ ĐỘNG (MSB)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 Ngân hàng: **MSB**\n"
            f"🔹 Số TK: `80002422042`\n"
            f"🔹 Nội dung: `NAP {uid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡️ Chờ 20-30s sau khi chuyển để hệ thống duyệt."
        )
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

    elif "SOI CẦU" in message.text:
        exp = users_db.get(uid, {}).get('expire_date')
        if not exp or exp < datetime.now():
            return bot.send_message(message.chat.id, "❌ **BẠN CHƯA CÓ VIP**\nVui lòng nạp gói để dùng AI Soi Cầu.")
        
        mode = "THƯỜNG" if "XÓC ĐĨA" in message.text else "MD5"
        url = API_TX if mode == "THƯỜNG" else API_MD5
        users_db[uid]['is_running'] = True
        bot.send_message(message.chat.id, f"🚀 **Đang lấy tín hiệu {mode}...**")
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode), daemon=True).start()

    elif message.text == '🛑 DỪNG TOOL':
        if uid in users_db: users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 Đã ngắt kết nối tín hiệu.")

def auto_predict(chat_id, uid, api_url, mode):
    last_phien = ""
    while users_db.get(uid, {}).get('is_running'):
        try:
            res = requests.get(api_url, timeout=10).json()
            phien = str(res.get('phien', ''))
            if phien != last_phien:
                last_phien = phien
                du_doan = str(res.get('du doan') or res.get('du_doan', 'N/A')).upper()
                icon = "🔴 CHẴN" if "CHẴN" in du_doan or "TÀI" in du_doan else "⚪ LẺ"
                bot.send_message(chat_id, f"🦅 **{mode}** | Phiên: `{phien}`\n🔮 Dự đoán: **{icon}**", parse_mode="Markdown")
        except: pass
        time.sleep(12)

# ================= MENU ADMIN =================
def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Thống Kê", callback_data="ad_stats"),
        types.InlineKeyboardButton("➕ Cộng VIP", callback_data="ad_add"),
        types.InlineKeyboardButton("📢 Thông Báo", callback_data="ad_msg")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "👑 **ADMIN CONTROL PANEL**", reply_markup=admin_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('ad_'))
def callback_admin(call):
    if call.data == "ad_stats":
        bot.send_message(call.message.chat.id, f"👥 Tổng User trong DB: {len(users_db)}")
    elif call.data == "ad_add":
        m = bot.send_message(call.message.chat.id, "👉 Nhập: `ID SO_NGAY` (VD: `7816353760 30`)")
        bot.register_next_step_handler(m, process_ad_add)
    elif call.data == "ad_msg":
        m = bot.send_message(call.message.chat.id, "📣 Nhập thông báo gửi toàn bot:")
        bot.register_next_step_handler(m, process_ad_broadcast)

def process_ad_add(message):
    try:
        uid, days = message.text.split()
        if uid not in users_db: users_db[uid] = {'expire_date': None, 'is_running': False}
        now = datetime.now()
        start = users_db[uid]['expire_date'] if users_db[uid]['expire_date'] and users_db[uid]['expire_date'] > now else now
        users_db[uid]['expire_date'] = start + timedelta(days=int(days))
        save_data()
        bot.send_message(message.chat.id, f"✅ Đã cộng {days} ngày cho `{uid}`")
        bot.send_message(uid, f"🎁 **ADMIN TẶNG VIP:** Bạn được cộng thêm `{days} ngày VIP`!")
    except: bot.send_message(message.chat.id, "❌ Lỗi định dạng.")

def process_ad_broadcast(message):
    count = 0
    for uid in users_db:
        try:
            bot.send_message(uid, f"🔔 **THÔNG BÁO TỪ ADMIN:**\n\n{message.text}")
            count += 1
        except: continue
    bot.send_message(message.chat.id, f"✅ Đã gửi tới {count} người.")

# ================= KHỞI CHẠY =================
if __name__ == "__main__":
    # Chạy Web Server cho Render
    threading.Thread(target=run_web_server, daemon=True).start()
    # Chạy Quét Bank Tự Động
    threading.Thread(target=check_bank_auto, daemon=True).start()
    print("✅ Bot đã sẵn sàng!")
    bot.infinity_polling()
                
