from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import MSG_EFFECT

try:
    from pyromod.exceptions import ListenerTimeout
except ImportError:
    try:
        from pyrogram.errors.pyromod import ListenerTimeout
    except ImportError:
        ListenerTimeout = TimeoutError

# =============================================================== #

@Client.on_message(filters.command('db') & filters.private)
async def db_channels_command(client: Client, message: Message):
    """Direct command to manage DB channels"""
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)

    db_channels = getattr(client, 'db_channels', {})
    primary_db = getattr(client, 'primary_db_channel', client.db)

    if db_channels:
        channel_list = []
        for channel_id_str, channel_data in db_channels.items():
            channel_name = channel_data.get('name', 'ᴜɴᴋɴᴏᴡɴ')
            is_primary = "✓ ᴘʀɪᴍᴀʀʏ" if channel_data.get('is_primary', False) else "• sᴇᴄᴏɴᴅᴀʀʏ"
            is_active = "✓ ᴀᴄᴛɪᴠᴇ" if channel_data.get('is_active', True) else "✗ ɪɴᴀᴄᴛɪᴠᴇ"
            channel_list.append(
                f"• `{channel_name}` (`{channel_id_str}`)\n  {is_primary} | {is_active}"
            )

        channels_display = "\n\n".join(channel_list)
    else:
        channels_display = "_ɴᴏ ᴀᴅᴅɪᴛɪᴏɴᴀʟ ᴅᴀᴛᴀʙᴀsᴇ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ_"

    msg = f"""<blockquote>✦ ᴅᴀᴛᴀʙᴀsᴇ ᴄʜᴀɴɴᴇʟs ᴍᴀɴᴀɢᴇᴍᴇɴᴛ</blockquote>

›› **ᴄᴜʀʀᴇɴᴛ ᴘʀɪᴍᴀʀʏ ᴅʙ:** `{primary_db}`
›› **ᴛᴏᴛᴀʟ ᴅʙ ᴄʜᴀɴɴᴇʟs:** `{len(db_channels)}`

**ᴄᴏɴғɪɢᴜʀᴇᴅ ᴄʜᴀɴɴᴇʟs:**
{channels_display}

__ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴅᴀᴛᴀʙᴀsᴇ ᴄʜᴀɴɴᴇʟs!__
"""

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('›› ᴀᴅᴅ ᴅʙ ᴄʜᴀɴɴᴇʟ', callback_data='add_db_channel')],
        [InlineKeyboardButton('›› ʀᴇᴍᴏᴠᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ', callback_data='rm_db_channel')],
        [InlineKeyboardButton('›› sᴇᴛ ᴘʀɪᴍᴀʀʏ', callback_data='set_primary_db')],
        [InlineKeyboardButton('›› ᴛᴏɢɢʟᴇ sᴛᴀᴛᴜs', callback_data='toggle_db_status')],
        [InlineKeyboardButton('›› ᴠɪᴇᴡ ᴅᴇᴛᴀɪʟs', callback_data='db_details')]
    ])

    await message.reply(msg, reply_markup=reply_markup)

# =============================================================== #

@Client.on_callback_query(filters.regex("^db_details$"))
async def db_details(client, query):
    if query.from_user.id not in client.admins:
        return await query.answer('✗ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!', show_alert=True)

    await query.answer()

    db_channels = getattr(client, 'db_channels', {})
    primary_db = getattr(client, 'primary_db_channel', client.db)

    msg = f"""<blockquote>✦ ᴅᴇᴛᴀɪʟᴇᴅ ᴅʙ ᴄʜᴀɴɴᴇʟs ɪɴғᴏʀᴍᴀᴛɪᴏɴ</blockquote>

›› **ᴘʀɪᴍᴀʀʏ ᴅʙ:** `{primary_db}`
›› **ᴛᴏᴛᴀʟ:** `{len(db_channels)}`
"""

    if db_channels:
        for i, (channel_id_str, channel_data) in enumerate(db_channels.items(), 1):
            channel_name = channel_data.get('name', 'ᴜɴᴋɴᴏᴡɴ')
            is_primary = channel_data.get('is_primary', False)
            is_active = channel_data.get('is_active', True)
            added_by = channel_data.get('added_by', 'ᴜɴᴋɴᴏᴡɴ')

            msg += f"""
**{i}. {channel_name}**
• ID: `{channel_id_str}`
• Status: {'ᴘʀɪᴍᴀʀʏ' if is_primary else 'sᴇᴄᴏɴᴅᴀʀʏ'}
• Active: {'ʏᴇs' if is_active else 'ɴᴏ'}
• Added by: `{added_by}`
"""

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('‹ ʙᴀᴄᴋ', callback_data='back_to_db_management')]
    ])

    await query.message.edit_text(msg, reply_markup=reply_markup)

# =============================================================== #

