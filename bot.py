import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from config import API_ID, API_HASH, BOT_TOKEN, SOURCE_CHANNEL, TARGET_CHANNEL, FILE_STORE_CHANNEL, FORCE_SUB_CHANNEL

bot = Client("auto_upload_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store to handle saving the thumbnail/poster
thumbnail_poster_store = {}

# Function to generate buttons for different quality options
def generate_quality_buttons(file_id):
    buttons = [
        [InlineKeyboardButton("480p", url=f"https://t.me/{bot.username}?start=download_480p_{file_id}")],
        [InlineKeyboardButton("720p", url=f"https://t.me/{bot.username}?start=download_720p_{file_id}")],
        [InlineKeyboardButton("1080p", url=f"https://t.me/{bot.username}?start=download_1080p_{file_id}")]
    ]
    return InlineKeyboardMarkup(buttons)

# Extract anime name, episode number, and quality from the file name
def parse_anime_info(filename):
    match = re.search(r"(.*?)[._ ](Ep[\d]{1,4})[._ ](\d{3,4}p)", filename, re.IGNORECASE)
    if match:
        anime_name = match.group(1).replace('.', ' ').replace('_', ' ').strip()
        episode_num = match.group(2)
        quality = match.group(3)
        return anime_name, episode_num, quality
    return None, None, None

# Event handler for receiving video or document in source channel
@bot.on_message(filters.channel & (filters.video | filters.document) & filters.chat(SOURCE_CHANNEL))
async def handle_video(client, message):
    media = message.video or message.document
    anime_name, episode_num, quality = parse_anime_info(media.file_name)

    if anime_name and episode_num and quality:
        # Send status message for downloading
        status_message = await message.reply_text("Downloading the video...")

        # Download the file
        download_path = await message.download()

        # Update status message to indicate download completion
        await status_message.edit_text("Download complete. Renaming and uploading...")

        # Rename the file based on the detected information
        new_filename = f"{anime_name} {episode_num} {quality}.mp4"
        new_file_path = f"./downloads/{new_filename}"
        os.rename(download_path, new_file_path)

        # Upload the renamed video to the file store channel
        sent_message = await bot.send_video(FILE_STORE_CHANNEL, video=new_file_path, thumb=THUMBNAIL_PATH, caption=new_filename)
        
        # Access the message ID correctly
        file_id = sent_message.id  # Correctly accessing the message ID here
        
        # Get bot info to retrieve its username
        bot_info = await client.get_me()
        bot_username = bot_info.username

        # Generate bot link for the user to download via the bot
        file_link = f"https://t.me/{bot_username}?start={file_id}"

        # Send the post with the video and buttons to the target channel
        caption = f"{anime_name} - {episode_num}\nQuality: {quality}\n[Download]({file_link})"
        buttons = generate_quality_buttons(file_id)
        await bot.send_photo(TARGET_CHANNEL, photo=POSTER_PATH, caption=caption, reply_markup=buttons)

        # Update status message to indicate upload completion
        await status_message.edit_text("Upload complete.")

        # Clean up downloaded file
        os.remove(new_file_path)

    else:
        await message.reply_text("Could not detect anime name, episode number, or quality from the file name.")
# Event handler for receiving pictures (to be used as thumbnail and poster)
@bot.on_message(filters.channel & filters.photo)
async def handle_thumbnail(client, message):
    thumbnail_poster_path = await message.download(file_name="thumbnail_poster.jpg")
    
    global THUMBNAIL_PATH, POSTER_PATH
    THUMBNAIL_PATH = thumbnail_poster_path
    POSTER_PATH = thumbnail_poster_path

    await message.reply_text("Thumbnail and poster image saved successfully!")

# Event handler when the user clicks the bot-generated link to download the video
@bot.on_message(filters.command("start"))
async def start(client, message):
    # Check if the user clicked the bot link with a file_id parameter
    if len(message.command) > 1:
        file_id = message.command[1]

        # Check if the user is subscribed to the forced subscribe channel
        user = await bot.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)

        if user.status not in ["member", "administrator", "creator"]:
            # User is not subscribed, send force subscribe message
            await message.reply(
                "You must join our channel to download this file.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
                     [InlineKeyboardButton("Try Again", callback_data=f"try_again_{file_id}")]]
                )
            )
        else:
            # User is subscribed, send the file
            await bot.forward_messages(
                chat_id=message.chat.id, 
                from_chat_id=FILE_STORE_CHANNEL, 
                message_ids=int(file_id)
            )

# Callback handler for the "Try Again" button after subscription
@bot.on_callback_query(filters.regex(r"try_again_(\d+)"))
async def try_again_callback(client, callback_query):
    file_id = callback_query.matches[0].group(1)

    # Check if the user is subscribed to the forced subscribe channel
    user = await bot.get_chat_member(FORCE_SUB_CHANNEL, callback_query.from_user.id)

    if user.status not in ["member", "administrator", "creator"]:
        await callback_query.answer("You are still not subscribed. Please join the channel first.", show_alert=True)
    else:
        # User is subscribed, send the file
        await bot.forward_messages(
            chat_id=callback_query.from_user.id, 
            from_chat_id=FILE_STORE_CHANNEL, 
            message_ids=int(file_id)
        )
        await callback_query.answer("Here is your file!")

# Start the bot
bot.run()
print("Bot is running...")
