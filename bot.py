import os
import re
import base64
from pyrogram.errors import RPCError
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN, FILE_STORE_CHANNEL_ID, TARGET_CHANNEL_ID, DB_CHANNEL, FILE_STORE_BOT_USERNAME

# Initialize the bot
app = Client("auto_anime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global variable to store the thumbnail path
thumbnail_path = None


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
        
        # Upload the file to the database (file store bot)
        uploaded_message = await app.send_document(
            chat_id=DB_CHANNEL,
            document=video_path,
            thumb=thumbnail_path if thumbnail_path else None,
            caption=f"Renamed Video: {new_filename}",
        )
        
        # After uploading, construct the exact link
        if uploaded_message:
            file_id = uploaded_message.id  # Get the message ID from uploaded message
            bot_username = "File_store033_bot"  # Replace with your file store bot's username
            
            # Construct the exact link for the button
            file_store_link = f"https://t.me/{bot_username}?start=get-{file_id}"
            
            buttons = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📥 Get File", url=file_store_link)]]
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
                
                await status_message.edit_text("✅ **Process completed successfully!**")
            except Exception as e:
                await status_message.edit_text(f"❌ **Failed to send message:** {str(e)}")
        else:
            await status_message.edit_text("❌ **Failed to upload the file to the database channel!**")
        
        # Remove the local file after processing
        if os.path.exists(video_path):
            os.remove(video_path)
        
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
