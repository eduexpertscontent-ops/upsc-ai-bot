import os
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from openai import OpenAI

# 1. LOAD DATA
# Render will look for this file in your GitHub repo
df = pd.read_excel("UPSC_Master_Tagged.xlsx")

# 2. SETUP AI CLIENT
# These keys will be added to Render's dashboard, not here!
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def start(update: Update, context):
    keyboard = [['Polity', 'Economy'], ['History', 'Geography'], ['Science & Tech', 'Environment']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("📚 *UPSC AI Mentor Active*\nChoose a subject:", reply_markup=reply_markup, parse_mode='Markdown')

async def handle_subject(update: Update, context):
    subject = update.message.text
    subset = df[df['Subject'] == subject]
    
    if subset.empty:
        await update.message.reply_text("Please pick a subject from the menu.")
        return

    # Select random question
    q = subset.sample(1).iloc[0]
    
    # Send Question
    await update.message.reply_text(f"⏳ *Year:* {q['Year']}\n❓ *Question:* {q['Question Text']}", parse_mode='Markdown')

    # Get AI Explanation
    prompt = f"Explain the logic of this UPSC question: {q['Question Text']}"
    ai_response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    
    await update.message.reply_text(f"💡 *AI ANALYSIS:*\n{ai_response.choices[0].message.content}", parse_mode='Markdown')

if __name__ == '__main__':
    # Get Token from Render Environment Variables
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_subject))
    app.run_polling()
