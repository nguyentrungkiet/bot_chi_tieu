import io
import sys
import os

# Sửa lỗi mã hóa Unicode trong console Windows (chỉ khi chạy trực tiếp)
# Không sửa stdout khi chạy trong thread hoặc trên server
if sys.platform == 'win32' and not os.getenv('KOYEB_DEPLOYMENT'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        # Bỏ qua nếu không thể thay đổi stdout (ví dụ khi chạy trong thread)
        pass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import telegram  # Thêm import này để sử dụng telegram.error
from datetime import datetime
import logging
import traceback
from database import Database
from config import TOKEN

# Thiết lập logging
log_handlers = [logging.FileHandler("bot_log.txt", encoding='utf-8')]

# Thêm StreamHandler chỉ khi an toàn
try:
    if sys.platform == 'win32' and not os.getenv('KOYEB_DEPLOYMENT'):
        log_handlers.append(
            logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
        )
    else:
        log_handlers.append(logging.StreamHandler())
except (AttributeError, ValueError):
    # Fallback nếu không thể tạo StreamHandler
    pass

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

class ExpenseBot:
    def __init__(self):
        self.db = Database()
        self.start_time = datetime.now()
        self.bot_info = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_message = """
👋 Chào mừng bạn đến với Bot ghi chép chi tiêu!

Cách sử dụng:
- Gửi tin nhắn theo format: <số tiền> <mô tả>
- Ví dụ: 50k ăn trưa
- Hoặc: 50000 ăn trưa
- Hỗ trợ cả: 1.5k cafe

Trong nhóm chat:
- Thêm @ trước số tiền để bot ghi nhận
- Ví dụ: @50k ăn trưa

Các lệnh:
/start - Hiển thị hướng dẫn
/total - Xem tổng chi tiêu hôm nay
/undo - Xóa ghi chép gần nhất của bạn
        """
        await update.message.reply_text(welcome_message)

    def should_process_message(self, message) -> bool:
        # Log chi tiết để debug
        chat_type = message.chat.type
        text = message.text.strip() if hasattr(message, 'text') and message.text else "Không có text"
        user = message.from_user.username or message.from_user.first_name
        
        logger.info(f"Tin nhắn nhận được - Chat: {chat_type}, User: {user}, Text: {text}")
        
        if chat_type == 'private':
            logger.info("Chat riêng tư - Sẽ xử lý tin nhắn")
            return True
        if chat_type in ['group', 'supergroup'] and text.startswith('@'):
            logger.info("Chat nhóm và tin nhắn bắt đầu bằng @ - Sẽ xử lý tin nhắn")
            return True
        
        logger.info("Không xử lý tin nhắn này")
        return False

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị trạng thái hoạt động của bot"""
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_message = (
            "🟢 Bot đang hoạt động\n"
            f"⏱️ Thời gian hoạt động: {uptime.days} ngày, {hours} giờ, {minutes} phút, {seconds} giây\n"
            f"📅 Khởi động lúc: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        
        try:
            # Kiểm tra kết nối đến database
            self.db.check_connection()
            status_message += "🗄️ Kết nối database: ✅ Đang hoạt động\n"
        except Exception as e:
            status_message += f"🗄️ Kết nối database: ❌ Lỗi ({str(e)})\n"
        
        await update.message.reply_text(status_message)

    async def handle_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            logger.info(f"Nhận tin nhắn: {update.message.text}")
            
            if not self.should_process_message(update.message):
                logger.info("Tin nhắn không được xử lý vì không đáp ứng điều kiện")
                return

            text = update.message.text.strip()
            logger.info(f"Xử lý tin nhắn: {text}")
            
            if text.startswith('@'):
                text = text[1:]
                logger.info(f"Đã loại bỏ @ đầu dòng: {text}")

            parts = text.split(None, 1)  # Tách thành tối đa 2 phần
            if len(parts) < 2:
                logger.warning(f"Tin nhắn không đúng định dạng: {text}")
                raise ValueError("Định dạng không đúng, thiếu mô tả")
                
            amount_str = parts[0].lower()
            description = parts[1]
            
            logger.info(f"Phân tích: Số tiền={amount_str}, Mô tả={description}")
            
            if amount_str.endswith('k'):
                amount = int(float(amount_str[:-1]) * 1000)
            else:
                amount = int(amount_str)
            
            logger.info(f"Số tiền sau khi chuyển đổi: {amount}")
            
            user = update.message.from_user.username or update.message.from_user.first_name
            # Tạo datetime string với định dạng YYYY-MM-DD HH:MM:SS
            datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"Thêm chi tiêu: User={user}, DateTime={datetime_str}, Amount={amount}, Desc={description}")
            success = self.db.add_expense(datetime_str, description, amount, user)
            
            if not success:
                logger.error("Không thể thêm chi tiêu vào database")
                await update.message.reply_text("❌ Không thể lưu chi tiêu. Vui lòng thử lại sau.")
                return
            
            keyboard = [[InlineKeyboardButton("❌ Xóa ghi chép này", callback_data=f"delete")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            formatted_amount = "{:,}".format(amount)
            await update.message.reply_text(
                f"✅ Đã ghi nhận chi tiêu của {user}:\n"
                f"💰 {formatted_amount}đ cho {description}\n"
                f"🕒 Thời gian: {datetime_str}",
                reply_markup=reply_markup
            )
            logger.info("Đã gửi phản hồi thành công")
            
        except ValueError as e:
            logger.warning(f"Lỗi định dạng: {str(e)}")
            if self.should_process_message(update.message):
                await update.message.reply_text(
                    "❌ Format không đúng. Vui lòng gửi theo format:\n"
                    "- Trong chat riêng: <số tiền> <mô tả>\n"
                    "- Trong nhóm: @<số tiền> <mô tả>\n"
                    "- Ví dụ: @50k ăn trưa\n"
                    "- Hoặc: @50000 ăn trưa\n"
                    "- Hoặc: @1.5k cafe")
        except Exception as e:
            logger.error(f"Lỗi không xác định: {str(e)}")
            logger.error(traceback.format_exc())
            if self.should_process_message(update.message):
                await update.message.reply_text("❌ Có lỗi xảy ra, vui lòng thử lại sau")

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý khi người dùng click nút xóa"""
        query = update.callback_query
        
        try:
            # Hiển thị thông báo "đang xử lý" cho người dùng
            await query.answer("Đang xóa...")
            
            user = query.from_user.username or query.from_user.first_name
            latest_expense, row_index = self.db.get_latest_expense(user)
            
            if not latest_expense:
                await query.edit_message_text("❌ Không tìm thấy ghi chép để xóa.")
                return
            
            if self.db.delete_expense(row_index):
                # Lấy thông tin với key an toàn
                amount = latest_expense.get('Số tiền', 0)
                description = latest_expense.get('Mô tả', 'không rõ')
                
                await query.edit_message_text(
                    f"🗑️ Đã xóa ghi chép của {user}:\n"
                    f"💰 {amount:,}đ cho {description}\n"
                    f"✅ Xóa thành công!"
                )
                logger.info(f"Đã xóa chi tiêu của {user}: {amount:,}đ")
            else:
                await query.edit_message_text("❌ Không thể xóa ghi chép. Vui lòng thử lại sau.")
                logger.error(f"Không thể xóa chi tiêu của {user}")
        except Exception as e:
            logger.error(f"Lỗi khi xóa chi tiêu: {str(e)}")
            logger.error(traceback.format_exc())
            await query.answer("❌ Có lỗi xảy ra!", show_alert=True)
            try:
                await query.edit_message_text("❌ Có lỗi xảy ra khi xóa ghi chép.")
            except:
                pass

    async def undo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /undo"""
        try:
            user = update.message.from_user.username or update.message.from_user.first_name
            latest_expense, row_index = self.db.get_latest_expense(user)
            
            if not latest_expense:
                await update.message.reply_text("❌ Không tìm thấy ghi chép nào của bạn để xóa.")
                return
                
            if self.db.delete_expense(row_index):
                # Lấy thông tin với key an toàn
                amount = latest_expense.get('Số tiền', 0)
                description = latest_expense.get('Mô tả', 'không rõ')
                
                await update.message.reply_text(
                    f"🗑️ Đã xóa ghi chép gần nhất của {user}:\n"
                    f"💰 {amount:,}đ cho {description}\n"
                    f"✅ Xóa thành công!"
                )
                logger.info(f"Đã xóa chi tiêu qua lệnh /undo: {user} - {amount:,}đ")
            else:
                await update.message.reply_text("❌ Không thể xóa ghi chép. Vui lòng thử lại sau.")
                logger.error(f"Không thể xóa chi tiêu qua lệnh /undo: {user}")
        except Exception as e:
            logger.error(f"Lỗi khi xử lý lệnh /undo: {str(e)}")
            logger.error(traceback.format_exc())
            await update.message.reply_text("❌ Có lỗi xảy ra khi xóa ghi chép.")

    async def get_total(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị tổng chi tiêu trong ngày"""
        try:
            date = datetime.now().strftime('%Y-%m-%d')
            expenses = self.db.get_daily_expenses(date)
            
            if not expenses:
                await update.message.reply_text("📊 Hôm nay chưa có khoản chi tiêu nào!")
                return
                
            user_expenses = {}
            for expense in expenses:
                user = expense.get('Người dùng', 'Không rõ')
                if user not in user_expenses:
                    user_expenses[user] = []
                user_expenses[user].append(expense)

            total_all = sum(expense.get('Số tiền', 0) for expense in expenses)
            report = f"📊 Chi tiêu hôm nay ({date}):\n\n"
            
            for user, user_exps in user_expenses.items():
                user_total = sum(exp.get('Số tiền', 0) for exp in user_exps)
                report += f"👤 {user} - Tổng: {user_total:,}đ\n"
                for exp in user_exps:
                    description = exp.get('Mô tả', 'Không rõ')
                    amount = exp.get('Số tiền', 0)
                    time = exp.get('Thời gian', 'Không rõ')
                    report += f"  - {description}: {amount:,}đ ({time})\n"
                report += "\n"
            
            report += f"💰 Tổng cộng tất cả: {total_all:,}đ"
            
            await update.message.reply_text(report)
            
        except Exception as e:
            logger.error(f"Lỗi khi tính tổng chi tiêu: {str(e)}")
            logger.error(traceback.format_exc())
            await update.message.reply_text("❌ Có lỗi xảy ra khi tính tổng chi tiêu")

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị thông tin về bot và Google Sheet"""
        if not self.bot_info:
            self.bot_info = await context.bot.get_me()
            
        info_message = (
            "📊 Thông tin Bot Chi Tiêu\n\n"
            f"🤖 Tên bot: {self.bot_info.first_name}\n"
            f"👤 Username: @{self.bot_info.username}\n"
            f"🆔 Bot ID: {self.bot_info.id}\n\n"
        )
        
        # Thêm thông tin về Google Sheet
        sheet_info = self.db.get_sheet_info()
        if sheet_info:
            info_message += (
                "📝 Google Sheet:\n"
                f"📄 Tên: {sheet_info['title']}\n"
                f"🔗 Link: {sheet_info['url']}\n"
            )
        else:
            info_message += "❌ Không thể lấy thông tin Google Sheet\n"
            
        await update.message.reply_text(info_message)

def main():
    logger.info("Đang khởi động bot...")
    
    # Thêm xử lý ngoại lệ khi khởi động
    try:
        bot = ExpenseBot()
        application = Application.builder().token(TOKEN).build()
        
        # Lấy thông tin sheet
        sheet_info = bot.db.get_sheet_info()
        if sheet_info:
            logger.info("===== THÔNG TIN GOOGLE SHEET =====")
            logger.info(f"📄 Tên: {sheet_info['title']}")
            logger.info(f"🔗 Link: {sheet_info['url']}")
            logger.info("===================================")
        
        # Thêm handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("total", bot.get_total))
        application.add_handler(CommandHandler("undo", bot.undo_command))
        application.add_handler(CommandHandler("status", bot.status))
        application.add_handler(CommandHandler("info", bot.info))
        application.add_handler(CallbackQueryHandler(bot.button_click))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, bot.handle_expense))
        
        # Thêm error handler để xử lý lỗi
        application.add_error_handler(error_handler)
        
        # Log khi bot khởi động thành công
        logger.info("Bot đã khởi động thành công!")
        logger.info("Bot đã sẵn sàng! Gửi lệnh /status trong Telegram để kiểm tra trạng thái.")
        
        # Chạy bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except telegram.error.Conflict:
        logger.error("LỖI: Đã có một phiên bản bot đang chạy với TOKEN này!")
        logger.error("Vui lòng kiểm tra và đóng tất cả các cửa sổ terminal đang chạy bot trước khi chạy lại.")
        logger.error("Conflict: Đã có phiên bản bot đang chạy")
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("LỖI: Không tìm thấy Google Spreadsheet!")
        logger.error("Hãy tạo Google Spreadsheet mới và cập nhật file database.py")
        logger.error("Hoặc chạy check_sheets.py để kiểm tra kết nối")
        logger.error("Không tìm thấy spreadsheet")
    except Exception as e:
        logger.error(f"LỖI: {e}")
        logger.error(f"Không thể khởi động bot: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lỗi khi bot đang chạy"""
    logger.error(f"Lỗi khi xử lý cập nhật: {context.error}")
    logger.error(traceback.format_exc())
    
    if isinstance(context.error, telegram.error.Conflict):
        logger.error("Bot bị xung đột: Đã có phiên bản khác đang chạy")
    
    # Thêm xử lý cho các lỗi phổ biến khác
    elif isinstance(context.error, telegram.error.NetworkError):
        logger.error("Lỗi mạng khi giao tiếp với Telegram API")
    elif isinstance(context.error, telegram.error.TelegramError):
        logger.error(f"Lỗi Telegram API: {str(context.error)}")

if __name__ == '__main__':
    main()