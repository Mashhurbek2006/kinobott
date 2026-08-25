import telebot
import json
import os
import database
from telebot import custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

database.init_db()

TOKEN = os.environ.get("BOT_TOKEN", "8822651236:AAG8hnN1ZOb6e8dnqW5fPhsik-3BFpq5_GY")
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)
BOT_USERNAME = None

ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "5469081053").split(",")))

# --- BACKUP KANAL TIZIMI ---
BACKUP_CHANNEL_LINK = "https://t.me/+zHIC33VrEBY5YjRi"
BACKUP_ID_FILE = "backup_channel_id.txt"

def get_backup_channel_id():
    """Backup kanal ID sini fayldan o'qish."""
    try:
        with open(BACKUP_ID_FILE, 'r') as f:
            return int(f.read().strip())
    except:
        return None

def save_backup_channel_id(chat_id):
    """Backup kanal ID sini faylga saqlash."""
    with open(BACKUP_ID_FILE, 'w') as f:
        f.write(str(chat_id))

def backup_to_channel():
    """Barcha ma'lumotlarni JSON fayl sifatida backup kanalga yuborish va pin qilish."""
    channel_id = get_backup_channel_id()
    if not channel_id:
        return
    try:
        data = database.export_all_data()
        backup_content = json.dumps(data, ensure_ascii=False, indent=2)
        with open("backup.json", 'w', encoding='utf-8') as f:
            f.write(backup_content)
        with open("backup.json", 'rb') as f:
            import datetime
            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            msg = bot.send_document(channel_id, f, caption=f"\U0001f4e6 Bot zaxira nusxasi\n\U0001f4c5 {now}")
        try:
            bot.pin_chat_message(channel_id, msg.message_id, disable_notification=True)
        except:
            pass
    except Exception as e:
        print(f"Backup xatolik: {e}")

def restore_from_channel():
    """Backup kanalning pin qilingan xabaridagi JSON fayldan bazani tiklash."""
    channel_id = get_backup_channel_id()
    if not channel_id:
        return False
    try:
        chat = bot.get_chat(channel_id)
        if not chat.pinned_message or not chat.pinned_message.document:
            return False
        file_info = bot.get_file(chat.pinned_message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        data = json.loads(downloaded.decode('utf-8'))
        database.import_all_data(data)
        print(f"\u2705 Backup kanaldan tiklandi: {len(data.get('movies', []))} kino, {len(data.get('channels', []))} kanal, {len(data.get('users', []))} foydalanuvchi")
        return True
    except Exception as e:
        print(f"Restore xatolik: {e}")
        return False

# Startup: agar baza bo'sh bo'lsa, backup kanaldan tiklash
if database.get_movie_count() == 0 and database.get_user_count() == 0:
    print("Baza bo'sh, backup kanaldan tiklash urinilmoqda...")
    if restore_from_channel():
        print("Ma'lumotlar muvaffaqiyatli tiklandi!")
    else:
        print("Backup topilmadi yoki backup kanal sozlanmagan.")

TOKEN = os.environ.get("BOT_TOKEN", "8822651236:AAGMsIFclDnsf5V6CS5xZWWWD0OoDtUSozI")
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)
# Retrieve bot username once for link generation (will be set lazily)
BOT_USERNAME = None


ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "5469081053").split(",")))

class BackupChannelState(StatesGroup):
    forward = State()

class MovieState(StatesGroup):
    code = State()
    name = State()
    lang = State()
    quality = State()

class SearchState(StatesGroup):
    code = State()

class ChannelState(StatesGroup):
    chat_id = State()
    name = State()
    url = State()
    style = State()
    emoji_id = State()

class BroadcastState(StatesGroup):
    message = State()

class RemoveChannelState(StatesGroup):
    chat_id = State()

class SupportState(StatesGroup):
    username = State()
    text = State()

