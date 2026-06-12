from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import re
from config import OWNER_ID

#========================================================================#

def parse_duration(duration_str: str) -> timedelta:
    duration_str = duration_str.lower().strip()
    match = re.match(r'^(\d+)\s*(day|days|week|weeks|month|months|year|years)$', duration_str)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).rstrip('s')
    if unit == 'day':
        return timedelta(days=amount)
    elif unit == 'week':
        return timedelta(weeks=amount)
    elif unit == 'month':
        return timedelta(days=amount * 30)
    elif unit == 'year':
        return timedelta(days=amount * 365)
    return None

def premium_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ 15 Days", callback_data=f"prem_{user_id}_15"),
            InlineKeyboardButton("💎 30 Days", callback_data=f"prem_{user_id}_30"),
        ],
        [
            InlineKeyboardButton("✏️ Custom", callback_data=f"prem_{user_id}_custom"),
            InlineKeyboardButton("♾️ Permanent", callback_data=f"prem_{user_id}_perm"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="prem_cancel")]
    ])

#========================================================================#

@Client.on_message(filters.command('addpremium') & filters.private)
async def add_premium_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    parts = message.command[1:]
    if not parts:
        return await message.reply_text(
            "<b>Usage:</b> /addpremium &lt;user_id&gt;\n\n"
            "After running the command, choose duration from the buttons."
        )

    try:
        user_id_to_add = int(parts[0])
    except ValueError:
        return await message.reply_text("Invalid user ID. Please check again.")

    try:
        user = await client.get_users(user_id_to_add)
        display_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Could not fetch user info: {e}")

    is_pro = await client.mongodb.is_pro(user_id_to_add)
    if is_pro:
        expiry = await client.mongodb.get_expiry_date(user_id_to_add)
        status_text = f"♻️ <b>Update Premium</b> — currently expires: <b>{expiry.strftime('%d %b %Y') if expiry else 'Permanent'}</b>"
    else:
        status_text = "🆓 <b>Free User</b> — select a plan to activate premium"

    await message.reply(
        f"👤 <b>User:</b> {display_name} (<code>{user_id_to_add}</code>)\n"
        f"{status_text}\n\n"
        f"<b>Select premium duration:</b>",
        reply_markup=premium_keyboard(user_id_to_add)
    )

#========================================================================#

@Client.on_callback_query(filters.regex(r"^prem_(\d+)_(15|30|perm|custom)$"))
async def premium_duration_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Only the owner can do this!", show_alert=True)

    match = re.match(r"^prem_(\d+)_(15|30|perm|custom)$", callback_query.data)
    user_id = int(match.group(1))
    option = match.group(2)

    # Fetch user info
    try:
        user = await client.get_users(user_id)
        display_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception as e:
        return await callback_query.answer(f"Error: {e}", show_alert=True)

    if option == "custom":
        await callback_query.message.edit_text(
            f"👤 <b>User:</b> {display_name} (<code>{user_id}</code>)\n\n"
            "✏️ <b>Send the custom duration</b> within 60 seconds.\n\n"
            "<b>Examples:</b>\n"
            "• <code>7 days</code>\n"
            "• <code>2 weeks</code>\n"
            "• <code>3 months</code>\n"
            "• <code>1 year</code>"
        )
        try:
            res = await client.listen(
                user_id=callback_query.from_user.id,
                filters=filters.text,
                timeout=60
            )
            duration = parse_duration(res.text.strip())
            if not duration:
                return await callback_query.message.edit_text(
                    "❌ Invalid duration format. Please use formats like:\n"
                    "<code>7 days</code>, <code>2 weeks</code>, <code>1 month</code>",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Try Again", callback_data=f"prem_retry_{user_id}")
                    ]])
                )
            expiry_date = datetime.now() + duration
            duration_text = f"{res.text.strip()} (until {expiry_date.strftime('%d %b %Y')})"
        except Exception:
            return await callback_query.message.edit_text(
                "⏰ Timed out. Please run /addpremium again.",
            )
    elif option == "15":
        expiry_date = datetime.now() + timedelta(days=15)
        duration_text = f"15 Days (until {expiry_date.strftime('%d %b %Y')})"
    elif option == "30":
        expiry_date = datetime.now() + timedelta(days=30)
        duration_text = f"30 Days (until {expiry_date.strftime('%d %b %Y')})"
    elif option == "perm":
        expiry_date = None
        duration_text = "Permanent"

    # Save to database
    await client.mongodb.add_pro(user_id, expiry_date)

    await callback_query.message.edit_text(
        f"✅ <b>Premium Activated!</b>\n\n"
        f"👤 <b>User:</b> {display_name} (<code>{user_id}</code>)\n"
        f"📅 <b>Duration:</b> {duration_text}"
    )

    # Notify the user
    try:
        if expiry_date:
            notify = (
                f"🎉 <b>Congratulations!</b>\n\n"
                f"Your premium membership has been activated until "
                f"<b>{expiry_date.strftime('%d %b %Y')}</b>!\n\n"
                f"Enjoy exclusive access to all content. 🌟"
            )
        else:
            notify = (
                "🎉 <b>Congratulations!</b>\n\n"
                "Your <b>Permanent Premium</b> membership has been activated!\n\n"
                "Enjoy exclusive access to all content forever. 🌟"
            )
        await client.send_message(user_id, notify)
    except Exception as e:
        await callback_query.message.reply(f"⚠️ Could not notify user: {e}")

#========================================================================#

