import asyncio
import sqlite3
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

BOT_TOKEN = "8182141201:AAHP9UDOX79woOpmB8TtS_byiwamJBcEVbQ"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Database
conn = sqlite3.connect("accounts.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    username TEXT PRIMARY KEY,
    status TEXT
)
""")
conn.commit()

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers, timeout=15)
    text = r.text.lower()

    if "sorry, this page isn't available" in text:
        return "banned"
    if "profile_id" in text or "shareddata" in text:
        return "active"
    return "unknown"

@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer(
        "🤖 Instagram Unban Monitor Bot\n\n"
        "Commands:\n"
        "/monitor username\n"
        "/list\n"
        "/remove username"
    )

@dp.message(Command("monitor"))
async def monitor(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Usage: /monitor username")
        return

    username = parts[1].replace("@", "")
    cur.execute("INSERT OR IGNORE INTO accounts VALUES (?, ?)", (username, "banned"))
    conn.commit()
    await msg.answer(f"✅ Monitoring started\nAccount: {username}")

@dp.message(Command("list"))
async def list_accounts(msg: Message):
    cur.execute("SELECT username, status FROM accounts")
    rows = cur.fetchall()

    if not rows:
        await msg.answer("No accounts monitored.")
        return

    text = "📊 Monitored Accounts:\n"
    for u, s in rows:
        text += f"- {u} : {s}\n"

    await msg.answer(text)

@dp.message(Command("remove"))
async def remove(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Usage: /remove username")
        return

    username = parts[1]
    cur.execute("DELETE FROM accounts WHERE username=?", (username,))
    conn.commit()
    await msg.answer(f"❌ Removed {username}")

async def background_checker():
    while True:
        cur.execute("SELECT username, status FROM accounts")
        rows = cur.fetchall()

        for username, old_status in rows:
            new_status = check_instagram(username)

            if old_status == "banned" and new_status == "active":
                await bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"🎉 INSTAGRAM UNBANNED\n\nAccount: {username}"
                )
                cur.execute(
                    "UPDATE accounts SET status=? WHERE username=?",
                    ("active", username)
                )
                conn.commit()

        await asyncio.sleep(900)  # 15 minutes

async def main():
    asyncio.create_task(background_checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    ADMIN_CHAT_ID = 5590079891
    asyncio.run(main())