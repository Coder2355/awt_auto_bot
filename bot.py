import os
import re
from pyrogram.errors import RPCError
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN, FILE_STORE_CHANNEL_ID, TARGET_CHANNEL_ID, DB_CHANNEL, FILE_STORE_BOT_USERNAME

# Initialize the bot
app = Client("auto_anime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global variable to store the thumbnail path
thumbnail_path = None

# Function to rename and upload video to file store bot's channel

# Utility function to validate URLs
def is_valid_url(url):
    # Regular expression to validate URL format
    url_regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(url_regex, url) is not None

@app.on_message(filters.channel & filters.document)
async def handle_video(client, message):
    global thumbnail_path

    if message.chat.id == FILE_STORE_CHANNEL_ID:
        status_message = await message.reply_text("📥 **Downloading video file...**")
        anime_name = "Anime_Name"
        episode_number = "01"
        quality = "720p"
        new_filename = f"{anime_name}_Episode_{episode_number}_{quality}.mp4"
        video_path = await message.download(file_name=new_filename)
        await status_message.edit_text("✅ **Video downloaded! Renaming file...**")
        await status_message.edit_text("📤 **Uploading video to database channel...**")
        
        uploaded_message = await app.send_document(
            chat_id=DB_CHANNEL,
            document=video_path,
            thumb=thumbnail_path if thumbnail_path else None,
            caption=f"Renamed Video: {new_filename}",
        )
        
        # Extract the link from the uploaded message caption
        store_bot_link = uploaded_message.caption if uploaded_message.caption else None
        
        if store_bot_link and is_valid_url(store_bot_link):
            buttons = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📥 Get File", url=store_bot_link)]]
            )
            
            try:
                if thumbnail_path and os.path.exists(thumbnail_path):
                    await app.send_photo(
                        chat_id=TARGET_CHANNEL_ID,
                        photo=thumbnail_path,
                        caption=f"New Anime Episode: {anime_name} - Episode {episode_number} [{quality}]",
                        reply_markup=buttons
                    )
                else:
                    await app.send_message(
                        chat_id=TARGET_CHANNEL_ID,
                        text=f"New Anime Episode: {anime_name} - Episode {episode_number} [{quality}]",
                        reply_markup=buttons
                    )
            except RPCError as e:
                await status_message.edit_text(f"❌ **Failed to send message:** {str(e)}")
        else:
            await status_message.edit_text("❌ **Failed to get a valid file link!**")
        
        os.remove(video_path)
        await status_message.edit_text("✅ **Process completed!**")
        
# Function to handle picture upload for thumbnail and poster image
@app.on_message(filters.photo)
async def handle_thumbnail(client, message):
    global thumbnail_path

    # Download the thumbnail image
    thumbnail_path = await message.download()

    # Send a confirmation message
    await message.reply_text("Thumbnail and poster image added successfully ✅")

# Optional progress callback to show download/upload progress
async def progress_callback(current, total):
    print(f"Progress: {current * 100 / total:.1f}%")

# Run the bot
app.run()