def premium_emoji(emoji_id, fallback="👍"):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def colorful_reply_button(text, style="default", emoji_id=None):
    btn = {"text": text, "style": style}
    if emoji_id:
        btn["icon_custom_emoji_id"] = emoji_id
    return btn

def get_main_menu():
    keyboard = [
        [colorful_reply_button("Kino Qidirish", "primary", "5231012545799666522"), colorful_reply_button("Saqlanganlar", "success", "5253742260054409879")],
        [colorful_reply_button("Yordam", "danger", "5334544901428229844")]
    ]
    return json.dumps({"keyboard": keyboard, "resize_keyboard": True})

def get_cancel_keyboard():
    keyboard = [[colorful_reply_button("❌ Bekor qilish", "danger")]]
    return json.dumps({"keyboard": keyboard, "resize_keyboard": True})

def get_admin_keyboard():
    keyboard = [
        [colorful_reply_button("\U0001f4e2 Majburiy obuna", "danger"), colorful_reply_button("\u2699\ufe0f Yordam tugmasi", "primary")],
        [colorful_reply_button("\U0001f4ca Statistika", "primary"), colorful_reply_button("\u2709\ufe0f Rassilka", "success")],
        [colorful_reply_button("\U0001f3ac Yangi kino", "danger"), colorful_reply_button("\U0001f3ac Kinolar ro'yxati", "primary")],
        [colorful_reply_button("\U0001f4e6 Backup kanal", "success"), colorful_reply_button("\U0001f3e0 Asosiy menyu", "default")]
    ]
    return json.dumps({"keyboard": keyboard, "resize_keyboard": True})

def get_admin_channels_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Kanal qo'shish", callback_data="admin_add_ch"),
        InlineKeyboardButton("➖ Kanal o'chirish", callback_data="admin_rem_ch"),
        InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_ch")
    )
    return markup

def get_movie_keyboard(code, user_id=None):
    markup = {
        "inline_keyboard": [
            [
                {"text": "💾 Saqlash", "callback_data": f"save_{code}", "style": "success"}
            ]
        ]
    }
    return json.dumps(markup)


# --- MAJBURIY OBUNA TEKSHIRUVI ---
def check_subscription(user_id):
    if user_id in ADMIN_IDS: return []
    channels = database.get_channels()
    not_subscribed = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch['chat_id'], user_id)
            if member.status in ['left', 'kicked']:
                if not database.has_join_request(user_id, ch['chat_id']):
                    not_subscribed.append(ch)
        except Exception as e:
            print(f"Error checking sub for {ch['chat_id']}: {e}")
            if not database.has_join_request(user_id, ch['chat_id']):
                not_subscribed.append(ch)
    return not_subscribed

def send_subscription_warning(chat_id, not_subscribed):
    inline_keyboard = []
    for ch in not_subscribed:
        btn = {"text": ch['name'], "url": ch['url']}
        if ch.get('style'):
            btn["style"] = ch['style']
        if ch.get('emoji_id') and ch['emoji_id'] != "0":
            btn["icon_custom_emoji_id"] = ch['emoji_id']
        inline_keyboard.append([btn])
    inline_keyboard.append([{"text": "Tekshirish", "callback_data": "check_sub", "style": "success", "icon_custom_emoji_id": "6296367896398399651"}])
    
    markup = json.dumps({"inline_keyboard": inline_keyboard})
    text = f"{premium_emoji('6296341890371422476', '❗️')} Kechirasiz, botimizdan to‘liq foydalanish uchun quyidagi kanallarga a‘zo bo‘ling {premium_emoji('6296303781126604562', '👇')}"
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

@bot.chat_join_request_handler(func=lambda request: True)
def handle_join_request(request):
    print(f"Zayavka tushdi: User {request.from_user.id} -> Chat {request.chat.id}")
    database.add_join_request(request.from_user.id, request.chat.id)

