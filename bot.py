import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# =========================================================
# إعدادات أساسية
# =========================================================
TOKEN = "9100262932:AAHUo79g_vKxOPTWmPXAnj2mXhVIwN-PBdU"   # ضعي توكن البوت الجديد هنا
ADMIN_ID = 8292471160             # رقم حساب المشرفة

bot = telebot.TeleBot(TOKEN)
DB_NAME = "mtoo7_data.db"

# المواد ومعرّفات الملفات التي أرسلتِها في المحادثة.
# ملاحظة: قد لا تعمل file_id القديمة مع البوت الجديد؛ عندها ارفعي
# ملفات PDF من لوحة الإدارة داخل البوت ليحفظ معرّفاتها الجديدة.
INITIAL_SUBJECTS = {
    "Histology 🔬": [
        ("محاضرة الهستولوجي رقم 1", "BQACAgQAAxkBAAICAgADiSEAAlSfMVI"),
        ("محاضرة الهستولوجي رقم 2", "AgADwx8AAin7iFI"),
    ],
    "Physiology 🫀": [
        ("محاضرة الفسيولوجي رقم 1", "AgAD3B8AAin7gFI"),
        ("محاضرة الفسيولوجي رقم 2", "AgADiioAAs3tgFI"),
    ],
    "Biochemistry 🧪": [
        ("محاضرة البايوكيمستري رقم 1", "AgADvyEAAtXJmFE"),
        ("محاضرة البايوكيمستري رقم 2", "AgADyR8AAhg1-VE"),
    ],
    "Pathology 🦠": [
        ("محاضرة الباثولوجي رقم 1", "AgADvzEAAh3tOFM"),
        ("محاضرة الباثولوجي رقم 2", "AgADwDEAAh3tOFM"),
    ],
    "Materials 📦": [
        ("محاضرة الماتيريال رقم 1", "AgADYB8AAhblKVM"),
    ],
    "Anatomy 🦴": [
        ("محاضرة الأناتومي رقم 1", "AgADxh8AAhg1-VE"),
        ("محاضرة الأناتومي رقم 2", "AgADxh8AAhg1-VE"),
    ],
    "Microbiology 🧫": [
        ("محاضرة الميكرو رقم 1", "AgADESEAAh5vEFI"),
    ],
    "أخلاقيات المهنة الطبية 📚": [
        ("أخلاقيات المهنة الطبية", "AgADaxsAAtx56VE"),
    ],
    "ثقافة وطنية 🇱🇾": [
        ("الثقافة الوطنية", "AgADCigAAiAO6VI"),
    ],
    "علم النفس الطبي 🧠": [
        ("علم النفس الطبي", "AgADiB0AApu_SFI"),
    ],
    "إدارة صحية 📊": [
        ("الإدارة الصحية", "AQADJigAAgsq2FFy"),
    ],
}

# حالات انتظار رسائل المشرفة
admin_state = {}


def connect_db():
    return sqlite3.connect(DB_NAME)


