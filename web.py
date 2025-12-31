"""
Web server đơn giản để pass health check của Koyeb
Bot Telegram sẽ chạy trong background thread
"""
from flask import Flask, jsonify
import threading
import logging
import os
import sys
import time

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Biến global để track bot status
bot_status = {
    'running': False,
    'error': None,
    'started_at': None
}

# Tạo Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot Chi Tiêu Telegram đang chạy!', 200

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'telegram-bot',
        'bot_running': bot_status['running']
    }), 200

@app.route('/status')
def status():
    uptime = None
    if bot_status['started_at']:
        uptime = int(time.time() - bot_status['started_at'])
    
    return jsonify({
        'status': 'running',
        'service': 'telegram-expense-bot',
        'description': 'Bot quản lý chi tiêu hàng ngày',
        'bot_running': bot_status['running'],
        'bot_error': bot_status['error'],
        'uptime_seconds': uptime
    }), 200

def run_bot():
    """Chạy Telegram bot trong thread riêng với asyncio event loop"""
    global bot_status
    
    # Đợi một chút để Flask khởi động xong
    time.sleep(2)
    
    try:
        logger.info("========================================")
        logger.info("Đang khởi động Telegram bot...")
        logger.info("========================================")
        
        bot_status['started_at'] = time.time()
        bot_status['running'] = True
        
        # Tạo event loop mới cho thread này
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Import và chạy bot
        import bot as telegram_bot
        
        # Chạy async main trong event loop
        try:
            loop.run_until_complete(telegram_bot.async_main())
        finally:
            loop.close()
        
    except KeyboardInterrupt:
        logger.info("Bot dừng bởi người dùng")
        bot_status['running'] = False
    except Exception as e:
        logger.error(f"❌ LỖI KHI CHẠY BOT: {e}")
        import traceback
        logger.error(traceback.format_exc())
        bot_status['running'] = False
        bot_status['error'] = str(e)

if __name__ == '__main__':
    logger.info("========================================")
    logger.info("KHỞI ĐỘNG WEB SERVER + TELEGRAM BOT")
    logger.info("========================================")
    
    # Chạy bot trong background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ Bot thread đã được khởi động")
    
    # Chạy Flask web server
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"✅ Đang khởi động web server trên port {port}")
    logger.info("========================================")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
