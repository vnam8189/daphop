import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os, asyncio, re, random, logging, json
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG (THAY ID TẠI ĐÂY)
# ==========================================
API_TOKEN = '8475867709:AAGPINZGRgMnZBRDpNZWPGgBof0fY8N-0D4'
API_ID = 36437338
API_HASH = "18d34c7efc396d277f3db62baa078efc"

ADMIN_CHINH = [7816353760]  # ID Boss (Toàn quyền quản lý nhóm, thông báo)
ADMIN_PHU = [6472034224]              # ID CTV (Chỉ được nạp acc và xem mem)

MONEY_PER_REF = 3500   
COST_PER_CODE = 10000  
BOT_GAME_TARGET = "xocdia88_bot_uytin_bot"
SESSION_FILE = "sessions.txt"
DB_FILE = "database.json"

# ==========================================
# 2. XỬ LÝ DATABASE (LƯU TRỮ TRÁNH MẤT DỮ LIỆU)
# ==========================================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {}, 
        "codes": [],
        "channels": ['@kiemtienonline48h'],
        "game_link": "https://xocdia88.ec"
    }

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

db = load_db()
PENDING_LOGINS = {}
ACCS = {}
admin_states = {}

bot = telebot.TeleBot(API_TOKEN)
telethon_loop = asyncio.new_event_loop()

# ==========================================
# 3. WORKER CLONE (AUTO SĂN CODE)
# ==========================================
def make_grab_handler(client, name):
    async def handler(ev):
        if ev.reply_markup:
            btn = next((b for r in ev.reply_markup.rows for b in r.buttons if "đập" in b.text.lower()), None)
            if btn:
                await asyncio.sleep(random.uniform(0.1, 0.4))
                try:
                    await ev.click()
                    await asyncio.sleep(2.0)
                    msgs = await client.get_messages(BOT_GAME_TARGET, limit=1)
                    if msgs and msgs[0].message:
                        match = re.search(r'là:\s*([A-Z0-9]+)', msgs[0].message)
                        if match:
                            code = match.group(1)
                            if code not in db["codes"]:
                                db["codes"].append(code)
                                save_db()
                                for adm in (ADMIN_CHINH + ADMIN_PHU):
                                    bot.send_message(adm, f"🎊 **HÚP ĐƯỢC CODE:** `{code}`\n👤 Nguồn: {name}", parse_mode="Markdown")
                except: pass
    return handler

async def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            for line in f.read().splitlines():
                if not line.strip(): continue
                try:
                    c = TelegramClient(StringSession(line), API_ID, API_HASH)
                    await c.connect()
                    if await c.is_user_authorized():
                        me = await c.get_me()
                        ACCS[me.first_name] = c
                        c.add_event_handler(make_grab_handler(c, me.first_name), events.NewMessage(chats=BOT_GAME_TARGET))
                except: pass

# ==========================================
# 4. GIAO DIỆN MENU HỆ THỐNG
# ==========================================
def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Thống Kê", "🎁 Rút Giftcode")
    markup.add("🔗 Link Mời", "🎮 Link Game")
    if uid in ADMIN_CHINH or uid in ADMIN_PHU:
        markup.add("🛠 Admin Panel", "📱 Dàn Clone")
        markup.add("➕ Thêm Clone")
    return markup

def admin_panel_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if uid in ADMIN_CHINH:
        markup.add("📢 Gửi Thông Báo", "📢 Quản Lý Nhóm")
    markup.add("👥 Danh Sách Mem", "🔙 Quay Lại")
    return markup

def group_manage_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Thêm Nhóm", "➖ Xóa Nhóm")
    markup.add("🔙 Quay Lại Admin")
    return markup

# ==========================================
# 5. XỬ LÝ SỰ KIỆN CHÍNH
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in db["users"]:
        args = message.text.split()
        referrer = args[1] if len(args) > 1 and args[1].isdigit() else None
        db["users"][uid] = {'balance': 0, 'invited_by': referrer, 'refs': 0, 'verified': False}
        save_db()
    
    if not db["users"][uid]['verified']:
        list_groups = "\n".join([f"🔹 {c}" for c in db["channels"]])
        msg = f"👋 **Chào mừng bạn!**\n\nĐể sử dụng Bot, bạn cần tham gia:\n{list_groups}"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Xác Minh Ngay")
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "✨ Hệ thống đã sẵn sàng!", reply_markup=main_menu(int(uid)))

