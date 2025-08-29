import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from firebase_db import FirebaseDB  # Import your Firebase database handler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in Render Environment Variables!")

# Initialize Firebase
firebase = FirebaseDB()

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name

    # Check if user exists in Firebase
    user_data = firebase.get_user(user_id)
    if not user_data:
        firebase.create_user(user_id, first_name)

    # Referral system
    ref_code = context.args[0] if context.args else None
    if ref_code and ref_code != user_id:
        firebase.add_referral(ref_code, user_id)

    keyboard = [[InlineKeyboardButton("💰 Check Balance", callback_data="balance")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Hello {first_name}!\n\n"
        "Welcome to **Algam Telegram Bot** 🎉\n\n"
        "✅ Earn **100 coins daily**\n"
        "✅ Invite friends & earn more!\n\n"
        "Use your referral link:\n"
        f"https://t.me/{context.bot.username}?start={user_id}",
        reply_markup=reply_markup
    )

# Daily reward command
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    reward_given = firebase.give_daily_reward(user_id)

    if reward_given:
        await update.message.reply_text("🎁 You received **100 coins** today! Come back tomorrow!")
    else:
        await update.message.reply_text("⏳ You already claimed today's reward. Try again tomorrow!")

# Balance command
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balance = firebase.get_balance(user_id)
    await update.message.reply_text(f"💰 Your current balance: **{balance} coins**")

# Main function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("balance", balance))

    logger.info("🤖 Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