def init_db():
    with connect_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            file_id TEXT NOT NULL,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )""")

        for subject_name, lectures in INITIAL_SUBJECTS.items():
            conn.execute(
                "INSERT OR IGNORE INTO subjects(name) VALUES (?)",
                (subject_name,)
            )
            subject_id = conn.execute(
                "SELECT id FROM subjects WHERE name = ?", (subject_name,)
            ).fetchone()[0]

            for lecture_name, file_id in lectures:
                exists = conn.execute(
                    "SELECT id FROM lectures WHERE subject_id=? AND name=?",
                    (subject_id, lecture_name)
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO lectures(subject_id,name,file_id) VALUES (?,?,?)",
                        (subject_id, lecture_name, file_id)
                    )


def is_admin(user_id):
    return user_id == ADMIN_ID


def subjects_keyboard():
    # قائمة ثابتة تظهر أسفل الشاشة بدل أزرار داخل رسالة
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    with connect_db() as conn:
        rows = conn.execute("SELECT name FROM subjects ORDER BY id").fetchall()
    for (name,) in rows:
        markup.add(KeyboardButton(name))
    markup.add(KeyboardButton("🏠 القائمة الرئيسية"))
    return markup


def lectures_keyboard(subject_id):
    markup = InlineKeyboardMarkup(row_width=1)
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT id,name FROM lectures WHERE subject_id=? ORDER BY id",
            (subject_id,)
        ).fetchall()
    for lid, name in rows:
        markup.add(InlineKeyboardButton(name, callback_data=f"lecture:{lid}"))
    markup.add(InlineKeyboardButton("⬅️ رجوع للمواد", callback_data="home"))
    return markup


def admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ إضافة مادة", callback_data="adm:add_subject"),
        InlineKeyboardButton("📤 إضافة محاضرة / PDF", callback_data="adm:add_lecture"),
        InlineKeyboardButton("✏️ تعديل اسم محاضرة", callback_data="adm:rename"),
        InlineKeyboardButton("🗑️ حذف محاضرة", callback_data="adm:delete_lecture"),
        InlineKeyboardButton("🗑️ حذف مادة كاملة", callback_data="adm:delete_subject"),
        InlineKeyboardButton("📚 عرض المواد والمحاضرات", callback_data="adm:list"),
        InlineKeyboardButton("🏠 قائمة الطلبة", callback_data="home"),
    )
    return markup


def send_admin_panel(chat_id):
    bot.send_message(
        chat_id,
        "👩🏻‍💻 لوحة تحكم المشرفة\n"
        "من هنا تقدري تضيفي وتعدلي وتحذفي المواد والمحاضرات.\n"
        "اختاري العملية:",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "أهلاً بك في مكتبة تقنية الأسنان 🦷📚\n\n"
        "اختاري المادة من القائمة اللي تحت لعرض كل الشيتات:",
        reply_markup=subjects_keyboard()
    )


@bot.message_handler(commands=["admin"])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "هذه اللوحة مخصصة للمشرفة فقط.")
        return
    send_admin_panel(message.chat.id)


@bot.message_handler(commands=["cancel"])
def cancel(message):
    if is_admin(message.from_user.id):
        admin_state.pop(message.from_user.id, None)
        bot.reply_to(message, "تم إلغاء العملية.")
        send_admin_panel(message.chat.id)


def ask_subject_for_action(chat_id, action, prompt):
    with connect_db() as conn:
        rows = conn.execute("SELECT id,name FROM subjects ORDER BY id").fetchall()
    if not rows:
        bot.send_message(chat_id, "لا توجد مواد. أضيفي مادة أولاً.")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for sid, name in rows:
        markup.add(InlineKeyboardButton(name, callback_data=f"pick:{action}:{sid}"))
    bot.send_message(chat_id, prompt, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    uid = call.from_user.id
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if data == "home":
        bot.edit_message_text(
            "📚 القائمة الرئيسية\nاختاري المادة:",
            chat_id, call.message.message_id,
            reply_markup=subjects_keyboard()
        )
        return

    if data.startswith("subject:"):
        sid = int(data.split(":")[1])
        with connect_db() as conn:
            row = conn.execute("SELECT name FROM subjects WHERE id=?", (sid,)).fetchone()
        if not row:
            bot.send_message(chat_id, "المادة غير موجودة.")
            return
        bot.edit_message_text(
            f"📖 {row[0]}\n\nاختاري المحاضرة:",
            chat_id, call.message.message_id,
            reply_markup=lectures_keyboard(sid)
        )
        return

    if data.startswith("lecture:"):
        lid = int(data.split(":")[1])
        with connect_db() as conn:
            row = conn.execute(
                "SELECT name,file_id FROM lectures WHERE id=?", (lid,)
            ).fetchone()
        if not row:
            bot.send_message(chat_id, "المحاضرة غير موجودة.")
            return
        try:
            bot.send_document(chat_id, row[1], caption=f"📚 {row[0]}")
        except Exception:
            bot.send_message(
                chat_id,
                "تعذر إرسال هذا الملف. غالباً معرّف الملف القديم لا يعمل مع البوت الجديد.\n"
                "اطلبي من المشرفة إعادة رفع ملف PDF من لوحة الإدارة."
            )
        return

    # كل العمليات التالية للمشرفة فقط
    if data.startswith("adm:") or data.startswith("pick:"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "غير مسموح لكِ.", show_alert=True)
            return

    if data == "adm:add_subject":
        admin_state[uid] = {"step": "new_subject"}
        bot.send_message(chat_id, "اكتبي اسم المادة الجديدة.\nللإلغاء اكتبي /cancel")
        return

    if data == "adm:add_lecture":
        ask_subject_for_action(chat_id, "add", "اختاري المادة التي تريدين إضافة محاضرة إليها:")
        return

    if data == "adm:rename":
        ask_subject_for_action(chat_id, "rename_subject", "اختاري مادة المحاضرة التي تريدين تعديل اسمها:")
        return

    if data == "adm:delete_lecture":
        ask_subject_for_action(chat_id, "delete_subject", "اختاري المادة التي تحتوي على المحاضرة المراد حذفها:")
        return

    if data == "adm:delete_subject":
        ask_subject_for_action(chat_id, "delete_all_subject", "اختاري المادة التي تريدين حذفها بالكامل:")
        return

    if data == "adm:list":
        with connect_db() as conn:
            rows = conn.execute("""
                SELECT subjects.name, lectures.name
                FROM subjects LEFT JOIN lectures ON subjects.id=lectures.subject_id
                ORDER BY subjects.id, lectures.id
            """).fetchall()
        if not rows:
            bot.send_message(chat_id, "لا توجد مواد حالياً.")
        else:
            lines = []
            last_subject = None
            for sname, lname in rows:
                if sname != last_subject:
                    lines.append(f"\n📚 {sname}")
                    last_subject = sname
                lines.append(f"  • {lname or 'لا توجد محاضرات'}")
            bot.send_message(chat_id, "\n".join(lines))
        return

    if data.startswith("pick:"):
        _, action, sid_text = data.split(":")
        sid = int(sid_text)

        if action == "add":
            admin_state[uid] = {"step": "new_lecture_name", "subject_id": sid}
            bot.send_message(chat_id, "اكتبي اسم المحاضرة الجديدة.\nللإلغاء اكتبي /cancel")
            return

        if action in ("rename_subject", "delete_subject"):
            with connect_db() as conn:
                rows = conn.execute(
                    "SELECT id,name FROM lectures WHERE subject_id=? ORDER BY id", (sid,)
                ).fetchall()
            if not rows:
                bot.send_message(chat_id, "المادة لا تحتوي على محاضرات.")
                return
            markup = InlineKeyboardMarkup(row_width=1)
            verb = "rename" if action == "rename_subject" else "del"
            for lid, lname in rows:
                markup.add(InlineKeyboardButton(lname, callback_data=f"lecture_action:{verb}:{lid}"))
            bot.send_message(chat_id, "اختاري المحاضرة:", reply_markup=markup)
            return

        if action == "delete_all_subject":
            with connect_db() as conn:
                conn.execute("DELETE FROM lectures WHERE subject_id=?", (sid,))
                conn.execute("DELETE FROM subjects WHERE id=?", (sid,))
            bot.send_message(chat_id, "تم حذف المادة وكل محاضراتها. ✅")
            send_admin_panel(chat_id)
            return

    if data.startswith("lecture_action:"):
        if not is_admin(uid):
            return
        _, action, lid_text = data.split(":")
        lid = int(lid_text)
        if action == "del":
            with connect_db() as conn:
                conn.execute("DELETE FROM lectures WHERE id=?", (lid,))
            bot.send_message(chat_id, "تم حذف المحاضرة. ✅")
            send_admin_panel(chat_id)
        elif action == "rename":
            admin_state[uid] = {"step": "rename_lecture", "lecture_id": lid}
            bot.send_message(chat_id, "اكتبي الاسم الجديد للمحاضرة.\nللإلغاء اكتبي /cancel")


@bot.message_handler(content_types=["document"])
def receive_pdf(message):
    uid = message.from_user.id
    state = admin_state.get(uid)
    if not is_admin(uid) or not state or state.get("step") != "waiting_pdf":
        return

    doc = message.document
    filename = (doc.file_name or "").lower()
    if doc.mime_type != "application/pdf" and not filename.endswith(".pdf"):
        bot.reply_to(message, "ابعتي ملف PDF فقط، أو اكتبي /cancel للإلغاء.")
        return

    with connect_db() as conn:
        conn.execute(
            "INSERT INTO lectures(subject_id,name,file_id) VALUES (?,?,?)",
            (state["subject_id"], state["lecture_name"], doc.file_id)
        )
    admin_state.pop(uid, None)
    bot.reply_to(message, "تمت إضافة المحاضرة بنجاح! ✅")
    send_admin_panel(message.chat.id)


@bot.message_handler(content_types=["text"])
def admin_text(message):
    uid = message.from_user.id
    state = admin_state.get(uid)
    text = message.text.strip()

    # تنقّل الطلبة من لوحة الأزرار السفلية
    if not state:
        if text == "🏠 القائمة الرئيسية":
            bot.send_message(
                message.chat.id,
                "📚 مكتبة تقنية الأسنان 🦷\nاختاري المادة من القائمة اللي تحت:",
                reply_markup=subjects_keyboard()
            )
            return

        with connect_db() as conn:
            subject = conn.execute(
                "SELECT id,name FROM subjects WHERE name=?", (text,)
            ).fetchone()
        if subject:
            sid, subject_name = subject
            with connect_db() as conn:
                lectures = conn.execute(
                    "SELECT name,file_id FROM lectures WHERE subject_id=? ORDER BY id",
                    (sid,)
                ).fetchall()
            if not lectures:
                bot.send_message(message.chat.id, f"📖 {subject_name}\nمافيش شيتات مضافة للمادة حالياً.")
                return
            bot.send_message(message.chat.id, f"📚 شيتات {subject_name}:")
            for lecture_name, file_id in lectures:
                try:
                    bot.send_document(message.chat.id, file_id, caption=f"📄 {lecture_name}")
                except Exception:
                    bot.send_message(
                        message.chat.id,
                        f"تعذر إرسال {lecture_name}. غالباً الملف القديم لا يعمل مع البوت الجديد؛ ارفعيه من لوحة الإدارة مرة ثانية."
                    )
            return

        return

    if not is_admin(uid):
        return

    step = state.get("step")

    if step == "new_subject":
        if not text:
            bot.reply_to(message, "اكتبي اسم المادة.")
            return
        try:
            with connect_db() as conn:
                conn.execute("INSERT INTO subjects(name) VALUES (?)", (text,))
            admin_state.pop(uid, None)
            bot.reply_to(message, f"تمت إضافة مادة {text} بنجاح. ✅")
            send_admin_panel(message.chat.id)
        except sqlite3.IntegrityError:
            bot.reply_to(message, "المادة موجودة بالفعل. اكتبي اسماً آخر.")

    elif step == "new_lecture_name":
        state["lecture_name"] = text
        state["step"] = "waiting_pdf"
        bot.reply_to(message, "ممتاز! توا ابعتي ملف المحاضرة بصيغة PDF 📎")

    elif step == "rename_lecture":
        with connect_db() as conn:
            conn.execute(
                "UPDATE lectures SET name=? WHERE id=?",
                (text, state["lecture_id"])
            )
        admin_state.pop(uid, None)
        bot.reply_to(message, "تم تعديل اسم المحاضرة. ✅")
        send_admin_panel(message.chat.id)


if __name__ == "__main__":
    if TOKEN == "PUT_NEW_BOT_TOKEN_HERE":
        print("ضعي توكن البوت الجديد في متغير TOKEN أولاً.")
    else:
        init_db()
        print("Mtoo7Bot is running...")
        bot.infinity_polling(skip_pending=True)
