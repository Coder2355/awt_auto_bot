import os
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelInvalid, FloodWait, PeerIdInvalid

# Import config settings
from config import API_ID, API_HASH, BOT_TOKEN, SOURCE_CHANNEL, TARGET_CHANNEL, FILE_STORE_CHANNEL, TEMP_DIR

app = Client("auto_upload_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ensure download directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def extract_anime_details(filename):
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

@app.on_message(filters.photo & filters.channel)
async def handle_thumbnail(client, message):
    global thumbnail_path
    thumbnail_path = await message.download(f"{TEMP_DIR}/thumbnail.jpg")
    await message.reply_text("Thumbnail has been set.")

@app.on_message((filters.video | filters.document) & filters.channel)
async def handle_upload(client, message):
    if message.chat.id != SOURCE_CHANNEL:
        return

    global thumbnail_path
    thumbnail_path = None

    download_msg = await message.reply_text("Downloading the file...")

    try:
        download_path = await message.download(f"{TEMP_DIR}/")
        await download_msg.edit_text("File downloaded successfully.")

        filename = os.path.basename(download_path)
        anime_name, season, episode, quality = extract_anime_details(filename)

        if not all([anime_name, season, episode, quality]):
            await message.reply_text(
                f"Unable to extract anime details from the filename: {filename}. "
                "Ensure the filename contains 'season', 'episode', and the quality (e.g., 720p) "
                "or follows a standard format such as 'AnimeName_S01E01_[720p]'."
            )
            return

        new_filename = f"{anime_name} S{season}E{episode} [{quality}] Tamil.mp4"
        new_filepath = os.path.join(TEMP_DIR, new_filename)
        os.rename(download_path, new_filepath)

        upload_msg = await message.reply_text("Uploading the file...")

        if message.video and message.video.thumbs:
            thumb_id = message.video.thumbs[0].file_id
        elif message.document and message.document.thumbs:
            thumb_id = message.document.thumbs[0].file_id
        else:
            thumb_id = thumbnail_path
        
        if thumb_id:
            thumbnail_path = await client.download_media(thumb_id, file_name=f"{TEMP_DIR}/thumb.jpg")
        else:
            thumbnail_path = None

        # Debugging the channel ID and object access
        print(f"Uploading video to channel: {FILE_STORE_CHANNEL}")

        file_message = await client.send_video(
            FILE_STORE_CHANNEL, 
            video=new_filepath, 
            thumb=thumbnail_path,  
            caption=new_filename
        )

        print(f"File message object: {file_message}")

        message_id = getattr(file_message, 'message_id', None)
        if not message_id:
            await message.reply_text("Failed to get the message ID for the uploaded file.")
            return

        file_link = f"https://t.me/{FILE_STORE_CHANNEL}/{message_id}"

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Download", url=file_link)]]
        )

        await client.send_photo(
            TARGET_CHANNEL,
            photo=thumbnail_path,  
            caption=f"**{anime_name}**\nSeason {season}, Episode {episode}\nQuality: {quality}",
            reply_markup=buttons
        )

        os.remove(new_filepath)
        if thumbnail_path:
            os.remove(thumbnail_path)
            thumbnail_path = None

        await upload_msg.edit_text("Video processed and uploaded successfully.")

    except PeerIdInvalid:
        await message.reply_text("The channel ID or username is invalid. Please check the configuration.")
    except ChannelInvalid:
        await message.reply_text("The channel ID or username is invalid. Please check the configuration.")
    except FloodWait as e:
        await message.reply_text(f"Rate limit exceeded. Please wait for {e.x} seconds.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

app.run()
