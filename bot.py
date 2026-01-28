import os
import pandas as pd
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from openai import OpenAI

# -------------------------------------------------
# LOGGING
# -------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
EXCEL_FILE = "UPSC_Master_Tagged.xlsx"
df = pd.read_excel(EXCEL_FILE)

# -------------------------------------------------
# OPENAI CLIENT
# -------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------
# /start → PRIVATE ONLY
# -------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['Polity', 'Economy'],
        ['Modern History', 'Geography'],
        ['Science & Tech', 'Environment & Ecology'],
        ['Current Affairs', 'Art and Culture']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        "📚 *UPSC AI Mentor Active*\n\n"
        "Practice UPSC PYQs (2014–2025) with AI-based explanation.\n"
        "✅ Completely FREE | No limits"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# -------------------------------------------------
# DELETE “START” TEXT IN GROUPS
# -------------------------------------------------
async def delete_start_in_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        if update.message.text.strip().upper() == "START":
            try:
                await update.message.delete()
            except Exception:
                pass  # bot not admin or no permission

# -------------------------------------------------
# HANDLE USER MESSAGES (PRIVATE ONLY)
# -------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject_choice = update.message.text

    subset = df[df["Subject"] == subject_choice]
    if subset.empty:
        await update.message.reply_text("Please select a subject from the menu.")
        return

    row = subset.sample(1).iloc[0]

    await update.message.reply_text(
        f"⏳ *Year:* {row['Year']}\n\n❓ *Question:*\n{row['Question Text']}",
        parse_mode="Markdown"
    )

    prompt = (
        "Act as a UPSC mentor. "
        "Explain the logic, elimination strategy, and common traps "
        "in the following question:\n\n"
        f"{row['Question Text']}"
    )

    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    analysis = ai_response.choices[0].message.content

    await update.message.reply_text(
        f"💡 *AI Explanation:*\n{analysis}",
        parse_mode="Markdown"
    )

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")

    application = ApplicationBuilder().token(token).build()

    # /start only in private
    application.add_handler(
        CommandHandler("start", start, filters.ChatType.PRIVATE)
    )

    # Delete START in groups
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            delete_start_in_groups
        )
    )

    # Normal text → private only
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    application.run_polling()
