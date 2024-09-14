import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Import config settings
from config import API_ID, API_HASH, BOT_TOKEN, SOURCE_CHANNEL, TARGET_CHANNEL, DB_CHANNEL, TEMP_DIR

app = Client("auto_upload_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ensure download directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


def extract_anime_details(filename):
    # Regular expression pattern for extracting anime details
    anime_pattern = r"(?P<name>.*?)\s*[._-]?[sS](?P<season>\d+)[eE](?P<episode>\d+)[._-]?\[?(?P<quality>\d{3,4}p)?\]?"
    match = re.search(anime_pattern, filename)
    
    if match:
        anime_name = match.group("name").replace('.', ' ').replace('_', ' ').strip()
        season = match.group("season")
        episode = match.group("episode")
        quality = match.group("quality") if match.group("quality") else "Unknown Quality"
        return anime_name, season, episode, quality
    
    return None, None, None, None

# Variable to store the latest thumbnail
thumbnail_path = None

# Handle receiving picture for setting as thumbnail
@app.on_message(filters.photo & filters.channel)
async def handle_thumbnail(client, message):
    global thumbnail_path
    thumbnail_path = await message.download(f"{TEMP_DIR}/thumbnail.jpg")
    await message.reply_text("Thumbnail has been set.")

@app.on_message((filters.video | filters.document) & filters.channel)
async def handle_upload(client, message):
    if message.chat.id != SOURCE_CHANNEL:
        return

    # Initialize the thumbnail_path variable
    global thumbnail_path
    
    # Send downloading message
    download_msg = await message.reply_text("Downloading the file...")

    # Download file
    download_path = await message.download(f"{TEMP_DIR}/")
    await download_msg.edit_text("File downloaded successfully.")

    filename = os.path.basename(download_path)
    
    # Extract anime details from the filename
    anime_name, season, episode, quality = extract_anime_details(filename)

    if not all([anime_name, season, episode, quality]):
        await message.reply_text(
            f"Unable to extract anime details from the filename: {filename}. "
            "Ensure the filename contains 'season', 'episode', and the quality (e.g., 720p) "
            "or follows a standard format such as 'AnimeName_S01E01_[720p]'."
        )
        return

    # Rename the file
    new_filename = f"{anime_name} S{season}E{episode} [{quality}] Tamil.mp4"
    new_filepath = os.path.join(TEMP_DIR, new_filename)
    os.rename(download_path, new_filepath)

    # Send uploading message
    upload_msg = await message.reply_text("Uploading the file...")

    # Upload the renamed video to the database channel (for generating the link)
    db_message = await client.send_video(
        DB_CHANNEL, 
        video=new_filepath, 
        thumb=thumbnail_path or message.video.thumbs[0].file_id if message.video.thumbs else None,
        caption=new_filename
    )

    # Generate the file link
    file_link = f"https://t.me/{DB_CHANNEL}/{db_message.message_id}"

    # Create poster with buttons linking to the video
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Download", url=file_link)]]
    )

    # Upload poster to the target channel with buttons
    await client.send_photo(
        TARGET_CHANNEL,
        photo=thumbnail_path or message.video.thumbs[0].file_id if message.video.thumbs else None,
        caption=f"**{anime_name}**\nSeason {season}, Episode {episode}\nQuality: {quality}",
        reply_markup=buttons
    )

    # Clean up temporary files
    os.remove(new_filepath)
    if thumbnail_path:
        os.remove(thumbnail_path)
        thumbnail_path = None  # Reset thumbnail_path after use

    await upload_msg.edit_text("Video processed and uploaded successfully.")
    
# Start the bot
app.run()
