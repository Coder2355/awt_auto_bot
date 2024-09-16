import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN, FILE_STORE_CHANNEL_ID, TARGET_CHANNEL_ID, DB_CHANNEL, FILE_STORE_BOT_USERNAME

# Initialize the bot
app = Client("auto_anime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global variable to store the thumbnail path
thumbnail_path = None

# Function to rename and upload video to file store bot's channel
@app.on_message(filters.channel & filters.document)
async def handle_video(client, message):
    global thumbnail_path
    
    if message.chat.id == FILE_STORE_CHANNEL_ID:  # Ensure this is from the source channel
        status_message = await message.reply_text("📥 **Downloading video file...**")
        
        # Step 1: Rename the video
        anime_name = "Anime_Name"
        episode_number = "01"
        quality = "720p"
        new_filename = f"{anime_name}_Episode_{episode_number}_{quality}.mp4"
        
        # Download the video
        video_path = await message.download(file_name=new_filename)
        await status_message.edit_text("✅ **Video downloaded! Renaming file...**")

        # Step 2: Upload to file store bot's database channel
        await status_message.edit_text("📤 **Uploading video to database channel...**")
        uploaded_message = await app.send_document(
            chat_id=DB_CHANNEL,
            document=video_path,
            thumb=thumbnail_path if thumbnail_path else None,  # Only send if thumbnail exists
            caption=f"Renamed Video: {new_filename}",
            progress=progress_callback  # Optional: progress callback function
        )
        
        # Step 3: Retrieve the file store bot link directly from the file store bot's response
        await status_message.edit_text("🔗 **Getting file link from the database channel...**")
        
        # Retrieve the actual link from the caption or text of the uploaded message in the file store bot
        if uploaded_message.caption:
            store_bot_link = uploaded_message.caption  # Extract the link from the caption
        elif uploaded_message.text:
            store_bot_link = uploaded_message.text  # Extract the link from the text
        else:
            await status_message.edit_text("❌ **Failed to get the correct link from the file store bot!**")
            return

        # Step 4: Create the button layout with the correct file store bot link
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📥 Get File", url=store_bot_link)]]
        )
        
        # Step 5: Post to the target channel with the file link and thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            await status_message.edit_text("📤 **Uploading video link to the target channel...**")
            await app.send_photo(
                chat_id=TARGET_CHANNEL_ID,
                photo=thumbnail_path,  # Send the poster image (thumbnail)
                caption=f"New Anime Episode: {anime_name} - Episode {episode_number} [{quality}]",
                reply_markup=buttons
            )
        else:
            await status_message.edit_text("📤 **Uploading video link to the target channel without thumbnail...**")
            await app.send_message(
                chat_id=TARGET_CHANNEL_ID,
                text=f"New Anime Episode: {anime_name} - Episode {episode_number} [{quality}]",
                reply_markup=buttons
            )
        
        # Clean up: Remove the downloaded file
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