def handle_start_deep_link(message):
    text = message.text or ""
    parts = text.split()
    if len(parts) < 2:
        return False
    token = parts[1]
    if token.startswith('movie_'):
        code = token.split('_', 1)[1]
        user_id = message.from_user.id
        not_subscribed = check_subscription(user_id)
        if not_subscribed:
            send_subscription_warning(message.chat.id, not_subscribed)
            return True
        movie = database.get_movie(code)
        if movie:
            caption = f"🎬 Nomi: <b>{movie['name']}</b>\n🇺🇿 Til: <b>{movie['lang']}</b>\n🎞 Sifati: <b>{movie['quality']}</b>"
            try:
                bot.send_video(message.chat.id, movie['file_id'], caption=caption, parse_mode="HTML", reply_markup=get_movie_keyboard(code), protect_content=True)
            except Exception:
                bot.send_message(message.chat.id, "Kino yuborishda xatolik: Video yaroqsiz.")
        else:
            bot.send_message(message.chat.id, "❌ Bunday kod bilan kino topilmadi.")
        return True
    return False

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "👨‍💻 <b>Admin panelga xush kelibsiz!</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())

@bot.message_handler(commands=['start'])
def start_handler(message):
    if not handle_start_deep_link(message):
        user_first = message.from_user.first_name
        bot.send_message(message.chat.id,
                         f"Salom, <b>{user_first}</b>! Botga hush kelibsiz.",
                         parse_mode="HTML",
                         reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def check_sub_callback(call):
    not_subscribed = check_subscription(call.from_user.id)
    if not not_subscribed:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Tabriklaymiz endi botdan toliq foydalanishingiz mumkin", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "Kechirasiz kanallarga toliq obuna bolmagansz", show_alert=True)

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(message.chat.id, "✉️ Xabarni kiriting (barcha foydalanuvchilarga yuboriladi):", reply_markup=get_cancel_keyboard())
    bot.set_state(message.from_user.id, BroadcastState.message, message.chat.id)

@bot.message_handler(state=BroadcastState.message)
def send_broadcast(message):
    text = message.text
    if text == "❌ Bekor qilish":
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "Xabar yuborish bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    user_ids = database.get_all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ Xabar {sent} foydalanuvchiga yuborildi.", reply_markup=get_admin_keyboard())
    bot.delete_state(message.from_user.id, message.chat.id)

