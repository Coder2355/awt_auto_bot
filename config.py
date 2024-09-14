
import os
from dotenv import load_dotenv

# Load environment variables from .env file if using python-dotenv
load_dotenv()

# API details from Telegram
API_ID = int(os.getenv("API_ID", "21740783"))  # Your Telegram API ID
API_HASH = os.getenv("API_HASH", "a5dc7fec8302615f5b441ec5e238cd46")  # Your Telegram API Hash
BOT_TOKEN = os.getenv("BOT_TOKEN", "7444872585:AAHYzPX_gygFh9xYvu0-k7YOUg7BSG_hzHg")  # Main bot token
FILE_STORE_BOT_TOKEN = os.getenv("FILE_STORE_BOT_TOKEN", "7116266807:AAFiuS4MxcubBiHRyzKEDnmYPCRiS0f3aGU")  # File store bot token

# Channel details
DB_CHANNEL = int(os.getenv("DATABASE_CHANNEL_ID", "-1002234974607"))  # ID of the channel where files are stored
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL", "-1002183423252"))  # ID of the source channel where videos are sent
TARGET_CHANNEL = int(os.getenv("TARGET_CHANNEL", "-1002245327685"))  # ID of the target channel where posts are published
TEMP_DIR = "downloads"  # Directory to store temporarily downloaded files
# Make sure that your environment variables (or hardcoded values) are correct.