@bot.message_handler(func=lambda msg: True)
def handle_all(message):
    uid_int = message.from_user.id
    uid = str(uid_int)
    text = message.text
    state = admin_states.get(uid_int)

    # --- XỬ LÝ TRẠNG THÁI (STATES) ---
    if state == "WAIT_PHONE":
        if text == "❌ Huỷ": admin_states.pop(uid_int); return bot.send_message(uid_int, "Đã huỷ", reply_markup=main_menu(uid_int))
        bot.send_message(uid_int, "⏳ Đang gửi yêu cầu OTP...")
        async def ask_code():
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            try:
                sent = await client.send_code_request(text)
                PENDING_LOGINS[uid_int] = {"p": text, "h": sent.phone_code_hash, "c": client}
                admin_states[uid_int] = "WAIT_OTP"
                bot.send_message(uid_int, "📩 **Nhập mã OTP (5 số):**", parse_mode="Markdown")
            except Exception as e: 
                bot.send_message(uid_int, f"❌ Lỗi: {e}")
                admin_states.pop(uid_int)
        asyncio.run_coroutine_threadsafe(ask_code(), telethon_loop); return

    if state == "WAIT_OTP":
        data = PENDING_LOGINS.get(uid_int)
        async def confirm():
            try:
                await data["c"].sign_in(data["p"], text, phone_code_hash=data["h"])
                ss = data["c"].session.save()
                with open(SESSION_FILE, "a") as f: f.write(ss + "\n")
                me = await data["c"].get_me()
                ACCS[me.first_name] = data["c"]
                data["c"].add_event_handler(make_grab_handler(data["c"], me.first_name), events.NewMessage(chats=BOT_GAME_TARGET))
                bot.send_message(uid_int, f"✅ Thành công! {me.first_name} đang online.", reply_markup=main_menu(uid_int))
            except Exception as e: bot.send_message(uid_int, f"❌ Lỗi: {e}")
            admin_states.pop(uid_int)
        asyncio.run_coroutine_threadsafe(confirm(), telethon_loop); return

    if state == "WAIT_ADD_GROUP" and uid_int in ADMIN_CHINH:
        db["channels"].append(text)
        save_db()
        admin_states.pop(uid_int)
        return bot.send_message(uid_int, f"✅ Đã thêm {text}", reply_markup=group_manage_menu())

    if state == "WAIT_DEL_GROUP" and uid_int in ADMIN_CHINH:
        if text in db["channels"]: db["channels"].remove(text); save_db()
        admin_states.pop(uid_int)
        return bot.send_message(uid_int, f"✅ Đã xoá {text}", reply_markup=group_manage_menu())

    if state == "WAIT_BROADCAST" and uid_int in ADMIN_CHINH:
        admin_states.pop(uid_int)
        for u in db["users"].keys():
            try: bot.send_message(u, f"📢 **THÔNG BÁO:**\n\n{text}", parse_mode="Markdown")
            except: pass
        return bot.send_message(uid_int, "✅ Đã gửi xong!", reply_markup=admin_panel_menu(uid_int))

    # --- XỬ LÝ NÚT BẤM ---
    if text == "✅ Xác Minh Ngay":
        for channel in db["channels"]:
            try:
                if bot.get_chat_member(channel, uid_int).status in ['left', 'kicked']:
                    return bot.reply_to(message, f"❌ Bạn chưa join: {channel}")
            except: pass
        db["users"][uid]['verified'] = True
        ref_id = db["users"][uid].get('invited_by')
        if ref_id and str(ref_id) in db["users"]:
            db["users"][str(ref_id)]['balance'] += MONEY_PER_REF
            db["users"][str(ref_id)]['refs'] += 1
        save_db()
        bot.send_message(uid_int, "✅ Xác minh thành công!", reply_markup=main_menu(uid_int))

    elif text == "📊 Thống Kê":
        u = db["users"].get(uid, {'balance': 0, 'refs': 0})
        bot.send_message(uid_int, f"👤 **TÀI KHOẢN**\n💰 Số dư: **{u['balance']:,}đ**\n👫 Đã mời: `{u['refs']}`", parse_mode="Markdown")

    elif text == "🎁 Rút Giftcode":
        u = db["users"].get(uid)
        if u['balance'] < COST_PER_CODE: return bot.send_message(uid_int, "❌ Thiếu tiền (Cần 10.000đ)")
        if not db["codes"]: return bot.send_message(uid_int, "📭 Hết code rồi!")
        code = db["codes"].pop(0)
        u['balance'] -= COST_PER_CODE
        save_db()
        bot.send_message(uid_int, f"🎁 Giftcode của bạn: `{code}`", parse_mode="Markdown")

    elif text == "🔗 Link Mời":
        bot.send_message(uid_int, f"🔗 Link: `https://t.me/{bot.get_me().username}?start={uid}`\n🎁 Nhận **{MONEY_PER_REF:,}đ** khi bạn bè xác minh.")

    elif text == "🛠 Admin Panel" and (uid_int in ADMIN_CHINH or uid_int in ADMIN_PHU):
        bot.send_message(uid_int, f"🛠 **QUẢN TRỊ**\n📦 Code trong kho: {len(db['codes'])}", reply_markup=admin_panel_menu(uid_int))

    elif text == "📢 Quản Lý Nhóm" and uid_int in ADMIN_CHINH:
        bot.send_message(uid_int, "📝 Danh sách nhóm:\n" + "\n".join(db["channels"]), reply_markup=group_manage_menu())

    elif text == "➕ Thêm Nhóm" and uid_int in ADMIN_CHINH:
        admin_states[uid_int] = "WAIT_ADD_GROUP"
        bot.send_message(uid_int, "Nhập Username nhóm (VD: @tennhom):", reply_markup=types.ReplyKeyboardRemove())

    elif text == "➖ Xóa Nhóm" and uid_int in ADMIN_CHINH:
        admin_states[uid_int] = "WAIT_DEL_GROUP"
        bot.send_message(uid_int, "Nhập chính xác Username cần xoá:", reply_markup=types.ReplyKeyboardRemove())

    elif text == "📢 Gửi Thông Báo" and uid_int in ADMIN_CHINH:
        admin_states[uid_int] = "WAIT_BROADCAST"
        bot.send_message(uid_int, "Nhập nội dung thông báo:", reply_markup=types.ReplyKeyboardRemove())

    elif text == "➕ Thêm Clone" and (uid_int in ADMIN_CHINH or uid_int in ADMIN_PHU):
        admin_states[uid_int] = "WAIT_PHONE"
        bot.send_message(uid_int, "📱 Nhập SĐT (VD: 849xxx):", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Huỷ"))

    elif text == "📱 Dàn Clone":
        msg = "📱 Workers: " + ", ".join(ACCS.keys()) if ACCS else "Chưa có clone."
        bot.send_message(uid_int, msg)

    elif text == "👥 Danh Sách Mem" and (uid_int in ADMIN_CHINH or uid_int in ADMIN_PHU):
        bot.send_message(uid_int, f"👥 Tổng mem: `{len(db['users'])}`")

    elif text == "🔙 Quay Lại Admin": bot.send_message(uid_int, "Menu Admin", reply_markup=admin_panel_menu(uid_int))
    elif text == "🔙 Quay Lại": bot.send_message(uid_int, "Menu Chính", reply_markup=main_menu(uid_int))

# ==========================================
# 6. RUN
# ==========================================
if __name__ == "__main__":
    t = Thread(target=lambda: (asyncio.set_event_loop(telethon_loop), telethon_loop.run_until_complete(load_sessions()), telethon_loop.run_forever()))
    t.start()
    app = Flask('')
    @app.route('/')
    def home(): return "Bot Live"
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    print("🚀 BOT ĐÃ SẴN SÀNG!")
    bot.infinity_polling()
                    
