import asyncio
import re
import os
from pyrogram import Client, filters
from pyrogram.errors import ChatWriteForbidden
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, SOURCE_CHANNEL, TARGET_CHANNEL, FILE_STORE_BOT

# Initialize bots
bot = Client("anime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = Client("file_store_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_anime_details(file_name):
    print(f"Received file name: {file_name}")  # Debug: Print received file name
    # Regex pattern to extract anime details
    match = re.match(r"(.+?)\s+S(\d{2})E(\d{2})\s+(\d{3,4}p)", file_name, re.IGNORECASE)
    if match:
        anime_name = match.group(1).strip()
        season = match.group(2)
        episode = match.group(3)
        quality = match.group(4)
        print(f"Extracted details: Name={anime_name}, Season={season}, Episode={episode}, Quality={quality}")  # Debug: Print extracted details
        return anime_name, season, episode, quality
    print("Regex match failed.")  # Debug: Indicate failure
    return None, None, None, None

async def rename_file(file_path, anime_name, season, episode, quality):
    new_file_name = f"{anime_name} S{season}E{episode} {quality}.mp4"
    new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
    os.rename(file_path, new_file_path)
    return new_file_path

async def upload_to_file_store(file_path, status_message):
    await status_message.edit_text("📤 Uploading file to the file store bot...")
    async with file_store_bot:
        file_id = await file_store_bot.send_document(
            chat_id=FILE_STORE_BOT,
            document=file_path
        )
    file_link = f"https://t.me/{FILE_STORE_BOT}/{file_id.message_id}"
    return file_link

async def create_poster_with_buttons(file_link, target_channel, anime_name, season, episode, quality):
    poster_text = f"Watch {anime_name} - Season {season}, Episode {episode} ({quality})"
    buttons = [[
        Button.url("Watch Video", file_link)
    ]]
    async with bot:
        await bot.send_message(
            chat_id=target_channel,
            text=poster_text,
            reply_markup=buttons
        )

@bot.on_message(filters.channel & filters.chat(SOURCE_CHANNEL) & (filters.video | filters.document))
async def handle_video_or_document(bot, message: Message):
    # Initial status message
    status_message = await message.reply_text("⏳ Processing your file...")

    file_id = message.video.file_id if message.video else message.document.file_id
    file_name = message.video.file_name if message.video else message.document.file_name

    print(f"Processing file: {file_name}")  # Debug: Print the file name being processed

    await status_message.edit_text("📥 Downloading file...")
    file_path = await bot.download_media(file_id, file_name=f"downloads/{file_name}")

    # Extract anime details from the file name
    anime_name, season, episode, quality = extract_anime_details(file_name)
    
    if anime_name and season and episode and quality:
        # Rename file with anime details
        new_file_path = await rename_file(file_path, anime_name, season, episode, quality)
        
        # Upload to the file store bot and get the link
        link = await upload_to_file_store(new_file_path, status_message)
        
        # Create a poster with buttons linking to the uploaded video
        await create_poster_with_buttons(link, TARGET_CHANNEL, anime_name, season, episode, quality)

        await status_message.edit_text("✅ Process completed successfully!")
    else:
        await status_message.edit_text("⚠️ Failed to extract anime details from the file name.")

if __name__ == "__main__":
    bot.run()
    app.run()
