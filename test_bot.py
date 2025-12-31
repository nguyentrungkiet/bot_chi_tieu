"""
Script test bot telegram để kiểm tra kết nối
"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError

# Token của bot
TOKEN = '7682518935:AAFNBfeNcdhUup7JrOR9iBwV1i1p2idM8Pc'

async def test_bot():
    print("=== KIỂM TRA BOT TELEGRAM ===\n")
    
    bot = Bot(token=TOKEN)
    
    try:
        # Test 1: Lấy thông tin bot
        print("1. Kiểm tra thông tin bot...")
        me = await bot.get_me()
        print(f"✅ Bot đang hoạt động:")
        print(f"   - Tên: {me.first_name}")
        print(f"   - Username: @{me.username}")
        print(f"   - ID: {me.id}")
        print()
        
        # Test 2: Kiểm tra webhook
        print("2. Kiểm tra webhook...")
        webhook_info = await bot.get_webhook_info()
        print(f"   - Webhook URL: {webhook_info.url if webhook_info.url else 'NONE (Polling mode)'}")
        print(f"   - Pending updates: {webhook_info.pending_update_count}")
        
        if webhook_info.url:
            print("   ⚠️ CẢNH BÁO: Bot đang dùng webhook mode!")
            print("   ℹ️ Cần xóa webhook để dùng polling mode")
            
            # Xóa webhook
            print("\n3. Đang xóa webhook...")
            result = await bot.delete_webhook(drop_pending_updates=True)
            if result:
                print("   ✅ Đã xóa webhook thành công!")
                print("   ℹ️ Bot giờ sẽ hoạt động ở polling mode")
            else:
                print("   ❌ Không thể xóa webhook")
        else:
            print("   ✅ Bot đang ở polling mode (OK)")
        
        print("\n4. Kiểm tra updates...")
        updates = await bot.get_updates(limit=5)
        print(f"   - Số updates chờ xử lý: {len(updates)}")
        if updates:
            print(f"   - Update gần nhất: Update ID {updates[-1].update_id}")
        
        print("\n=== KẾT QUẢ: Bot đang hoạt động bình thường ===")
        print("Nếu bot vẫn không phản hồi, hãy:")
        print("1. Restart app trên Koyeb")
        print("2. Gửi /start trong Telegram")
        print("3. Kiểm tra logs trên Koyeb Dashboard")
        
    except TelegramError as e:
        print(f"❌ LỖI TELEGRAM: {e}")
        if "Conflict" in str(e):
            print("\n⚠️ Có instance khác đang chạy với token này!")
            print("Giải pháp:")
            print("1. Dừng tất cả bot local (Ctrl+C trong terminal)")
            print("2. Hoặc restart app trên Koyeb")
    except Exception as e:
        print(f"❌ LỖI: {e}")

if __name__ == '__main__':
    asyncio.run(test_bot())
