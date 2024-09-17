
import os
from dotenv import load_dotenv

# Load environment variables from .env file if using python-dotenv
load_dotenv()

# API details from Telegram
API_ID = int(os.getenv("API_ID", "21740783"))  # Your Telegram API ID
API_HASH = os.getenv("API_HASH", "a5dc7fec8302615f5b441ec5e238cd46")  # Your Telegram API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "7444872585:AAHYzPX_gygFh9xYvu0-k7YOUg7BSG_hzHg")  # Main bot token
ADMINS = int(os.getenv("ADMINS", "6299192020"))
FILE_STORE_BOT_USERNAME = "Thhiiyxvvh_bot"
# Channel details
DB_CHANNEL = int(os.getenv("DB_CHANNEL", "-1002234974607"))  # ID of the channel where files are stored
FILE_STORE_CHANNEL_ID = int(os.getenv("FILE_STORE_CHANNEL_ID", "-1002183423252"))  # ID of the source channel where videos are sent
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1002245327685"))  # ID of the target channel where posts are published
TEMP_DIR = "downloads"  # Directory to store temporarily downloaded files
# Make sure that your environment variables (or hardcoded values) are correct.

DB_URI = "mongodb+srv://Speedwolf1:speedwolf24689@cluster0.rgfywsf.mongodb.net/"
DB_NAME = "Speedwolf1"
