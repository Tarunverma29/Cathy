from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from database.telegram_users import get_or_create_user
from database.messages import save_message, get_recent_messages

from core.chat_service import (
    create_new_chat_telegram,
    switch_chat_telegram,
    delete_chat,
    get_all_chats,
)

from mental.classifier import classify_emotions
from mental.reasoning import analyze_psychology
from mental.risk_engine import compute_risk
from mental.patterns import detect_streak
from mental.logger import log_emotional_state
from mental.responder import build_crisis_response

from core.llm import generate
from config.settings import TELEGRAM_TOKEN

BOT_TOKEN = TELEGRAM_TOKEN

with open("personas/cathy.txt", "r", encoding="utf-8") as f:
    CHARACTER = f.read()


# ──────────────────────────── MENU ────────────────────────────

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ New Chat", callback_data="new_chat")],
        [InlineKeyboardButton("📂 My Chats", callback_data="list_chats")],
    ]
    await update.message.reply_text(
        "Chat Manager", reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ──────────────────────────── BUTTON HANDLER ──────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    if data == "new_chat":
        chat_id = create_new_chat_telegram(user.id)
        await query.edit_message_text(f"✅ New chat created (id: {chat_id})")

    elif data == "list_chats":
        chats = get_all_chats()
        if not chats:
            await query.edit_message_text("No chats found.")
            return

        keyboard = [
            [
                InlineKeyboardButton(f"🔄 {c[1]}", callback_data=f"switch_{c[0]}"),
                InlineKeyboardButton("❌", callback_data=f"delete_{c[0]}"),
            ]
            for c in chats
        ]
        await query.edit_message_text(
            "Your Chats:", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("switch_"):
        chat_id = int(data.split("_")[1])
        switch_chat_telegram(user.id, chat_id)
        await query.edit_message_text("✅ Switched.")

    elif data.startswith("delete_"):
        chat_id = int(data.split("_")[1])
        delete_chat(chat_id)
        await query.edit_message_text("🗑️ Deleted.")


# ──────────────────────────── MAIN MESSAGE HANDLER ────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_input = update.message.text

    chat_id = get_or_create_user(user)
    save_message(chat_id, "user", user_input)

    # ── Mental Health Pipeline ──────────────────────────────────
    emotions    = classify_emotions(user_input)
    llm_data    = analyze_psychology(user_input)
    streak_fac  = detect_streak(user.id)

    risk_score = compute_risk(emotions, llm_data, streak_fac)

    log_emotional_state(user.id, chat_id, emotions, llm_data, risk_score)

    # ── Tier 1 — Critical Risk (≥15) ───────────────────────────
    if risk_score >= 15:
        reply = build_crisis_response(
            user_input, emotions, llm_data, risk_score, use_llm=True
        )
        save_message(chat_id, "assistant", reply)
        await update.message.reply_text(reply)
        print(f"⚠️  CRITICAL RISK  user={user.id}  score={risk_score}")
        return

    # ── Tier 2 — High Risk (10–14) ─────────────────────────────
    # Still reply, but prepend a brief check-in before the persona's reply
    if risk_score >= 10:
        check_in = build_crisis_response(
            user_input, emotions, llm_data, risk_score, use_llm=False
        )
        conversation = get_recent_messages(chat_id, limit=6)
        persona_reply = generate(CHARACTER, conversation, user_input)

        reply = f"{check_in}\n\n{persona_reply}"
        save_message(chat_id, "assistant", reply)
        await update.message.reply_text(reply)
        print(f"⚡  HIGH RISK  user={user.id}  score={risk_score}")
        return

    # ── Tier 3 — Moderate Risk (6–9) ───────────────────────────
    # Persona replies normally, but a soft check-in is appended
    if risk_score >= 6:
        conversation = get_recent_messages(chat_id, limit=6)
        persona_reply = generate(CHARACTER, conversation, user_input)
        check_in = build_crisis_response(
            user_input, emotions, llm_data, risk_score, use_llm=False
        )
        reply = f"{persona_reply}\n\n…{check_in}"
        save_message(chat_id, "assistant", reply)
        await update.message.reply_text(reply)
        return

    # ── Normal Chat ─────────────────────────────────────────────
    conversation = get_recent_messages(chat_id, limit=6)
    reply = generate(CHARACTER, conversation, user_input)
    save_message(chat_id, "assistant", reply)
    await update.message.reply_text(reply)


# ──────────────────────────── ENTRYPOINT ──────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("🤖 Telegram bot running…")
    app.run_polling()
