import re
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config  # Import from config.py

# Initialize the bot client using Config class
bot = Client(
    "anime_auto_uploader",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Pattern to extract anime details from file name
anime_pattern = re.compile(r"(?P<name>.+?)\s*[Ee]p(?:isode)?\s*(?P<episode>\d+)\s*.*?(?P<quality>\d+p)")

# Handler for pictures sent to the bot for setting as thumbnail
@bot.on_message(filters.photo & filters.private)
async def set_thumbnail(client, message):
    # Save the photo as the thumbnail
    await message.download(Config.THUMBNAIL_PATH)
    await message.reply_text("Thumbnail added successfully ✅")

# Handler for video or document files sent to the source channel
@bot.on_message(filters.channel & (filters.video | filters.document) & filters.chat(Config.SOURCE_CHANNEL))
async def auto_upload(client, message):
    # Extracting details from the file name
    file_name = message.video.file_name if message.video else message.document.file_name

    # Debugging: Log the received file name
    print(f"Received file: {file_name}")

    # Try to match the pattern for anime details (name, episode, quality)
    match = anime_pattern.search(file_name)

    if match:
        anime_name = match.group("name").strip()
        episode_num = match.group("episode")
        quality = match.group("quality")

        # Rename the video with new naming convention
        new_file_name = f"{anime_name}_Episode_{episode_num}_{quality}_Tamil.mp4"

        # Custom caption with anime details
        caption = f"Anime : {anime_name}\nEpisode {episode_num} Added ✅\nQuality: {quality}\n"
        caption += "Enna quality venumo click pannunga\nFile varum ✅"

        # Buttons for different quality options
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("720p", callback_data="720p"),
                 InlineKeyboardButton("1080p", callback_data="1080p")]
            ]
        )

        # Send a status message that file forwarding is starting
        status_message = await message.reply_text("Forwarding file...")

        # Check if the thumbnail exists
        if os.path.exists(Config.THUMBNAIL_PATH):
            thumb = Config.THUMBNAIL_PATH
        else:
            thumb = None

        try:
            # Send the renamed file to the file store bot
            if message.video:
                print(f"Forwarding video to file store bot with new name: {new_file_name}")
                file_message = await client.send_video(
                    Config.FILE_STORE_BOT,
                    video=message.video.file_id,
                    caption=f"Stored: {new_file_name}",
                    thumb=thumb  # Add thumbnail if exists
                )
            else:
                print(f"Forwarding document to file store bot with new name: {new_file_name}")
                file_message = await client.send_document(
                    Config.FILE_STORE_BOT,
                    document=message.document.file_id,
                    caption=f"Stored: {new_file_name}",
                    thumb=thumb  # Add thumbnail if exists
                )

            # Update status message to indicate successful forwarding
            await status_message.edit_text("File forwarded successfully! Uploading...")

            # Get the generated link for the stored file
            file_link = file_message.link

            # Forward the video/document with the new link to the target channel
            await client.send_message(
                Config.TARGET_CHANNEL,
                text=f"{caption}\n[Download Link]({file_link})",
                reply_markup=buttons,
                disable_web_page_preview=True
            )

            # Update the status message to indicate upload is complete
            await status_message.edit_text("Upload complete.")
            print(f"Uploaded {anime_name} Episode {episode_num} to the target channel with link.")

        except Exception as e:
            # Update the status message to indicate an error occurred
            await status_message.edit_text(f"Error occurred: {str(e)}")
            print(f"Error during upload: {str(e)}")
    else:
        # Send a message indicating that details couldn't be extracted from the file name
        await message.reply_text("Could not extract details from the file name.")
        print("Could not extract details from the file name.")

# Run the bot
bot.run()
