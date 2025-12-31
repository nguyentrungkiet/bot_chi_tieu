"""
Web server đơn giản để pass health check của Koyeb
Bot Telegram sẽ chạy trong background thread
"""
from flask import Flask, jsonify
import threading
import logging
import os
import sys

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot Chi Tiêu Telegram đang chạy!', 200

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'telegram-bot'}), 200

@app.route('/status')
def status():
    return jsonify({
        'status': 'running',
        'service': 'telegram-expense-bot',
        'description': 'Bot quản lý chi tiêu hàng ngày'
    }), 200

def run_bot():
    """Chạy Telegram bot trong thread riêng"""
    try:
        logger.info("Đang khởi động Telegram bot trong background thread...")
        # Import và chạy bot
        import bot as telegram_bot
        telegram_bot.main()
    except Exception as e:
        logger.error(f"Lỗi khi chạy bot: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    # Chạy bot trong background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Bot thread đã được khởi động")
    
    # Chạy Flask web server
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Đang khởi động web server trên port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
