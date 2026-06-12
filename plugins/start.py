import os
import asyncio
from helper.helper_func import *
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait
from config import MSG_EFFECT, OWNER_ID

QR_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "../assets/payment_qr.png")
CONTACT_USERNAME = "A_Gatherers_isekai_In_Hindi"

PREMIUM_GATE_CAPTION = (
    "<b>🔒 Premium Access Required</b>\n\n"
    "This content is only available for <b>Premium Members</b>.\n\n"
    "📲 Scan the QR code to make payment, then contact the owner to activate your premium access."
)

#===============================================================#

async def deliver_files(client, user_id, base64_string, original_payload, chat_id):
    """Decode and deliver files to the user."""
    try:
        string = await decode(base64_string)
        argument = string.split("-")
        ids = []
        source_channel_id = None

        if len(argument) == 3:
            encoded_start = int(argument[1])
            encoded_end = int(argument[2])

            primary_multiplier = abs(client.db)
            start_primary = int(encoded_start / primary_multiplier)
            end_primary = int(encoded_end / primary_multiplier)

            if encoded_start % primary_multiplier == 0 and encoded_end % primary_multiplier == 0:
                source_channel_id = client.db
                start = start_primary
                end = end_primary
            else:
                db_channels = getattr(client, 'db_channels', {})
                for channel_id_str in db_channels.keys():
                    channel_id = int(channel_id_str)
                    channel_multiplier = abs(channel_id)
                    start_test = int(encoded_start / channel_multiplier)
                    end_test = int(encoded_end / channel_multiplier)
                    if encoded_start % channel_multiplier == 0 and encoded_end % channel_multiplier == 0:
                        source_channel_id = channel_id
                        start = start_test
                        end = end_test
                        break
                if source_channel_id is None:
                    source_channel_id = client.db
                    start = start_primary
                    end = end_primary

            ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))

        elif len(argument) == 2:
            encoded_msg = int(argument[1])
            if hasattr(client, 'db_channel') and client.db_channel:
                primary_multiplier = abs(client.db_channel.id)
                msg_id_primary = int(encoded_msg / primary_multiplier)
                if encoded_msg % primary_multiplier == 0:
                    source_channel_id = client.db_channel.id
                    ids = [msg_id_primary]
                else:
                    db_channels = getattr(client, 'db_channels', {})
                    for channel_id_str in db_channels.keys():
                        channel_id = int(channel_id_str)
                        channel_multiplier = abs(channel_id)
                        msg_id_test = int(encoded_msg / channel_multiplier)
                        if encoded_msg % channel_multiplier == 0:
                            source_channel_id = channel_id
                            ids = [msg_id_test]
                            break
                    if source_channel_id is None:
                        source_channel_id = client.db_channel.id
                        ids = [msg_id_primary]
            else:
                source_channel_id = client.db
                ids = [int(encoded_msg / abs(client.db))]

    except Exception as e:
        client.LOGGER(__name__, client.name).warning(f"Error decoding base64: {e}")
        await client.send_message(chat_id, "⚠️ Invalid or expired link.")
        return

    temp_msg = await client.send_message(chat_id, "⏳ Loading your episode...")
    messages = []

    try:
        if source_channel_id:
            try:
                msgs = await client.get_messages(chat_id=source_channel_id, message_ids=list(ids))
                valid_msgs = [msg for msg in msgs if msg is not None]
                messages.extend(valid_msgs)
                if len(valid_msgs) < len(list(ids)):
                    missing_ids = [mid for mid in ids if mid not in {msg.id for msg in valid_msgs}]
                    if missing_ids:
                        additional = await get_messages(client, missing_ids)
                        messages.extend(additional)
            except Exception as e:
                client.LOGGER(__name__, client.name).warning(f"Error getting messages: {e}")
                messages = await get_messages(client, ids)
        else:
            messages = await get_messages(client, ids)
    except Exception as e:
        await temp_msg.edit_text("Something went wrong!")
        client.LOGGER(__name__, client.name).warning(f"Error getting messages: {e}")
        return

    if not messages:
        await temp_msg.edit_text("Couldn't find the files in the database.")
        return

    await temp_msg.delete()

    yugen_msgs = []
    for msg in messages:
        caption = (
            client.messages.get('CAPTION', '').format(
                previouscaption=msg.caption.html if msg.caption else msg.document.file_name
            ) if bool(client.messages.get('CAPTION', '')) and bool(msg.document)
            else ("" if not msg.caption else msg.caption.html)
        )
        reply_markup = msg.reply_markup if not client.disable_btn else None
        try:
            copied_msg = await msg.copy(
                chat_id=user_id,
                caption=caption,
                reply_markup=reply_markup,
                protect_content=client.protect
            )
            yugen_msgs.append(copied_msg)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            copied_msg = await msg.copy(
                chat_id=user_id,
                caption=caption,
                reply_markup=reply_markup,
                protect_content=client.protect
            )
            yugen_msgs.append(copied_msg)
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Failed to send message: {e}")

    if messages and client.auto_del > 0:
        asyncio.create_task(batch_auto_del_notification(
            bot_username=client.username,
            messages=yugen_msgs,
            delay_time=client.auto_del,
            transfer_link=original_payload,
            chat_id=chat_id,
            client=client
        ))

