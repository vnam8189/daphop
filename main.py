import telebot
import requests
import time
import threading
import json
import os
from datetime import datetime, timedelta
from telebot import types
from flask import Flask

# ================= CẤU HÌNH SERVER (GIỮ BOT LUÔN SỐNG TRÊN RENDER) =================
app = Flask(__name__)
@app.route('/')
def home(): return "<h1>BOT VIP XOCDIA IS RUNNING!</h1>"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ================= CẤU HÌNH BOT & API =================
API_TOKEN = '8404770438:AAHNI8xRHFlWPVNF4gL2-CShnvqgQ_OXUEI'
ADMIN_ID = 7816353760 

# API Ngân hàng & Game
BANK_API_URL = "https://spayment.net/msb-history?history=80002422042"
API_TX = "https://xd88-apsj.onrender.com/xd88/tx"
API_MD5 = "https://xd88-apsj.onrender.com/xd88/md5"
DB_FILE = 'users_db.json'

bot = telebot.TeleBot(API_TOKEN)

# ================= QUẢN LÝ DỮ LIỆU NGƯỜI DÙNG =================
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

# ================= TỰ ĐỘNG CỘNG TIỀN MSB =================
def check_bank_auto():
    processed_txns = []
    while True:
        try:
            res = requests.get(BANK_API_URL, timeout=15).json()
            transactions = res if isinstance(res, list) else res.get('data', [])

            for tr in transactions:
                # Xử lý số tiền từ chuỗi (Ví dụ: "2.000 VNĐ" -> 2000)
                amount_raw = str(tr.get('so_tien') or tr.get('amount', '0'))
                amount = int(amount_raw.replace('.', '').replace(' VNĐ', '').strip())
                desc = str(tr.get('noi_dung') or tr.get('description', '')).upper()
                tid = str(tr.get('ma_gd') or tr.get('transactionId', ''))

                if amount > 0 and tid not in processed_txns:
                    if "NAP" in desc:
                        try:
                            target_id = desc.split("NAP")[1].strip().split()[0]
                            target_id = ''.join(filter(str.isdigit, target_id))

                            if target_id in users_db:
                                days = 0
                                if amount >= 120000: days = 999
                                elif amount >= 60000: days = 14
                                elif amount >= 30000: days = 7
                                
                                if days > 0:
                                    now = datetime.now()
                                    start = users_db[target_id]['expire_date']
                                    if not start or start < now: start = now
                                    users_db[target_id]['expire_date'] = start + timedelta(days=days)
                                    save_data()
                                    processed_txns.append(tid)

                                    bot.send_message(target_id, f"✅ **NẠP THÀNH CÔNG {amount:,}đ**\n🎁 Đã cộng {days} ngày VIP!")
                                    bot.send_message(ADMIN_ID, f"💰 **AUTO BANK:** ID `{target_id}` nạp {amount:,}đ.")
                        except: continue
        except: pass
        time.sleep(25)

