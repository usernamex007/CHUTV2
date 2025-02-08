import asyncio
import os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from motor.motor_asyncio import AsyncIOMotorClient

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"

# 🔹 MongoDB Setup
MONGO_URI = "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net"
client = AsyncIOMotorClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["joined_users"]

# 🔹 Required Channel
MUST_JOIN = "SANATANI_TECH"

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}

# 🔹 Check if a user is in the required channel
async def is_user_in_channel(user_id):
    try:
        user = await bot.get_participants(MUST_JOIN, filter=events.ChatParticipants())
        user_ids = [u.id for u in user]
        return user_id in user_ids
    except Exception:
        return False

# 🔹 Start Command
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    is_joined = await is_user_in_channel(user_id)

    if not is_joined:
        await event.respond(
            f"🚨 You must join @{MUST_JOIN} to use this bot!\nClick below to join.",
            buttons=[Button.url("✅ Join Now", f"https://t.me/{MUST_JOIN}")]
        )
        return

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("ℹ️ Help", b"help")],
            [Button.inline("❌ Cancel", b"cancel")]
        ]
    )

# 🔹 Button Handlers
@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await ask_phone(event)
    elif event.data == b"help":
        await event.answer(
            "📌 **How to Generate a Session String:**\n\n"
            "1️⃣ Click 'Generate Session'\n"
            "2️⃣ Enter your phone number with country code (e.g., +919876543210)\n"
            "3️⃣ Enter the OTP received in Telegram\n"
            "4️⃣ If prompted, enter your 2-Step Verification password\n"
            "5️⃣ Your session string will be generated!"
        )
    elif event.data == b"cancel":
        user_id = event.sender_id
        if user_id in user_sessions:
            del user_sessions[user_id]
            await event.answer("✅ Process canceled successfully!")
        else:
            await event.answer("⚠️ No active process to cancel.")

# 🔹 Generate Session Command
async def ask_phone(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP.**")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**")

# 🔹 Process User Input (Phone, OTP, Password)
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return

    step = user_sessions[user_id]["step"]

    # ✅ Step 1: Enter Phone Number
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
            await event.respond("✅ **OTP sent! Please enter the OTP received on Telegram.**")
        except Exception as e:
            del user_sessions[user_id]
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    # ✅ Step 2: Enter OTP
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
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            
            # ✅ Log to MongoDB
            await users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"joined": True}},
                upsert=True
            )

            del user_sessions[user_id]
        except Exception as e:
            if "The confirmation code has expired" in str(e):
                await event.respond("❌ **Error: Your OTP has expired. Please request a new one using /generate.**")
                del user_sessions[user_id]
            elif "Two-steps verification is enabled" in str(e):
                user_sessions[user_id]["step"] = "password"
                await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:")
            else:
                await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    # ✅ Step 3: Enter Password (if needed)
    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
