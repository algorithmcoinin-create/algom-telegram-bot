import os, re, threading, logging
from flask import Flask, request, render_template_string, send_file
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from admin_templates import HTML
from config import TELEGRAM_BOT_TOKEN, ADMIN_PIN
from firebase_db import upsert_user, set_login, get_user, add_balance, can_claim_daily, set_daily_claimed, tap_increment, stats, search_users, init_firebase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Rewards
REWARDS = {"daily": 50, "tap_reward": 100, "tap_goal": 100, "referral": 500}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WALLET_RE = re.compile(r"^(0x)?[0-9a-fA-F]{40}$")

WELCOME = (f"Welcome to ALGOM Crypto Game! 🎮\n\n"
           f"• Daily check-in: +{REWARDS['daily']} coins (/daily)\n"
           f"• Tap-the-logo: {REWARDS['tap_goal']} taps → +{REWARDS['tap_reward']} coins (/tap)\n"
           f"• Refer friends: +{REWARDS['referral']} coins per referral (/me)\n\n"
           f"Use /login to submit your email (required) and wallet (optional).")

# --- Telegram Bot Handlers ---
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
    u = get_user(update.effective_user.id)
    if not u:
        await update.message.reply_text("Please /start first.")
        return
    me_info = await context.bot.get_me()
    ref_link = f"https://t.me/{me_info.username}?start={update.effective_user.id}"
    text = (f"👤 Your Profile\n"
            f"• Balance: {u.get('balance',0)} ALGOM\n"
            f"• Email: {u.get('email') or '—'}\n"
            f"• Wallet: {u.get('wallet') or '—'}\n"
            f"• Tap progress: {u.get('tap_progress') or 0}/{REWARDS['tap_goal']}\n\n"
            f"🔗 Referra
