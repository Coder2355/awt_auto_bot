# file_store_bot.py

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

# Initialize the bot for file storage
file_store_bot = Client(
    "file_store_bot",
    api_id=os.getenv("API_ID"),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("FILE_STORE_BOT_TOKEN")
)

# Dictionary to store file links and file names
file_storage = {}

# Function to handle file uploads (documents or videos)
@file_store_bot.on_message(filters.private & (filters.document | filters.video))
async def store_file(bot, message):
    file_id = message.document.file_id if message.document else message.video.file_id
    file_name = message.document.file_name if message.document else message.video.file_name

    # Store the file ID and file name in the dictionary
    file_storage[file_name] = file_id

    # Create a button to retrieve the file
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Download File", url=f"https://t.me/{bot.get_me().username}?start={file_id}")]]
    )

    # Reply with a message that contains the file ID and button to download
    await message.reply_text(
        f"File '{file_name}' has been stored!\nFile ID: `{file_id}`",
        reply_markup=buttons
    )

# Function to send stored file when link/button is pressed
@file_store_bot.on_message(filters.command("start"))
async def send_stored_file(bot, message):
    # Extract file ID from the start command (e.g. /start file_id)
    file_id = message.command[1] if len(message.command) > 1 else None

    if file_id and file_id in file_storage.values():
        # Send the file based on the file ID
        await bot.send_document(message.chat.id, file_id)
    else:
        await message.reply_text("Invalid file link or file no longer exists.")

# Run the file store bot
if __name__ == "__main__":
    file_store_bot.run()