@Client.on_callback_query(filters.regex("^back_to_db_management$"))
async def back_to_db_management(client, query):
    if query.from_user.id not in client.admins:
        return await query.answer('✗ ᴀᴅᴍɪɴs ᴏɴʟʏ!', show_alert=True)

    await query.answer()

    db_channels = getattr(client, 'db_channels', {})
    primary_db = getattr(client, 'primary_db_channel', client.db)

    if db_channels:
        channel_list = []
        for channel_id_str, channel_data in db_channels.items():
            channel_name = channel_data.get('name', 'ᴜɴᴋɴᴏᴡɴ')
            is_primary = "✓ ᴘʀɪᴍᴀʀʏ" if channel_data.get('is_primary') else "• sᴇᴄᴏɴᴅᴀʀʏ"
            is_active = "✓ ᴀᴄᴛɪᴠᴇ" if channel_data.get('is_active') else "✗ ɪɴᴀᴄᴛɪᴠᴇ"
            channel_list.append(
                f"• `{channel_name}` (`{channel_id_str}`)\n  {is_primary} | {is_active}"
            )

        channels_display = "\n\n".join(channel_list)
    else:
        channels_display = "_ɴᴏ ᴄʜᴀɴɴᴇʟs_"

    msg = f"""<blockquote>✦ ᴅᴀᴛᴀʙᴀsᴇ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ</blockquote>

›› **ᴘʀɪᴍᴀʀʏ:** `{primary_db}`
›› **ᴛᴏᴛᴀʟ:** `{len(db_channels)}`

**ᴄʜᴀɴɴᴇʟs:**
{channels_display}
"""

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('›› ᴀᴅᴅ ᴅʙ ᴄʜᴀɴɴᴇʟ', callback_data='add_db_channel')],
        [InlineKeyboardButton('›› ʀᴇᴍᴏᴠᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ', callback_data='rm_db_channel')],
        [InlineKeyboardButton('›› sᴇᴛ ᴘʀɪᴍᴀʀʏ', callback_data='set_primary_db')],
        [InlineKeyboardButton('›› ᴛᴏɢɢʟᴇ', callback_data='toggle_db_status')],
        [InlineKeyboardButton('›› ᴅᴇᴛᴀɪʟs', callback_data='db_details')]
    ])

    await query.message.edit_text(msg, reply_markup=reply_markup)

# =============================================================== #

@Client.on_callback_query(filters.regex('^home$'))
async def home(client: Client, query: CallbackQuery):
    buttons = [
        [InlineKeyboardButton("Help", callback_data="about"),
         InlineKeyboardButton("Close", callback_data="close")]
    ]

    if query.from_user.id in client.admins:
        buttons.insert(0, [
            InlineKeyboardButton("⛩️ ꜱᴇᴛᴛɪɴɢꜱ ⛩️", callback_data="settings")
        ])

    new_text = client.messages.get('START', 'No Start Message').format(
        first=query.from_user.first_name,
        last=query.from_user.last_name,
        username='@' + query.from_user.username if query.from_user.username else None,
        mention=query.from_user.mention,
        id=query.from_user.id
    )

    if query.message.text != new_text:
        await query.message.edit_text(
            text=new_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await query.answer("Already on this page")

# =============================================================== #

@Client.on_callback_query(filters.regex('^about$'))
async def about(client: Client, query: CallbackQuery):
    buttons = [[
        InlineKeyboardButton("Back", callback_data="home"),
        InlineKeyboardButton("Close", callback_data="close")
    ]]

    await query.message.edit_text(
        text=client.messages.get('ABOUT', 'No Start Message').format(
            owner_id=client.owner,
            bot_username=client.username,
            first=query.from_user.first_name,
            last=query.from_user.last_name,
            username='@' + query.from_user.username if query.from_user.username else None,
            mention=query.from_user.mention,
            id=query.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# =============================================================== #

@Client.on_callback_query(filters.regex('^close$'))
async def close(client: Client, query: CallbackQuery):
    await query.message.delete()
    try:
        await query.message.reply_to_message.delete()
    except:
        pass

# =============================================================== #

@Client.on_message(filters.command('ban'))
async def ban(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)

    try:
        user_ids = message.text.split(maxsplit=1)[1]
        c = 0
        for user_id in user_ids.split():
            user_id = int(user_id)
            c += 1

            if user_id in client.admins:
                continue

            if not await client.mongodb.present_user(user_id):
                await client.mongodb.add_user(user_id, True)
            else:
                await client.mongodb.ban_user(user_id)

        return await message.reply(f"__{c} users have been banned!__")

    except Exception as e:
        return await message.reply(f"**Error:** `{e}`")

# =============================================================== #

@Client.on_message(filters.command('unban'))
async def unban(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)

    try:
        user_ids = message.text.split(maxsplit=1)[1]
        c = 0

        for user_id in user_ids.split():
            user_id = int(user_id)
            c += 1

            if user_id in client.admins:
                continue

            if not await client.mongodb.present_user(user_id):
                await client.mongodb.add_user(user_id)
            else:
                await client.mongodb.unban_user(user_id)

        return await message.reply(f"__{c} users have been unbanned!__")

    except Exception as e:
        return await message.reply(f"**Error:** `{e}`")

# =============================================================== #
