import os
import time
import threading
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== SAFE ENV LOAD =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID_RAW = os.getenv("OWNER_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))

if not BOT_TOKEN or not OWNER_ID_RAW:
    print("❌ ENV variables missing")
    while True:
        time.sleep(60)  # keep container alive

OWNER_ID = int(OWNER_ID_RAW)

# ===== STORAGE =====
monitored_users = {}

# ===== INSTAGRAM CHECK =====
def is_unbanned(username: str) -> bool:
    try:
        url = f"https://www.instagram.com/{username}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        html = r.text.lower()
        return "profile_id" in html
    except:
        return False

# ===== MONITOR LOOP =====
def monitor_loop(app):
    print("🔄 Monitor loop started")
    while True:
        for username, status in list(monitored_users.items()):
            if status == "banned" and is_unbanned(username):
                monitored_users[username] = "unbanned"
                app.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"🎉 Instagram UNBANNED!\n\nUsername: {username}"
                )
        time.sleep(CHECK_INTERVAL)

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        "🤖 Instagram Unban Monitor Bot\n\n"
        "/add username\n"
        "/remove username\n"
        "/list"
    )

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /add username")
        return
    username = context.args[0].lower()
    monitored_users[username] = "banned"
    await update.message.reply_text(f"✅ Added: {username}")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /remove username")
        return
    username = context.args[0].lower()
    monitored_users.pop(username, None)
    await update.message.reply_text(f"❌ Removed: {username}")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not monitored_users:
        await update.message.reply_text("No usernames being monitored")
        return
    msg = "📋 Monitoring:\n\n"
    for u, s in monitored_users.items():
        msg += f"{u} → {s}\n"
    await update.message.reply_text(msg)

# ===== MAIN =====
def main():
    print("🚀 Bot starting")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(CommandHandler("remove", remove_user))
    app.add_handler(CommandHandler("list", list_users))

    threading.Thread(target=monitor_loop, args=(app,), daemon=True).start()
    app.run_polling()

if __name__ == "__main__":
    main()
