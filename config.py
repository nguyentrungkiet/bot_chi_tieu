# config.py - Production configuration
# This file reads from environment variables for deployment
import os

# Telegram Bot Token (REQUIRED)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required!")

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS = 'credentials.json'
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Chi tiêu hàng ngày')
WORKSHEET_NAME = os.getenv('WORKSHEET_NAME', 'Chi tiêu')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
if not SPREADSHEET_ID:
    raise ValueError("SPREADSHEET_ID environment variable is required!")

# Optional: Override with local config for development
try:
    from config.local import *
except ImportError:
    pass  # No local config, use environment variables