# config.py - Production configuration
# This file reads from environment variables for deployment
import os

# Try to import local config first (for development)
try:
    # Import as config_local since we can't do from config.local
    import config_local
    TOKEN = config_local.TOKEN
    GOOGLE_SHEETS_CREDENTIALS = config_local.GOOGLE_SHEETS_CREDENTIALS
    SPREADSHEET_NAME = config_local.SPREADSHEET_NAME
    WORKSHEET_NAME = config_local.WORKSHEET_NAME
    SPREADSHEET_ID = config_local.SPREADSHEET_ID
    print("✅ Loaded configuration from config_local.py")
except ImportError:
    # No local config, use environment variables (for production)
    print("⚙️ Using environment variables for configuration")
    
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