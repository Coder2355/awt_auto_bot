# file_store_bot.py

from pyrogram import Client, filters
import os
import config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Initialize the bot for file storage
file_store_bot = Client(
    "file_store_bot",
    api_id=os.getenv("API_ID"),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("FILE_STORE_BOT_TOKEN")
)

# Set the database channel where files will be stored
DATABASE_CHANNEL = int(os.getenv("DATABASE_CHANNEL_ID"))

# Function to handle file uploads (documents or videos) and store them in the database channel
@file_store_bot.on_message(filters.private & (filters.document | filters.video))
async def store_file(bot, message):
    file_id = message.document.file_id if message.document else message.video.file_id
    file_name = message.document.file_name if message.document else message.video.file_name
    
    # Forward the file to the database channel
    forwarded_message = await message.forward(DATABASE_CHANNEL)

    # Create a button that links to the forwarded message in the database channel
    file_link = f"https://t.me/c/{DATABASE_CHANNEL}/{forwarded_message.message_id}"
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Download File", url=file_link)]]
    )

    # Reply to the user with the file link
    await message.reply_text(
        f"File '{file_name}' has been stored!\n[Download here]({file_link})",
        reply_markup=buttons,
        disable_web_page_preview=True
    )

# Run the file store bot
if __name__ == "__main__":
    file_store_bot.run()
