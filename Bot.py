# bot.py
"""
Simple Telegram Movie/WebSeries bot (SQLite). 
- Requires python-telegram-bot v13.x (synchronous Updater style)
- Save this file, edit the CONFIG values below, then run: python bot.py
"""

import logging
import sqlite3
import datetime
from telegram import (
    Bot, Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler, CallbackContext
)

# ----------------- CONFIG: Edit these -----------------
BOT_TOKEN =7838817912:AAFVWw3P4gaNOiKDC5dHMQU-G5zwFN5RIvw "PASTE_YOUR_BOT_TOKEN_HERE"
CHANNEL_USERNAME =@Moviemakersch "@YourChannelUsername"   # OR numeric channel id like -1001234567890
ADMIN_ID = No  # put your telegram numeric user id here after you find it (or leave None and use /myid)
# -----------------------------------------------------

# Conversation states for /addmovie
(
    TITLE, TYPE, RELEASE, LANGUAGE, POSTER, WATCHLINK, DESCRIPTION, CONFIRM
) = range(8)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database helpers ---
def init_db():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        kind TEXT NOT NULL,
        release_date TEXT,
        language TEXT,
        poster_url TEXT,
        watch_link TEXT,
        description TEXT,
        added_by INTEGER,
        added_at TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_item(data, added_by):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('''
    INSERT INTO items (title, kind, release_date, language, poster_url, watch_link, description, added_by, added_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['title'], data['kind'], data.get('release_date',''), data.get('language',''),
        data.get('poster_url',''), data.get('watch_link',''), data.get('description',''),
        added_by, datetime.datetime.utcnow().isoformat()
    ))
    conn.commit()
    rowid = c.lastrowid
    conn.close()
    return rowid

def search_items_by_title(query):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    q = f"%{query}%"
    c.execute("SELECT id, title, kind, release_date, language FROM items WHERE title LIKE ? ORDER BY id DESC", (q,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_item_by_id(item_id):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute("SELECT id, title, kind, release_date, language, poster_url, watch_link, description FROM items WHERE id=?", (item_id,))
    row = c.fetchone()
    conn.close()
    return row

def latest_items(limit=5):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute("SELECT id, title, kind, release_date, language FROM items ORDER BY added_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# --- Utility ---
def is_member_of_channel(bot: Bot, user_id: int):
    """
    Returns True if user_id is a member (or admin) of CHANNEL_USERNAME.
    NOTE: Bot must be admin in the channel for reliable checks.
    """
    try:
        chat = bot.get_chat(CHANNEL_USERNAME)
        status = bot.get_chat_member(chat.id, user_id).status
        # accepted statuses: 'creator','administrator','member','restricted'
        return status in ('creator', 'administrator', 'member', 'restricted')
    except Exception as e:
        logger.warning("Membership check failed: %s", e)
        return False

def movie_post_caption(row):
    # row: (id, title, kind, release_date, language, poster_url, watch_link, description)
    id_, title, kind, release_date, language, poster_url, watch_link, description = row
    text = f"*{title}*  — _{kind}_\n"
    if release_date:
        text += f"Release: {release_date}\n"
    if language:
        text += f"Language: {language}\n"
    if description:
        text += f"\n{description}\n"
    text += f"\nID: {id_}"
    return text

def send_movie_to_channel(context: CallbackContext, item_row):
    """
    Sends the movie item to the channel (as admin).
    item_row should be the full row as returned by get_item_by_id.
    """
    bot = context.bot
    id_, title, kind, release_date, language, poster_url, watch_link, description = item_row
    caption = movie_post_caption(item_row)
    keyboard = []
    if watch_link:
        keyboard.append([InlineKeyboardButton("Watch / Trailer", url=watch_link)])
    keyboard_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    try:
        if poster_url:
            bot.send_photo(chat_id=CHANNEL_USERNAME, photo=poster_url, caption=caption, parse_mode='Markdown', reply_markup=keyboard_markup)
        else:
            bot.send_message(chat_id=CHANNEL_USERNAME, text=caption, parse_mode='Markdown', reply_markup=keyboard_markup)
        return True
    except Exception as e:
        logger.error("Failed to send to channel: %s", e)
        return False

# --- Handlers ---
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    bot = context.bot
    if is_member_of_channel(bot, user.id):
        keyboard = ReplyKeyboardMarkup(
            [["/search", "/browse"], ["/addmovie (admin)", "/help"]],
            resize_keyboard=True
        )
        update.message.reply_text(f"Welcome {user.first_name}! You are a member of the channel. Use /search to find movies or /browse to see latest.", reply_markup=keyboard)
    else:
        # user not a member — ask them to join the channel
        join_text = f"Hello {user.first_name}!\nTo use this bot you must first join the channel {CHANNEL_USERNAME}.\n\nPlease join the channel and then press the *I joined* button."
        keyboard = ReplyKeyboardMarkup([["I joined"]], resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(join_text, reply_markup=keyboard, parse_mode='Markdown')

def joined_check(update: Update, context: CallbackContext):
    """User pressed 'I joined' text button; re-check membership."""
    user = update.effective_user
    bot = context.bot
    if is_member_of_channel(bot, user.id):
        update.message.reply_text("Thanks — membership confirmed. Now you can use /search or /browse.")
    else:
        update.message.reply_text(f"I still can't see you as a member of {CHANNEL_USERNAME}. Make sure you joined that channel and that the bot is admin there.")

def help_cmd(update: Update, context: CallbackContext):
    help_text = (
        "/start - start & membership check\n"
        "/search - search by title\n"
        "/browse - see latest additions\n"
        "/addmovie - (admin only) add a movie/series/cartoon\n"
        "/myid - get your Telegram numeric id (useful for ADMIN_ID)\n"
    )
    update.message.reply_text(help_text)

def myid(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f"Your numeric Telegram user id is: {user.id}\nUse this value for ADMIN_ID if you want to hardcode admin in config.")

# ----------- /addmovie conversation (admin only) ----------
def addmovie_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if ADMIN_ID and user.id != ADMIN_ID:
        update.message.reply_text("Only the admin can add items.")
        return ConversationHandler.END
    update.message.reply_text("Let's add a new item.\nWhat is the *title* of the movie/web-series/cartoon? (send text)", parse_mode='Markdown')
    context.user_data['new_item'] = {}
    return TITLE

def addmovie_title(update: Update, context: CallbackContext):
    context.user_data['new_item']['title'] = update.message.text.strip()
    update.message.reply_text("Type? (Reply with one of: Movie / WebSeries / Cartoon)")
    return TYPE

def addmovie_type(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    context.user_data['new_item']['kind'] = text
    update.message.reply_text("Release date (YYYY-MM-DD) or just year (e.g. 2023). If unknown, send '-'")
    return RELEASE

def addmovie_release(update: Update, context: CallbackContext):
    context.user_data['new_item']['release_date'] = update.message.text.strip()
    update.message.reply_text("Language (e.g. Hindi, English). If multiple, separate by commas. If unknown, send '-'")
    return LANGUAGE

def addmovie_language(update: Update, context: CallbackContext):
    context.user_data['new_item']['language'] = update.message.text.strip()
    update.message.reply_text("Poster image URL (direct image link) OR send 'skip' to add later.")
    return POSTER

def addmovie_poster(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text.lower() != 'skip':
        context.user_data['new_item']['poster_url'] = text
    else:
        context.user_data['new_item']['poster_url'] = ''
    update.message.reply_text("Official watch/trailer link (YouTube, streaming page) or 'skip'.")
    return WATCHLINK

def addmovie_watchlink(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text.lower() != 'skip':
        context.user_data['new_item']['watch_link'] = text
    else:
        context.user_data['new_item']['watch_link'] = ''
    update.message.reply_text("Short description (1-2 lines) or 'skip'.")
    return DESCRIPTION

def addmovie_description(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text.lower() != 'skip':
        context.user_data['new_item']['description'] = text
    else:
        context.user_data['new_item']['description'] = ''

    preview = context.user_data['new_item']
    summary = (
        f"Title: {preview.get('title')}\n"
        f"Type: {preview.get('kind')}\n"
        f"Release: {preview.get('release_date')}\n"
        f"Language: {preview.get('language')}\n"
        f"Poster: {preview.get('poster_url') or 'none'}\n"
        f"Link: {preview.get('watch_link') or 'none'}\n"
        f"Desc: {preview.get('description') or 'none'}\n\n"
        "Send 'confirm' to save and post, or 'cancel' to abort."
    )
    update.message.reply_text(summary)
    return CONFIRM

def addmovie_confirm(update: Update, context: CallbackContext):
    text = update.message.text.strip().lower()
    if text == 'confirm':
        new_item = context.user_data.get('new_item', {})
        # Save to DB
        added_by = update.effective_user.id
        item_id = save_item(new_item, added_by)
        row = get_item_by_id(item_id)
        success = send_movie_to_channel(context, row)
        if success:
            update.message.reply_text("Saved and posted to your channel ✅")
        else:
            update.message.reply_text("Saved in the bot DB but failed to post to channel. Make sure the bot is admin in the channel and CHANNEL_USERNAME is correct.")
        context.user_data.pop('new_item', None)
        return ConversationHandler.END
    else:
        update.message.reply_text("Aborted. Nothing was saved.")
        context.user_data.pop('new_item', None)
        return ConversationHandler.END

def addmovie_cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Add item cancelled.")
    context.user_data.pop('new_item', None)
    return ConversationHandler.END

# ----- Search flow -----
def search_start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me the title (or part of it) to search:")
    return 0

def search_do(update: Update, context: CallbackContext):
    q = update.message.text.strip()
    results = search_items_by_title(q)
    if not results:
        update.message.reply_text("No results found.")
        return ConversationHandler.END
    text = "Search results:\n"
    for r in results[:10]:
        id_, title, kind, release, language = r
        text += f"• {title} ({kind}) — ID: {id_}\n"
    text += "\nTo view details send: ID <number>\nExample: `ID 3`"
    update.message.reply_text(text, parse_mode='Markdown')
    return ConversationHandler.END

def view_by_id(update: Update, context: CallbackContext):
    txt = update.message.text.strip()
    if txt.lower().startswith('id '):
        try:
            item_id = int(txt.split()[1])
            row = get_item_by_id(item_id)
            if not row:
                update.message.reply_text("No item with that ID.")
                return
            id_, title, kind, release_date, language, poster_url, watch_link, description = row
            caption = movie_post_caption(row)
            keyboard = []
            if watch_link:
                keyboard.append([InlineKeyboardButton("Watch / Trailer", url=watch_link)])
            if poster_url:
                update.message.reply_photo(photo=poster_url, caption=caption, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
            else:
                update.message.reply_text(caption, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
        except Exception as e:
            update.message.reply_text("Couldn't parse ID. Use format: `ID 3`")
    # else ignore

# ----- Browse latest -----
def browse(update: Update, context: CallbackContext):
    rows = latest_items(5)
    if not rows:
        update.message.reply_text("No items yet.")
        return
    text = "Latest items:\n"
    for r in rows:
        id_, title, kind, release, language = r
        text += f"• {title} ({kind}) — ID: {id_}\n"
    text += "\nView details: send `ID <number>`"
    update.message.reply_text(text, parse_mode='Markdown')

# ----- main -----
def main():
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # basic commands
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help_cmd))
    dp.add_handler(CommandHandler('myid', myid))
    dp.add_handler(CommandHandler('browse', browse))
    dp.add_handler(MessageHandler(Filters.regex(r'^(I joined)$'), joined_check))
    dp.add_handler(MessageHandler(Filters.regex(r'^(ID \d+)$'), view_by_id))

    # search conversation
    search_conv = ConversationHandler(
        entry_points=[CommandHandler('search', search_start)],
        states={0: [MessageHandler(Filters.text & ~Filters.command, search_do)]},
        fallbacks=[]
    )
    dp.add_handler(search_conv)

    # addmovie conversation (admin)
    add_conv = ConversationHandler(
        entry_points=[CommandHandler('addmovie', addmovie_start)],
        states={
            TITLE: [MessageHandler(Filters.text & ~Filters.command, addmovie_title)],
            TYPE: [MessageHandler(Filters.text & ~Filters.command, addmovie_type)],
            RELEASE: [MessageHandler(Filters.text & ~Filters.command, addmovie_release)],
            LANGUAGE: [MessageHandler(Filters.text & ~Filters.command, addmovie_language)],
            POSTER: [MessageHandler(Filters.text & ~Filters.command, addmovie_poster)],
            WATCHLINK: [MessageHandler(Filters.text & ~Filters.command, addmovie_watchlink)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, addmovie_description)],
            CONFIRM: [MessageHandler(Filters.text & ~Filters.command, addmovie_confirm)],
        },
        fallbacks=[CommandHandler('cancel', addmovie_cancel)]
    )
    dp.add_handler(add_conv)

    updater.start_polling()
    logger.info("Bot started. Press Ctrl+C to stop.")
    updater.idle()

if __name__ == "__main__":
    main()