#===============================================================#

@Client.on_message(filters.command('start') & filters.private)
@force_sub
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    present = await client.mongodb.present_user(user_id)
    if not present:
        try:
            await client.mongodb.add_user(user_id)
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error adding a user:\n{e}")

    is_banned = await client.mongodb.is_banned(user_id)
    if is_banned:
        return await message.reply("**You have been banned from using this bot!**")

    text = message.text
    if len(text) > 7:
        try:
            original_payload = text.split(" ", 1)[1]
            base64_string = original_payload

            if base64_string.startswith("yu3elk"):
                base64_string = base64_string[6:-1]

        except IndexError:
            return await message.reply("Invalid command format.")

        is_user_pro = await client.mongodb.is_pro(user_id)
        is_privileged = is_user_pro or user_id in client.admins or user_id == OWNER_ID

        # Free users → send QR + contact button, no files
        if not is_privileged:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=QR_IMAGE_PATH,
                caption=PREMIUM_GATE_CAPTION,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📩 Contact Owner", url=f"https://t.me/{CONTACT_USERNAME}")]
                ])
            )
            return

        # Premium / admin / owner → store access data and show "Access Episode" button
        client.pending_accesses[user_id] = (base64_string, original_payload)
        await message.reply(
            "<b>✅ Premium Access Verified!</b>\n\nClick the button below to get your episode.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Access Episode", callback_data=f"access_ep_{user_id}")]
            ])
        )
        return

    # Normal /start message
    buttons = [[InlineKeyboardButton("Help", callback_data="about"), InlineKeyboardButton("Close", callback_data='close')]]
    if user_id in client.admins:
        buttons.insert(0, [InlineKeyboardButton("⛩️ ꜱᴇᴛᴛɪɴɢꜱ ⛩️", callback_data="settings")])

    photo = client.messages.get("START_PHOTO", "")
    start_caption = client.messages.get('START', 'Welcome, {mention}').format(
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        username=None if not message.from_user.username else '@' + message.from_user.username,
        mention=message.from_user.mention,
        id=message.from_user.id
    )

    if photo:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=start_caption,
            message_effect_id=MSG_EFFECT,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text=start_caption,
            message_effect_id=MSG_EFFECT,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

#===============================================================#

@Client.on_callback_query(filters.regex(r"^access_ep_\d+$"))
async def access_episode_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    expected_uid = int(callback_query.data.split("_")[-1])

    if user_id != expected_uid:
        return await callback_query.answer("❌ This button is not for you!", show_alert=True)

    pending = client.pending_accesses.pop(user_id, None)
    if not pending:
        return await callback_query.answer("⏰ Session expired. Please use the link again.", show_alert=True)

    await callback_query.answer("✅ Loading your episode...")

    try:
        await callback_query.message.delete()
    except Exception:
        pass

    base64_string, original_payload = pending
    await deliver_files(client, user_id, base64_string, original_payload, callback_query.message.chat.id)

#===============================================================#

@Client.on_message(filters.command('request') & filters.private)
async def request_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_admin = user_id in client.admins
    is_user_premium = await client.mongodb.is_pro(user_id)

    if is_admin or user_id == OWNER_ID:
        await message.reply_text("🔹 **You are my sensei!**\nThis command is only for users.")
        return

    if not is_user_premium:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=QR_IMAGE_PATH,
            caption=PREMIUM_GATE_CAPTION,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Contact Owner", url=f"https://t.me/{CONTACT_USERNAME}")]
            ])
        )
        return

    if len(message.command) < 2:
        await message.reply("⚠️ **Send me your request in this format:**\n`/request Your_Request_Here`")
        return

    requested = " ".join(message.command[1:])
    owner_message = (
        f"📩 **New Request from {message.from_user.mention}**\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📝 Request: `{requested}`"
    )
    await client.send_message(OWNER_ID, owner_message)
    await message.reply("✅ **Thanks for your request!**\nYour request will be reviewed soon. Please wait.")

#===============================================================#

@Client.on_message(filters.command('profile') & filters.private)
async def my_plan(client: Client, message: Message):
    user_id = message.from_user.id
    is_admin = user_id in client.admins

    if is_admin or user_id == OWNER_ID:
        await message.reply_text("🔹 You're my sensei! This command is only for users.")
        return

    is_user_premium = await client.mongodb.is_pro(user_id)

    if is_user_premium:
        await message.reply_text(
            "**👤 Profile Information:**\n\n"
            "🔸 Ads: Disabled\n"
            "🔸 Plan: Premium\n"
            "🔸 Request: Enabled\n\n"
            "🌟 You're a Premium User!"
        )
    else:
        await message.reply_text(
            "**👤 Profile Information:**\n\n"
            "🔸 Ads: Enabled\n"
            "🔸 Plan: Free\n"
            "🔸 Request: Disabled\n\n"
            "🔓 Upgrade to Premium to access all content.\n"
            f"Contact: @{CONTACT_USERNAME}"
        )
