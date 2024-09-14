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
    
    
    if message.chat.username != SOURCE_CHANNEL:
        return

    # Initialize the thumbnail_path variable
    global thumbnail_path
    thumbnail_path = None  # Initialize as None at the start

    # Send downloading message
    download_msg = await message.reply_text("Downloading the file...")

    # Download the video or document
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

    # Handle the thumbnail
    if message.video and message.video.thumbs:
        thumb_id = message.video.thumbs[0].file_id
    elif message.document and message.document.thumbs:
        thumb_id = message.document.thumbs[0].file_id
    else:
        thumb_id = thumbnail_path  # Custom thumbnail if provided
    
    if thumb_id:
        # Download the thumbnail locally
        thumbnail_path = await client.download_media(thumb_id, file_name=f"{TEMP_DIR}/thumb.jpg")
    else:
        thumbnail_path = None  # No thumbnail available

    # Upload the renamed video to the database channel (for generating the link)
    try:
        db_message = await client.send_video(
            DB_CHANNEL, 
            video=new_filepath, 
            thumb=thumbnail_path,  # Use the downloaded thumbnail
            caption=new_filename
        )
    except Exception as e:
        await upload_msg.edit_text(f"Failed to upload video: {e}")
        return

    # Generate the file link
    file_link = f"https://t.me/{DB_CHANNEL}/{db_message.message_id}"

    # Create poster with buttons linking to the video
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Download", url=file_link)]]
    )

    # Upload poster to the target channel with buttons
    try:
        await client.send_photo(
            TARGET_CHANNEL,
            photo=thumbnail_path,  # Use the thumbnail as the poster image
            caption=f"**{anime_name}**\nSeason {season}, Episode {episode}\nQuality: {quality}",
            reply_markup=buttons
        )
    except Exception as e:
        await upload_msg.edit_text(f"Failed to upload poster: {e}")
        return

    # Clean up temporary files
    os.remove(new_filepath)
    if thumbnail_path:
        os.remove(thumbnail_path)
        thumbnail_path = None  # Reset thumbnail_path after use

    await upload_msg.edit_text("Video processed and uploaded successfully.")
    
# Start the bot
app.run()
