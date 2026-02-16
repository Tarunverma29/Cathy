from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database.telegram_users import get_or_create_user
from database.messages import save_message, get_recent_messages

from core.chat_service import (
    create_new_chat_telegram,
    switch_chat_telegram,
    delete_chat,
    get_all_chats
)

from mental.classifier import classify_emotions
from mental.reasoning import analyze_psychology
from mental.risk_engine import compute_risk
from mental.patterns import detect_streak
from mental.logger import log_emotional_state

from core.llm import generate

BOT_TOKEN = "8387791728:AAECyIoxGIGtCRLPH6fuRrx7l8DU3_QriX4"

with open("personas/cathy.txt", "r", encoding="utf-8") as f:
    CHARACTER = f.read()


# ---------- MENU ----------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ New Chat", callback_data="new_chat")],
        [InlineKeyboardButton("📂 My Chats", callback_data="list_chats")]
    ]

    await update.message.reply_text(
        "Chat Manager",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------- BUTTON HANDLER ----------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    if data == "new_chat":
        chat_id = create_new_chat_telegram(user.id)
        await query.edit_message_text(f"Created chat {chat_id}")

    elif data == "list_chats":
        chats = get_all_chats()

        if not chats:
            await query.edit_message_text("No chats.")
            return

        keyboard = []
        for c in chats:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔄 {c[1]}",
                    callback_data=f"switch_{c[0]}"
                ),
                InlineKeyboardButton(
                    "❌",
                    callback_data=f"delete_{c[0]}"
                )
            ])

        await query.edit_message_text(
            "Your Chats:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("switch_"):
        chat_id = int(data.split("_")[1])
        switch_chat_telegram(user.id, chat_id)
        await query.edit_message_text("Switched.")

    elif data.startswith("delete_"):
        chat_id = int(data.split("_")[1])
        delete_chat(chat_id)
        await query.edit_message_text("Deleted.")


# ---------- CHAT ----------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_input = update.message.text

    # 🔹 This already ensures user exists AND returns active chat_id
    chat_id = get_or_create_user(user)

    # Save user message
    save_message(chat_id, "user", user_input)

    # -------- Mental Health Detection --------
    emotions = classify_emotions(user_input)
    llm_analysis = analyze_psychology(user_input)
    streak_factor = detect_streak(user.id)

    risk_score = compute_risk(
        emotions,
        llm_analysis,
        streak_factor
    )

    log_emotional_state(
        user.id,
        chat_id,
        emotions,
        llm_analysis,
        risk_score
    )

    # -------- High Risk Override --------
    if risk_score >= 15:
        reply = (
            "I'm really concerned about how you're feeling. "
            "You deserve support. If you're in immediate danger, "
            "please contact local emergency services or someone you trust."
        )

        save_message(chat_id, "assistant", reply)
        await update.message.reply_text(reply)

        print(f"⚠ CRITICAL RISK USER {user.id} SCORE {risk_score}")
        return

    # -------- Normal Chat --------
    conversation = get_recent_messages(chat_id, limit=6)

    reply = generate(CHARACTER, conversation, user_input)

    save_message(chat_id, "assistant", reply)

    await update.message.reply_text(reply)


# ---------- MAIN ----------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram bot running...")
    app.run_polling()

