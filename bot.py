import asyncio
import psycopg2
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"

# 🔹 PostgreSQL Database Connection
DATABASE_URL = "postgres://iarfggbc:Vxzh_kG7cxa1kHR5faxcd1kuA4R-UT9E@rosie.db.elephantsql.com/iarfggbc"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# 🔹 Initialize Bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Start Command
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("ℹ Help", b"help")]
        ]
    )

# 🔹 Help Button
@bot.on(events.CallbackQuery(pattern=b"help"))
async def help_text(event):
    await event.respond("ℹ **How to Generate Session?**\n\n1️⃣ Click **Generate Session**\n2️⃣ Enter your phone number\n3️⃣ Enter OTP received on Telegram\n4️⃣ If asked, enter 2-Step Verification password\n✅ Your session string will be generated!")

# 🔹 Generate Session
@bot.on(events.CallbackQuery(pattern=b"generate"))
async def ask_phone(event):
    user_id = event.sender_id
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**")
    bot.user_sessions[user_id] = {"step": "phone"}

# 🔹 Process User Inputs
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in bot.user_sessions:
        return

    step = bot.user_sessions[user_id]["step"]

    if step == "phone":
        phone_number = event.message.text.strip()
        bot.user_sessions[user_id]["phone"] = phone_number
        bot.user_sessions[user_id]["step"] = "otp"
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()

        try:
            sent_code = await client.send_code_request(phone_number)
            bot.user_sessions[user_id]["client"] = client
            bot.user_sessions[user_id]["sent_code"] = sent_code
            await event.respond("📩 **OTP sent! Please enter the OTP received on Telegram.**")
        except Exception as e:
            await event.respond(f"❌ **Error:** {e}. Please try again.")
            del bot.user_sessions[user_id]

    elif step == "otp":
        otp_code = event.message.text.strip()
        client = bot.user_sessions[user_id]["client"]
        phone_number = bot.user_sessions[user_id]["phone"]

        try:
            await client.sign_in(phone_number, otp_code)
            session_string = client.session.save()
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del bot.user_sessions[user_id]
        except Exception as e:
            if "The confirmation code has expired" in str(e):
                await event.respond("❌ **Error: The OTP has expired. Please use /generate to start again.**")
                del bot.user_sessions[user_id]
            elif "Two-steps verification is enabled" in str(e):
                bot.user_sessions[user_id]["step"] = "password"
                await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:")
            else:
                await event.respond(f"❌ **Error:** {e}. Please try again.")

    elif step == "password":
        password = event.message.text.strip()
        client = bot.user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del bot.user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {e}. Please try again.")

# 🔹 Run Bot
print("🚀 Bot is running...")
bot.user_sessions = {}
bot.run_until_disconnected()
