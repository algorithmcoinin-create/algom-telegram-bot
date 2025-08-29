import os, re, threading, logging
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters, ConversationHandler
)
from config import TELEGRAM_BOT_TOKEN
from firebase_db import (
    init_firebase, upsert_user, set_login, get_user, add_balance,
    can_claim_daily, set_daily_claimed, tap_increment
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# --- Rewards ---
REWARDS = {"daily": 50, "tap_reward": 100, "tap_goal": 100, "referral": 500}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WALLET_RE = re.compile(r"^(0x)?[0-9a-fA-F]{40}$")

# --- Flask tiny web (Render keeps the service alive) ---
web = Flask(__name__)

@web.get("/")
def root():  # simple health page
    return "ALGOM bot is running ✅"

@web.get("/healthz")
def healthz():
    return "ok", 200

# --- Telegram Bot ---

ASK_LOGIN = 1  # conversation state

WELCOME = (f"Welcome to ALGOM Crypto Game! 🎮\n\n"
           f"• Daily check-in: +{REWARDS['daily']} coins → /daily\n"
           f"• Tap-the-logo: {REWARDS['tap_goal']} taps → +{REWARDS['tap_reward']} → /tap\n"
           f"• Refer friends: +{REWARDS['referral']} coins → /me for your link\n\n"
           f"Use /login to submit your email (required) and wallet (optional).")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_firebase()
    u = update.effective_user
    args = context.args or []
    referrer = int(args[0]) if (args and args[0].isdigit()) else None
    upsert_user({
        "user_id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "username": u.username,
        "language_code": u.language_code or "en",
        "referrer": referrer
    })
    await update.message.reply_text(WELCOME)
    await me(update, context)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Please /start first.")
        return
    me_info = await context.bot.get_me()
    ref_link = f"https://t.me/{me_info.username}?start={update.effective_user.id}"
    text = (
        f"👤 Your Profile\n"
        f"• Balance: {user.get('balance',0)} ALGOM\n"
        f"• Email: {user.get('email') or '—'}\n"
        f"• Wallet: {user.get('wallet') or '—'}\n"
        f"• Tap progress: {user.get('tap_progress',0)}/{REWARDS['tap_goal']}\n\n"
        f"🔗 Referral link:\n{ref_link}"
    )
    await update.message.reply_text(text)

# --- /login conversation ---
async def login_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your details like this:\n\n"
        "`email@example.com 0xYourBNBWallet`\n\n"
        "Wallet is optional — you can send only email.",
        parse_mode="Markdown"
    )
    return ASK_LOGIN

async def login_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    parts = msg.split()
    email = parts[0] if parts else ""
    wallet = parts[1] if len(parts) > 1 else None

    if not EMAIL_RE.match(email):
        await update.message.reply_text("❌ Invalid email. Try again or /cancel.")
        return ASK_LOGIN
    if wallet and not WALLET_RE.match(wallet):
        await update.message.reply_text("❌ Wallet must be a 42-hex address (0x...). Try again or /cancel.")
        return ASK_LOGIN

    set_login(update.effective_user.id, email, wallet)
    await update.message.reply_text("✅ Saved! Use /daily and /tap to earn ALGOM.")
    return ConversationHandler.END

async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

# --- Daily reward ---
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not can_claim_daily(uid):
        await update.message.reply_text("⏳ You already claimed today. Try again in 24h.")
        return
    add_balance(uid, REWARDS["daily"], "daily")
    set_daily_claimed(uid)
    await update.message.reply_text(f"🎁 +{REWARDS['daily']} ALGOM added! See /me")

# --- Tap mini game ---
def tap_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🟡 TAP", callback_data="tap")]])

async def tap_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Please /start first.")
        return
    prog = int(user.get("tap_progress", 0))
    await update.message.reply_text(
        f"Tap the button {REWARDS['tap_goal']} times to win +{REWARDS['tap_reward']}.\n"
        f"Progress: {prog}/{REWARDS['tap_goal']}",
        reply_markup=tap_keyboard()
    )

async def tap_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    prog, done = tap_increment(uid, REWARDS["tap_goal"])
    if done:
        add_balance(uid, REWARDS["tap_reward"], "tap_reward")
        await q.edit_message_text(
            f"✅ Completed {REWARDS['tap_goal']} taps! +{REWARDS['tap_reward']} ALGOM added.\nUse /tap to play again."
        )
    else:
        await q.edit_message_text(
            f"Keep tapping… {prog}/{REWARDS['tap_goal']}", reply_markup=tap_keyboard()
        )

# --- Run bot polling in background thread so Flask can bind $PORT ---
def run_bot():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing!")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("tap", tap_cmd))
    app.add_handler(CallbackQueryHandler(tap_cb, pattern="^tap$"))

    login_conv = ConversationHandler(
        entry_points=[CommandHandler("login", login_entry)],
        states={ASK_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_receive)]},
        fallbacks=[CommandHandler("cancel", login_cancel)],
    )
    app.add_handler(login_conv)

    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == "__main__":
    # Start telegram bot in a separate thread
    threading.Thread(target=run_bot, daemon=True).start()

    # Start tiny Flask web server (Render expects a web service to bind $PORT)
    port = int(os.getenv("PORT", "10000"))
    web.run(host="0.0.0.0", port=port)