# --- ADMIN CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_') or call.data.startswith('sup_') or call.data.startswith('bkp_'))
def admin_channels_callback(call):
    if call.from_user.id not in ADMIN_IDS: return
    # --- BACKUP KANAL ---
    if call.data == "bkp_set":
        bot.send_message(call.message.chat.id, "\U0001f4e4 Backup kanaldan istalgan xabarni menga FORWARD (uzatib) yuboring:", reply_markup=get_cancel_keyboard())
        bot.set_state(call.from_user.id, BackupChannelState.forward, call.message.chat.id)
    elif call.data == "bkp_now":
        backup_id = get_backup_channel_id()
        if not backup_id:
            bot.answer_callback_query(call.id, "\u274c Avval backup kanalni sozlang!", show_alert=True)
            return
        backup_to_channel()
        bot.answer_callback_query(call.id, "\u2705 Backup muvaffaqiyatli yuborildi!", show_alert=True)
    elif call.data == "bkp_restore":
        backup_id = get_backup_channel_id()
        if not backup_id:
            bot.answer_callback_query(call.id, "\u274c Avval backup kanalni sozlang!", show_alert=True)
            return
        if restore_from_channel():
            bot.answer_callback_query(call.id, "\u2705 Ma'lumotlar backupdan tiklandi!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "\u274c Backupda ma'lumot topilmadi!", show_alert=True)
    # --- YORDAM ---
    elif call.data == "sup_del":
        database.delete_setting("support_username")
        database.delete_setting("support_text")
        bot.answer_callback_query(call.id, "🗑 Yordam ma'lumotlari o'chirildi!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "sup_edit":
        bot.send_message(call.message.chat.id, "Yordam beruvchi adminning username'ini kiriting (masalan: kinolas_admin):", reply_markup=get_cancel_keyboard())
        bot.set_state(call.from_user.id, SupportState.username, call.message.chat.id)
    elif call.data == "admin_add_ch":
        bot.send_message(call.message.chat.id, "Kanalning ID raqamini (yoki @username) kiriting:\n\n💡 <i>Maslahat: Agar kanal maxfiy bo'lsa va ID sini bilmasangiz, shunchaki u yerdagi biron xabarni menga FORWARD (uzatib) yuboring!</i>", parse_mode="HTML")
        bot.set_state(call.from_user.id, ChannelState.chat_id, call.message.chat.id)
    elif call.data == "admin_rem_ch":
        bot.send_message(call.message.chat.id, "O'chirmoqchi bo'lgan kanal ID sini kiriting:")
        bot.set_state(call.from_user.id, RemoveChannelState.chat_id, call.message.chat.id)
    elif call.data == "admin_list_ch":
        channels = database.get_channels()
        if not channels:
            bot.send_message(call.message.chat.id, "Kanallar yo'q.")
            return
        text = "📋 <b>Majburiy kanallar ro'yxati:</b>\n\n"
        for idx, ch in enumerate(channels, 1):
            if ch.get('emoji_id') and ch['emoji_id'] != "0":
                emoji_html = premium_emoji(ch['emoji_id'], "🌟")
                text += f"{idx}. {emoji_html} <b>{ch['name']}</b> (<code>{ch['chat_id']}</code>)\n"
            else:
                text += f"{idx}. <b>{ch['name']}</b> (<code>{ch['chat_id']}</code>)\n"
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")

@bot.message_handler(state=ChannelState.chat_id, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def add_ch_id(message):
    chat_id = message.text
    if message.forward_from_chat and message.forward_from_chat.type == 'channel':
        chat_id = str(message.forward_from_chat.id)
        
    if not chat_id:
        bot.send_message(message.chat.id, "Iltimos, kanal ID sini matn orqali yozing yoki kanaldan xabar forward qiling.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data: 
        data['chat_id'] = chat_id
    bot.send_message(message.chat.id, f"✅ Qabul qilindi: <b>{chat_id}</b>\n\nEndi kanalning tugmada chiqadigan nomini kiriting:", parse_mode="HTML")
    bot.set_state(message.from_user.id, ChannelState.name, message.chat.id)

@bot.message_handler(state=ChannelState.name)
def add_ch_name(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data: data['name'] = message.text
    bot.send_message(message.chat.id, "Endi kanalning invite ssilkasini kiriting (https://t.me/...):")
    bot.set_state(message.from_user.id, ChannelState.url, message.chat.id)

@bot.message_handler(state=ChannelState.url)
def add_ch_url(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data: data['url'] = message.text
    bot.send_message(message.chat.id, "Tugma qaysi rangda chiqishini xohlaysiz? Yozib yuboring (masalan: primary, success, danger, default):")
    bot.set_state(message.from_user.id, ChannelState.style, message.chat.id)

@bot.message_handler(state=ChannelState.style)
def add_ch_style(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data: data['style'] = message.text
    bot.send_message(message.chat.id, "Premium Emoji ID kiriting (Agar yo'q bo'lsa yoki kerak bo'lmasa `0` deb yozing):", parse_mode="Markdown")
    bot.set_state(message.from_user.id, ChannelState.emoji_id, message.chat.id)

@bot.message_handler(state=ChannelState.emoji_id)
def add_ch_emoji_id(message):
    emoji_id = "" if message.text == "0" else message.text
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        database.add_channel(data['chat_id'], data['name'], data['url'], data['style'], emoji_id)
    
    if emoji_id:
        emoji_html = premium_emoji(emoji_id, "🌟")
        bot.send_message(message.chat.id, f"✅ Kanal bazaga rang va emoji {emoji_html} bilan muvaffaqiyatli qo'shildi!", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "✅ Kanal bazaga rang bilan muvaffaqiyatli qo'shildi!")
        
    bot.delete_state(message.from_user.id, message.chat.id)
    backup_to_channel()

@bot.message_handler(state=RemoveChannelState.chat_id)
def remove_ch_id(message):
    database.remove_channel(message.text)
    bot.send_message(message.chat.id, "\u2705 Kanal o'chirildi (agar mavjud bo'lsa).")
    bot.delete_state(message.from_user.id, message.chat.id)
    backup_to_channel()

@bot.message_handler(state=BackupChannelState.forward, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def set_backup_channel(message):
    if message.text == "\u274c Bekor qilish":
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=get_admin_keyboard())
        bot.delete_state(message.from_user.id, message.chat.id)
        return
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
        save_backup_channel_id(chat_id)
        bot.send_message(message.chat.id, f"\u2705 Backup kanal muvaffaqiyatli sozlandi!\n\nKanal ID: <code>{chat_id}</code>", parse_mode="HTML", reply_markup=get_admin_keyboard())
        bot.delete_state(message.from_user.id, message.chat.id)
    else:
        bot.send_message(message.chat.id, "\u274c Iltimos, backup kanaldan xabarni FORWARD (uzatib) yuboring!")

@bot.message_handler(state=SupportState.username)
def get_support_username(message):
    if message.text == "❌ Bekor qilish":
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=get_admin_keyboard())
        bot.delete_state(message.from_user.id, message.chat.id)
        return
    username = message.text.replace("@", "").strip()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['sup_username'] = username
    bot.send_message(message.chat.id, "Ushbu admin sahifasiga kirganda avtomatik yoziladigan xabarni kiriting (masalan: Assalomu aleykum, yordam kerak!):", reply_markup=get_cancel_keyboard())
    bot.set_state(message.from_user.id, SupportState.text, message.chat.id)

@bot.message_handler(state=SupportState.text)
def get_support_text(message):
    if message.text == "❌ Bekor qilish":
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=get_admin_keyboard())
        bot.delete_state(message.from_user.id, message.chat.id)
        return
    text = message.text
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        database.set_setting("support_username", data['sup_username'])
        database.set_setting("support_text", text)
    bot.send_message(message.chat.id, "\u2705 Yordam tugmasi ma'lumotlari muvaffaqiyatli saqlandi!", reply_markup=get_admin_keyboard())
    bot.delete_state(message.from_user.id, message.chat.id)
    backup_to_channel()

# --- QOLGAN FUNKSIYALAR ---
@bot.channel_post_handler(content_types=['video', 'document'])
def handle_channel_post(message):
    file_id = message.video.file_id if message.video else (message.document.file_id if message.document else None)
    if file_id:
        admin_id = ADMIN_IDS[0]
        bot.send_message(admin_id, "📥 Kanaldan yangi kino/video qabul qilindi!\n\nIltimos, ushbu kino uchun <b>KOD</b> kiriting:", parse_mode="HTML")
        bot.set_state(admin_id, MovieState.code, admin_id)
        with bot.retrieve_data(admin_id, admin_id) as data:
            data['file_id'] = file_id
            data['message_id'] = message.message_id
            data['channel_id'] = message.chat.id

@bot.message_handler(state=MovieState.code)
def get_code(message):
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['code'] = message.text
        bot.send_message(message.chat.id, "Kino nomini yozing:")
        bot.set_state(message.from_user.id, MovieState.name, message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

@bot.message_handler(state=MovieState.name)
def get_name(message):
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['name'] = message.text
        bot.send_message(message.chat.id, "Kino tilini yozing (masalan: O'zbekcha):")
        bot.set_state(message.from_user.id, MovieState.lang, message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

@bot.message_handler(state=MovieState.lang)
def get_lang(message):
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['lang'] = message.text
        bot.send_message(message.chat.id, "Kino sifatini yozing (masalan: 1080p, 720p):")
        bot.set_state(message.from_user.id, MovieState.quality, message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

@bot.message_handler(state=MovieState.quality)
def get_quality(message):
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            code, file_id, name, lang, quality = data['code'], data['file_id'], data['name'], data['lang'], message.text
            database.add_movie(code, file_id, name, lang, quality, data.get('message_id'), data.get('channel_id'))
        bot.send_message(message.chat.id, f"\u2705 <b>Kino bazaga saqlandi!</b>\n\n\U0001f4cc <b>Kod:</b> {code}\n\U0001f3ac <b>Nom:</b> {name}\n\U0001f1fa\U0001f1ff <b>Til:</b> {lang}\n\U0001f39e <b>Sifat:</b> {quality}", parse_mode="HTML")
        bot.delete_state(message.from_user.id, message.chat.id)
        # Backup kanalga videoni yuborish
        backup_id = get_backup_channel_id()
        if backup_id:
            try:
                caption = f"\U0001f4cc Kod: {code}\n\U0001f3ac Nom: {name}\n\U0001f1fa\U0001f1ff Til: {lang}\n\U0001f39e Sifat: {quality}"
                bot.send_video(backup_id, file_id, caption=caption)
            except Exception as e:
                print(f"Backup kanalga video yuborishda xatolik: {e}")
        # JSON backup yangilash
        backup_to_channel()
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

@bot.message_handler(state=SearchState.code)
def search_movie(message):
    user_id = message.from_user.id
    code = message.text

    if code in ["❌ Bekor qilish", "Bekor qilish"]:
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "Kino qidirish bekor qilindi.", reply_markup=get_main_menu())
        return

    not_subscribed = check_subscription(user_id)
    if not_subscribed:
        send_subscription_warning(message.chat.id, not_subscribed)
        bot.delete_state(user_id, message.chat.id)
        return

    movie = database.get_movie(code)
    if movie:
        caption = f"🎬 Nomi: <b>{movie['name']}</b>\n🇺🇿 Tili: <b>{movie['lang']}</b>\n🎞 Sifati: <b>{movie['quality']}</b>"
        try:
            bot.send_video(message.chat.id, movie['file_id'], caption=caption, parse_mode="HTML", reply_markup=get_movie_keyboard(code), protect_content=True)
        except Exception:
            bot.send_message(message.chat.id, "Kino yuborishda xatolik: Video yaroqsiz.")
    else:
        bot.send_message(message.chat.id, "Kechirasiz bunday kodlik kino yo'q.")
    bot.delete_state(message.from_user.id, message.chat.id)

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'), state=None)
def text_handler(message):
    text = message.text
    user_id = message.from_user.id
    database.add_user(user_id)

    if text == "❌ Bekor qilish":
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=get_main_menu())
        bot.delete_state(user_id, message.chat.id)
        return

    if text == "📢 Majburiy obuna" and user_id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Majburiy obuna sozlamalari:", reply_markup=get_admin_channels_menu())
        return

    if text in ["🔍 Kino Qidirish", "💾 Saqlanganlar", "ℹ️ Yordam", "Kino Qidirish", "Saqlanganlar", "Yordam"] or not text.startswith('/'):
        not_subscribed = check_subscription(user_id)
        if not_subscribed:
            send_subscription_warning(message.chat.id, not_subscribed)
            return
            
    if text in ["🔍 Kino Qidirish", "Kino Qidirish"]:
        bot.send_message(message.chat.id, "✍️ Iltimos, topmoqchi bo'lgan kino kodini yozing:", reply_markup=get_cancel_keyboard())
        bot.set_state(message.from_user.id, SearchState.code, message.chat.id)
    elif text in ["💾 Saqlanganlar", "Saqlanganlar"]:
        saved = database.get_saved_movies(user_id)
        if not saved:
            bot.send_message(message.chat.id, "📭 Sizda hozircha saqlangan kinolar yo'q.\n\n💡 Kino topib, <b>💾 Saqlash</b> tugmasini bosing!", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, f"💾 <b>Saqlangan kinolar ({len(saved)} ta):</b>", parse_mode="HTML")
            for movie in saved:
                caption = f"🎬 <b>{movie['name']}</b>\n🇺🇿 Til: {movie['lang']}\n🎞 Sifat: {movie['quality']}\n📌 Kod: <code>{movie['code']}</code>"
                markup = json.dumps({"inline_keyboard": [[{"text": "🗑 O'chirish", "callback_data": f"unsave_{movie['code']}", "style": "danger"}]]})
                try:
                    bot.send_video(message.chat.id, movie['file_id'], caption=caption, parse_mode="HTML", reply_markup=markup, protect_content=True)
                except:
                    bot.send_message(message.chat.id, caption, parse_mode="HTML", reply_markup=markup)
    elif text in ["ℹ️ Yordam", "Yordam"]:
        username = database.get_setting("support_username")
        auto_text = database.get_setting("support_text", "")
        if not username:
            bot.send_message(message.chat.id, "Hozircha admin bilan bog'lanish o'chirilgan.")
        else:
            import urllib.parse
            encoded_text = urllib.parse.quote(auto_text)
            url = f"https://t.me/{username}?text={encoded_text}"
            markup = json.dumps({"inline_keyboard": [[{"text": "👨‍💻 Adminga yozish", "url": url, "style": "primary"}]]})
            bot.send_message(message.chat.id, "Admin bilan bog'lanish uchun quyidagi tugmani bosing:", reply_markup=markup)
    elif text == "\U0001f3e0 Asosiy menyu":
        bot.send_message(message.chat.id, "Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu())
    elif text == "\U0001f4e6 Backup kanal" and user_id in ADMIN_IDS:
        current_id = get_backup_channel_id()
        if current_id:
            status_text = f"\u2705 Backup kanal sozlangan: <code>{current_id}</code>"
        else:
            status_text = "\u274c Backup kanal hali sozlanmagan"
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("\U0001f4e4 Backup kanaldan xabar forward qiling", callback_data="bkp_set"),
            InlineKeyboardButton("\U0001f504 Hozir backup qilish", callback_data="bkp_now"),
            InlineKeyboardButton("\U0001f4e5 Backupdan tiklash", callback_data="bkp_restore")
        )
        msg = f"\U0001f4e6 <b>Backup kanal sozlamalari:</b>\n\n{status_text}\n\U0001f517 Link: {BACKUP_CHANNEL_LINK}\n\n\U0001f4a1 <i>Botni backup kanalga admin qilib qo'shing va quyidagi tugmalardan foydalaning.</i>"
        bot.send_message(message.chat.id, msg, parse_mode="HTML", reply_markup=markup)
    elif text == "⚙️ Yordam tugmasi" and user_id in ADMIN_IDS:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("✏️ Tahrirlash", callback_data="sup_edit"),
            InlineKeyboardButton("🗑 Olib tashlash", callback_data="sup_del")
        )
        current_username = database.get_setting("support_username", "Kiritilmagan")
        current_text = database.get_setting("support_text", "Kiritilmagan")
        msg = f"ℹ️ <b>Yordam tugmasi sozlamalari:</b>\n\n👤 Username: {current_username}\n📝 Avto-matn: {current_text}"
        bot.send_message(message.chat.id, msg, parse_mode="HTML", reply_markup=markup)
    elif text == "✉️ Rassilka" and user_id in ADMIN_IDS:
        bot.send_message(message.chat.id, "✉️ Xabarni kiriting (barcha foydalanuvchilarga yuboriladi):", reply_markup=get_cancel_keyboard())
        bot.set_state(message.from_user.id, BroadcastState.message, message.chat.id)
    elif text == "📊 Statistika" and user_id in ADMIN_IDS:
        total_users = database.get_user_count()
        today_users = database.get_new_user_count(1)
        week_users = database.get_new_user_count(7)
        month_users = database.get_new_user_count(30)
        total_movies = database.get_movie_count()
        total_saved = database.get_total_saved_movies_count()
        total_channels = len(database.get_channels())
        
        import datetime
        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

        stats_msg = (
            f"📊 <b>Bot Statistikasi</b>\n"
            f"📅 <i>Sana: {now}</i>\n\n"
            f"👥 <b>Foydalanuvchilar:</b>\n"
            f" ┣ Barcha: <b>{total_users}</b>\n"
            f" ┣ Bugun: <b>+{today_users}</b>\n"
            f" ┣ Shu hafta: <b>+{week_users}</b>\n"
            f" ┗ Shu oy: <b>+{month_users}</b>\n\n"
            f"🎬 <b>Kino bazasi:</b>\n"
            f" ┣ Jami kinolar: <b>{total_movies}</b>\n"
            f" ┗ Foydalanuvchilar saqlagan: <b>{total_saved}</b> marta\n\n"
            f"📢 <b>Tizim:</b>\n"
            f" ┗ Majburiy kanallar: <b>{total_channels}</b> ta"
        )
        bot.send_message(message.chat.id, stats_msg, parse_mode="HTML")

    elif text == "🎬 Yangi kino" and user_id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Buning uchun bot ulanadigan kanalga yangi video yuboring, bot o'zi sizdan ma'lumotlarni so'raydi!")
    elif text == "🎬 Kinolar ro'yxati" and user_id in ADMIN_IDS:
        movies = database.get_all_movies()
        if not movies:
            bot.send_message(message.chat.id, "📭 Bazada hech qanday kino yo'q.")
        else:
            for m in movies:
                markup = json.dumps({"inline_keyboard": [[{"text": "🗑 O'chirish", "callback_data": f"delm_{m['code']}", "style": "danger"}]]})
                bot.send_message(
                    message.chat.id,
                    f"🎬 <b>{m['name']}</b>\n📌 Kod: <code>{m['code']}</code>\n🇺🇿 Til: {m['lang']} | 🎞 Sifat: {m['quality']}",
                    parse_mode="HTML",
                    reply_markup=markup
                )

@bot.callback_query_handler(func=lambda call: call.data.startswith('save_'))
def save_movie_callback(call):
    not_subscribed = check_subscription(call.from_user.id)
    if not_subscribed:
        bot.answer_callback_query(call.id, "Avval kanallarga obuna bo'ling!", show_alert=True)
        send_subscription_warning(call.message.chat.id, not_subscribed)
        return
    code = call.data.split('_', 1)[1]
    database.save_movie(call.from_user.id, code)
    bot.answer_callback_query(call.id, "✅ Kino saqlanganlarga qo'shildi!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('unsave_'))
def unsave_movie_callback(call):
    code = call.data.split('_', 1)[1]
    database.remove_saved_movie(call.from_user.id, code)
    bot.answer_callback_query(call.id, "🗑 Kino saqlanganlardan o'chirildi!", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('delm_'))
def delete_movie_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Ruxsat yo'q!", show_alert=True)
        return
    code = call.data.split('_', 1)[1]
    database.delete_movie(code)
    bot.answer_callback_query(call.id, f"\u2705 '{code}' kodi bilan kino o'chirildi!", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    # Backup yangilash
    backup_to_channel()

bot.add_custom_filter(custom_filters.StateFilter(bot))

if __name__ == '__main__':
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot ishlayapti!")
        def log_message(self, format, *args):
            pass  # loglarni o'chirish

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Health check server {port}-portda ishga tushdi.")

    print("Kino bot ishga tushdi...")
    import time
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True, allowed_updates=['message', 'callback_query', 'channel_post', 'chat_join_request'])
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            time.sleep(15)  # wait before retrying