# ================= MENU ADMIN CHUYÊN NGHIỆP =================
def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Thống Kê", callback_data="admin_stats"),
        types.InlineKeyboardButton("➕ Cộng VIP", callback_data="admin_add_vip"),
        types.InlineKeyboardButton("📢 Thông Báo", callback_data="admin_broadcast")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    total = len(users_db)
    active = sum(1 for u in users_db if users_db[u]['expire_date'] and users_db[u]['expire_date'] > datetime.now())
    msg = f"👑 **ADMIN CONTROL PANEL**\n━━━━━━━━━━━━━\n👥 Tổng User: `{total}`\n🌟 Đang VIP: `{active}`"
    bot.send_message(message.chat.id, msg, reply_markup=admin_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callbacks(call):
    if call.data == "admin_stats":
        msg = "📋 **DANH SÁCH VIP:**\n"
        for uid, info in users_db.items():
            if info['expire_date'] and info['expire_date'] > datetime.now():
                msg += f"• `{uid}`: {info['expire_date'].strftime('%d/%m/%Y')}\n"
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    
    elif call.data == "admin_add_vip":
        msg = bot.send_message(call.message.chat.id, "👉 Nhập: `ID_USER SO_NGAY` (Ví dụ: `7816353760 30`)")
        bot.register_next_step_handler(msg, process_ad_add)

    elif call.data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📣 Nhập nội dung thông báo gửi toàn bộ user:")
        bot.register_next_step_handler(msg, process_ad_broadcast)

def process_ad_add(message):
    try:
        uid, days = message.text.split()
        days = int(days)
        if uid not in users_db: users_db[uid] = {'expire_date': None, 'is_running': False}
        now = datetime.now()
        start = users_db[uid]['expire_date'] if users_db[uid]['expire_date'] and users_db[uid]['expire_date'] > now else now
        users_db[uid]['expire_date'] = start + timedelta(days=days)
        save_data()
        bot.send_message(message.chat.id, f"✅ Đã cộng {days} ngày cho `{uid}`")
        bot.send_message(uid, f"🎁 Admin đã tặng bạn {days} ngày VIP!")
    except: bot.send_message(message.chat.id, "⚠️ Lỗi định dạng.")

def process_ad_broadcast(message):
    count = 0
    for uid in users_db:
        try:
            bot.send_message(uid, f"📣 **THÔNG BÁO ADMIN:**\n\n{message.text}")
            count += 1
        except: continue
    bot.send_message(message.chat.id, f"✅ Đã gửi cho {count} người.")

# ================= CHỨC NĂNG NGƯỜI DÙNG =================
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
    bot.send_message(message.chat.id, "🦅 **BOT XOCDIA88 PREDICT** 🦅", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = str(message.from_user.id)
    if message.text == '👤 TÀI KHOẢN':
        exp = users_db.get(uid, {}).get('expire_date')
        status = "🟢 VIP ACTIVE" if exp and exp > datetime.now() else "🔴 HẾT HẠN"
        d = exp.strftime("%d/%m/%Y %H:%M") if exp else "Chưa ĐK"
        bot.send_message(message.chat.id, f"🆔 ID: `{uid}`\nTrạng thái: {status}\nHạn dùng: {d}", parse_mode="Markdown")

    elif message.text == '💳 NẠP VIP':
        bot.send_message(message.chat.id, f"🏦 **NẠP TỰ ĐỘNG MSB**\nSTK: `80002422042`\nNội dung: `NAP {uid}`\n(Hệ thống tự duyệt sau 30s)")

    elif "SOI CẦU" in message.text:
        exp = users_db.get(uid, {}).get('expire_date')
        if not exp or exp < datetime.now():
            return bot.send_message(message.chat.id, "❌ Bạn cần Nạp VIP để dùng chức năng này.")
        
        mode = "THƯỜNG" if "XÓC ĐĨA" in message.text else "MD5"
        url = API_TX if mode == "THƯỜNG" else API_MD5
        users_db[uid]['is_running'] = True
        bot.send_message(message.chat.id, f"🚀 Khởi động AI {mode}...")
        threading.Thread(target=auto_predict, args=(message.chat.id, uid, url, mode), daemon=True).start()

    elif message.text == '🛑 DỪNG TOOL':
        if uid in users_db: users_db[uid]['is_running'] = False
        bot.send_message(message.chat.id, "🛑 Đã dừng tool.")

def auto_predict(chat_id, uid, api_url, mode_name):
    last_phien = ""
    while users_db.get(uid, {}).get('is_running'):
        try:
            res = requests.get(api_url, timeout=10).json()
            phien = str(res.get('phien', ''))
            if phien != last_phien:
                last_phien = phien
                du_doan = str(res.get('du doan') or res.get('du_doan', 'N/A')).upper()
                icon = "🔴 CHẴN" if "CHẴN" in du_doan or "TÀI" in du_doan else "⚪ LẺ"
                bot.send_message(chat_id, f"🦅 {mode_name} | Phiên: {phien}\n🔮 Dự đoán: **{icon}**", parse_mode="Markdown")
        except: pass
        time.sleep(12)

# ================= CHẠY BOT =================
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=check_bank_auto, daemon=True).start()
    print("✅ Bot đang chạy...")
    bot.infinity_polling()
        