@Client.on_callback_query(filters.regex(r"^prem_retry_(\d+)$"))
async def premium_retry_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Only the owner can do this!", show_alert=True)

    user_id = int(callback_query.data.split("_")[2])
    try:
        user = await client.get_users(user_id)
        display_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception:
        display_name = str(user_id)

    is_pro = await client.mongodb.is_pro(user_id)
    expiry = await client.mongodb.get_expiry_date(user_id) if is_pro else None
    status_text = (
        f"♻️ Currently expires: <b>{expiry.strftime('%d %b %Y') if expiry else 'Permanent'}</b>"
        if is_pro else "🆓 Free User"
    )

    await callback_query.message.edit_text(
        f"👤 <b>User:</b> {display_name} (<code>{user_id}</code>)\n"
        f"{status_text}\n\n<b>Select premium duration:</b>",
        reply_markup=premium_keyboard(user_id)
    )

#========================================================================#

@Client.on_callback_query(filters.regex("^prem_cancel$"))
async def premium_cancel_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Only the owner can do this!", show_alert=True)
    await callback_query.message.edit_text("❌ <b>Cancelled.</b>")

#========================================================================#

@Client.on_message(filters.command('delpremium') & filters.private)
async def remove_premium_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) != 2:
        return await message.reply_text("<b>Usage:</b> /delpremium &lt;user_id&gt;")

    try:
        user_id_to_remove = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid user ID. Please check again.")

    try:
        user = await client.get_users(user_id_to_remove)
        display_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Error fetching user: {e}")

    if await client.mongodb.is_pro(user_id_to_remove):
        await client.mongodb.remove_pro(user_id_to_remove)
        await message.reply_text(
            f"✅ <b>Premium Removed</b>\n\n"
            f"👤 <b>User:</b> {display_name} (<code>{user_id_to_remove}</code>)\n"
            f"Their premium membership has been revoked."
        )
        try:
            await client.send_message(
                user_id_to_remove,
                "⚠️ <b>Your premium membership has ended.</b>\n\n"
                f"Contact the owner to renew it."
            )
        except Exception as e:
            await message.reply_text(f"⚠️ Could not notify user: {e}")
    else:
        await message.reply_text(
            f"❌ <b>User {display_name} (<code>{user_id_to_remove}</code>) is not a premium user.</b>"
        )

#========================================================================#

@Client.on_message(filters.command('premiumusers') & filters.private)
async def premium_users_list(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    pro_user_ids = await client.mongodb.get_pros_list()
    if not pro_user_ids:
        return await message.reply_text("<b>No premium users found.</b>")

    lines = []
    for uid in pro_user_ids:
        try:
            user = await client.get_users(uid)
            name = user.first_name + (f" {user.last_name}" if user.last_name else "")
            username = f"@{user.username}" if user.username else "—"
        except Exception:
            name, username = "Unknown", "—"
        expiry = await client.mongodb.get_expiry_date(uid)
        expiry_str = expiry.strftime("%d %b %Y") if expiry else "♾️ Permanent"
        lines.append(f"• <b>{name}</b> ({username})\n  ID: <code>{uid}</code> | Expires: {expiry_str}")

    text = f"<b>💎 Premium Users ({len(lines)}):</b>\n\n" + "\n\n".join(lines)
    # Split if too long
    if len(text) > 4000:
        for i in range(0, len(lines), 20):
            chunk = f"<b>💎 Premium Users (page {i//20 + 1}):</b>\n\n" + "\n\n".join(lines[i:i+20])
            await message.reply_text(chunk, disable_web_page_preview=True)
    else:
        await message.reply_text(text, disable_web_page_preview=True)

#========================================================================#

@Client.on_message(filters.command('checkpremium') & filters.private)
async def check_premium_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) != 2:
        return await message.reply_text("<b>Usage:</b> /checkpremium &lt;user_id&gt;")

    try:
        user_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid user ID.")

    try:
        user = await client.get_users(user_id)
        display_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Error fetching user: {e}")

    is_pro = await client.mongodb.is_pro(user_id)
    if is_pro:
        expiry = await client.mongodb.get_expiry_date(user_id)
        expiry_str = expiry.strftime("%d %b %Y at %H:%M") if expiry else "♾️ Permanent"
        await message.reply_text(
            f"💎 <b>Premium User</b>\n\n"
            f"👤 <b>Name:</b> {display_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📅 <b>Expires:</b> {expiry_str}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("♻️ Update Duration", callback_data=f"prem_{user_id}_custom"),
                InlineKeyboardButton("🗑 Remove", callback_data=f"prem_del_{user_id}")
            ]])
        )
    else:
        await message.reply_text(
            f"🆓 <b>Free User</b>\n\n"
            f"👤 <b>Name:</b> {display_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Give Premium", callback_data=f"prem_give_{user_id}")
            ]])
        )

#========================================================================#

@Client.on_callback_query(filters.regex(r"^prem_give_(\d+)$"))
async def prem_give_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Only the owner can do this!", show_alert=True)
    user_id = int(callback_query.data.split("_")[2])
    try:
        user = await client.get_users(user_id)
        display_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    except Exception:
        display_name = str(user_id)
    await callback_query.message.edit_text(
        f"👤 <b>User:</b> {display_name} (<code>{user_id}</code>)\n"
        f"🆓 <b>Free User</b>\n\n<b>Select premium duration:</b>",
        reply_markup=premium_keyboard(user_id)
    )

#========================================================================#

@Client.on_callback_query(filters.regex(r"^prem_del_(\d+)$"))
async def prem_del_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Only the owner can do this!", show_alert=True)
    user_id = int(callback_query.data.split("_")[2])
    await client.mongodb.remove_pro(user_id)
    try:
        user = await client.get_users(user_id)
        display_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
        await client.send_message(user_id, "⚠️ <b>Your premium membership has ended.</b>")
    except Exception:
        display_name = str(user_id)
    await callback_query.message.edit_text(
        f"✅ <b>Premium removed</b> for {display_name} (<code>{user_id}</code>)."
    )
