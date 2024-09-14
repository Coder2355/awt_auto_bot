import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from config import API_ID, API_HASH, BOT_TOKEN, FILE_STORE_BOT, SOURCE_CHANNEL, TARGET_CHANNEL

# Initialize the bot
bot = Client(
    "anime_upload_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# Dictionary to store custom thumbnail
custom_thumbnail = {}

# Helper function to extract anime details from file name
def extract_anime_details(file_name):
    # Example: "One Piece S01E23 1080p.mp4"
    match = re.match(r"(.+?) S(\d+)E(\d+).+?(\d{3,4}p)", file_name)
    if match:
        anime_name = match.group(1)
        season = match.group(2)
        episode = match.group(3)
        quality = match.group(4)
        return anime_name.strip(), season, episode, quality
    return None, None, None, None

# Function to rename the video file
async def rename_file(file_path, anime_name, season, episode, quality):
    new_name = f"{anime_name} S{season}E{episode} {quality}.mp4"
    new_path = os.path.join("downloads", new_name)
    os.rename(file_path, new_path)
    return new_path

# Function to upload file to file store bot and get the link
async def upload_to_file_store(bot, file_path, status_message):
    async with bot:
        await status_message.edit_text("📤 Uploading file to file store bot...")  # Status message for uploading
        sent_message = await bot.send_document(FILE_STORE_BOT, file_path)
        await status_message.edit_text("✅ File uploaded successfully!")
        return sent_message.document.file_id  # File ID is the link to the document

# Function to create poster with button linking to the video file
async def create_poster_with_buttons(bot, chat_id, link, anime_name, season, episode, quality):
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"Watch {anime_name} S{season}E{episode} {quality}", url=f"https://t.me/{FILE_STORE_BOT}?start={link}")]]
    )
    
    caption = f"**{anime_name}**\nSeason {season} - Episode {episode} [{quality}]\n[Watch Now](https://t.me/{FILE_STORE_BOT}?start={link})"
    
    if chat_id in custom_thumbnail:
        await bot.send_photo(chat_id, custom_thumbnail[chat_id], caption=caption, reply_markup=buttons)
    else:
        await bot.send_message(chat_id, caption, reply_markup=buttons)

# Event handler for videos and document files in the source channel
@bot.on_message(filters.channel & filters.chat(SOURCE_CHANNEL) & (filters.video | filters.document))
async def handle_video_or_document(bot, message):
    # Initial status message
    status_message = await message.reply_text("⏳ Processing your file...")

    file_id = message.video.file_id if message.video else message.document.file_id
    file_name = message.video.file_name if message.video else message.document.file_name

    await status_message.edit_text("📥 Downloading file...")  # Update status for downloading
    file_path = await bot.download_media(file_id, file_name=f"downloads/{file_name}")

    # Extract anime details from the file name
    anime_name, season, episode, quality = extract_anime_details(file_name)
    
    if anime_name and season and episode and quality:
        # Rename file with anime details
        new_file_path = await rename_file(file_path, anime_name, season, episode, quality)
        
        # Upload to file store bot and get the link
        link = await upload_to_file_store(bot, new_file_path, status_message)
        
        # Create a poster with buttons linking to the uploaded video
        await create_poster_with_buttons(bot, TARGET_CHANNEL, link, anime_name, season, episode, quality)

        await status_message.edit_text("✅ Process completed successfully!")
    else:
        await status_message.edit_text("⚠️ Failed to extract anime details from the file name.")

# Event handler for images (used as thumbnail)
@bot.on_message(filters.channel & filters.chat(SOURCE_CHANNEL) & filters.photo)
async def handle_thumbnail(bot, message):
    # Save the thumbnail for future use
    custom_thumbnail[message.chat.id] = message.photo.file_id
    await message.reply_text("Thumbnail saved. It will be used for future video uploads.")

# Run the bot
if __name__ == "__main__":
    bot.run()
