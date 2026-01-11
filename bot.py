import os
import pandas as pd
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Enable logging to see errors in Render logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. LOAD DATA
EXCEL_FILE = "UPSC_Master_Tagged.xlsx"
df = pd.read_excel(EXCEL_FILE)

# 2. SETUP AI CLIENT
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 3. USER DATABASE (Simple dictionary to track free usage)
# In production on Render, this resets if the bot restarts. 
# For 2,100 users, it's fine for a start!
user_data = {} 

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
        "Practice 11 years of PYQs (2014-2025) with AI Strategy.\n"
        "🎁 *Free Trial:* Your first 3 questions are FREE!"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    subject_choice = update.message.text
    
    # Initialize user if new
    if user_id not in user_data:
        user_data[user_id] = {'count': 0, 'is_paid': False}

    # PAYMENT CHECK
    if user_data[user_id]['count'] >= 3 and not user_data[user_id]['is_paid']:
        upi_id = "9643443102@ptsbi"
        pay_url = f"upi://pay?pa={upi_id}&pn=UPSC_AI_Mentor&am=199&cu=INR"
        
        keyboard = [[InlineKeyboardButton("💳 Pay ₹199 to Unlock All 1200+ Questions", url=pay_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🛑 *Trial Ended!*\n\nYou've used your 3 free questions. Pay once to unlock the full database and AI analysis forever.",
            reply_markup=reply_markup, parse_mode='Markdown'
        )
        return

    # FETCH QUESTION
    subset = df[df['Subject'] == subject_choice]
    if subset.empty:
        await update.message.reply_text("Please select a subject from the menu.")
        return

    row = subset.sample(1).iloc[0]
    user_data[user_id]['count'] += 1
    
    await update.message.reply_text(f"⏳ *Year:* {row['Year']}\n❓ *Question:* {row['Question Text']}", parse_mode='Markdown')

    # AI ANALYSIS
    prompt = f"Act as a UPSC mentor. Explain the logic and the 'trap' in this question: {row['Question Text']}"
    ai_response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    
    analysis = ai_response.choices[0].message.content
    await update.message.reply_text(f"💡 *AI STRATEGY:*\n{analysis}", parse_mode='Markdown')

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
