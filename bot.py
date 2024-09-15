import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from pymongo import MongoClient
import subprocess

# Load configurations from config.py
from config import API_ID, API_HASH, BOT_TOKEN, DB_URI, DB_NAME, ADMINS, TARGET_CHANNEL, SOURCE_CHANNEL, FLASK_PORT

# Pyrogram Client
bot = Client("auto_anime_upload_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB Client
client = MongoClient(DB_URI)
db = client[DB_NAME]

# Collection to store user requests
request_collection = db['requests']

# Default Thumbnail
default_thumbnail = 'Warrior Tamil.jpg'


@bot.on_message(filters.channel & (filters.video | filters.document) & filters.chat(SOURCE_CHANNEL))
async def handle_file(client, message):
    file = message.video or message.document
    file_name = file.file_name
    
    # Extract anime name, episode number, quality, and language from file_name (adjust regex accordingly)
    anime_name, season, episode, quality = extract_details_from_file_name(file_name)
    
    new_file_name = f"{anime_name} S{season}E{episode} {quality} Tamil"
    download_message = await message.reply_text(f"📥 Downloading {new_file_name}...")
    
    # Download the file
    download_path = await client.download_media(message, file_name=new_file_name)
    await download_message.edit(f"✅ Downloaded {new_file_name}")

    # Generate file link (using inbuilt file storage, adjust as necessary)
    file_link = f"http://your_file_storage.com/{new_file_name}"
    
    # Set Thumbnail
    thumb_path = default_thumbnail
    if db['thumbnails'].find_one({"chat_id": message.chat.id}):
        thumb_path = db['thumbnails'].find_one({"chat_id": message.chat.id})["thumbnail"]
    
    # Upload the file to target channel
    upload_message = await bot.send_message(message.chat.id, f"📤 Uploading {new_file_name}...")
    await client.send_video(
        chat_id=TARGET_CHANNEL,
        video=download_path,
        thumb=thumb_path,
        caption=f"**{anime_name}**\n**Episode**: {episode}\n**Quality**: {quality}\n**Tamil Dub**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Download", url=file_link)]
        ])
    )
    
    await upload_message.edit(f"✅ Uploaded {new_file_name}")

    # Cleanup downloaded files
    os.remove(download_path)


def extract_details_from_file_name(file_name):
    # Example: "AnimeName_S01E05_720p.mkv"
    # You can adjust this regex or string processing based on your file name format
    parts = file_name.split('_')
    anime_name = parts[0]
    season = parts[1][1:3]  # S01
    episode = parts[1][4:]  # E05
    quality = parts[2].split('.')[0]  # 720p
    return anime_name, season, episode, quality


# Command to set custom thumbnail
@bot.on_message(filters.command('set_thumbnail') & filters.user(ADMINS))
async def set_thumbnail(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        thumbnail = await message.reply_to_message.download()
        db['thumbnails'].update_one(
            {"chat_id": message.chat.id},
            {"$set": {"thumbnail": thumbnail}},
            upsert=True
        )
        await message.reply_text("✅ Thumbnail set successfully.")
    else:
        await message.reply_text("❌ Please reply to an image to set it as a thumbnail.")


# Command to start the bot
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Hello! I am the Auto Anime Upload Bot. Send me files from the source channel!")


if __name__ == "__main__":
    bot.run()
