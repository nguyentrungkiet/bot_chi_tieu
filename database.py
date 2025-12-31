import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import traceback
import logging
import json
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        try:
            # Tạo phạm vi quyền truy cập
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            
            # Đường dẫn đến file credentials.json
            credentials_path = "credentials.json"
            
            # Xác thực với Google Sheets
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
            client = gspread.authorize(creds)
            
            # Sử dụng spreadsheet ID cụ thể từ link được cung cấp
            SPREADSHEET_ID = "1nqSKi1q8wXZeP66DYYKmZhSvWnrh1RrrXjB4rx6rT6s"
            logger.info(f"Đang kết nối đến Google Sheet với ID: {SPREADSHEET_ID}")
            
            try:
                # Mở spreadsheet bằng ID
                self.spreadsheet = client.open_by_key(SPREADSHEET_ID)
                logger.info(f"Đã kết nối thành công đến spreadsheet: {self.spreadsheet.title}")
                
                # Kiểm tra và sử dụng worksheet
                try:
                    self.worksheet = self.spreadsheet.worksheet("Sheet1")
                    logger.info("Đã kết nối đến worksheet: Sheet1")
                    
                    # Cập nhật tiêu đề nếu cần
                    headers = self.worksheet.row_values(1)
                    if "Ngày" in headers and "Thời gian" in headers:
                        # Có cả "Ngày" và "Thời gian", cần cập nhật tiêu đề
                        logger.info("Cập nhật tiêu đề để gộp Ngày và Thời gian")
                        new_headers = ["Thời gian", "Mô tả", "Số tiền", "Người dùng"]
                        self.worksheet.clear()
                        self.worksheet.append_row(new_headers)
                    elif not headers:
                        # Nếu worksheet trống, tạo tiêu đề mới
                        logger.info("Worksheet trống, thêm tiêu đề mới")
                        self.worksheet.append_row(["Thời gian", "Mô tả", "Số tiền", "Người dùng"])
                        
                except gspread.exceptions.WorksheetNotFound:
                    # Sử dụng worksheet đầu tiên nếu không tìm thấy Sheet1
                    self.worksheet = self.spreadsheet.get_worksheet(0)
                    logger.info(f"Sử dụng worksheet đầu tiên: {self.worksheet.title}")
                    
                    # Kiểm tra nếu worksheet trống, thêm tiêu đề
                    values = self.worksheet.get_all_values()
                    if not values:
                        logger.info("Worksheet trống, thêm tiêu đề")
                        self.worksheet.append_row(["Thời gian", "Mô tả", "Số tiền", "Người dùng"])
                
            except gspread.exceptions.APIError as e:
                logger.error(f"Lỗi API khi kết nối đến spreadsheet: {e}")
                raise
            
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo Database: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def check_connection(self):
        """Kiểm tra kết nối đến Google Sheets"""
        try:
            # Thử truy cập worksheet
            self.worksheet.row_count
            return True
        except Exception as e:
            logger.error(f"Lỗi kết nối: {str(e)}")
            raise Exception(f"Không thể kết nối đến Google Sheets: {str(e)}")

    def add_expense(self, datetime_str, description, amount, user):
        """Thêm chi tiêu vào Google Sheets, trả về True nếu thành công"""
        try:
            logger.info(f"Thêm chi tiêu: {datetime_str}, {description}, {amount}, {user}")
            
            # Chuyển đổi lại int sang string để tránh lỗi khi gửi đến Google Sheets
            amount_str = str(amount)
            
            # Kiểm tra credentials trước khi thêm dữ liệu
            if hasattr(self, 'worksheet') and self.worksheet:
                # Thêm vào worksheet với định dạng mới (ngày và giờ gộp làm một)
                self.worksheet.append_row([datetime_str, description, amount_str, user])
                logger.info("Đã thêm chi tiêu thành công")
                return True
            else:
                logger.error("Không có kết nối tới worksheet")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi khi thêm chi tiêu: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def get_sheet_info(self):
        """Lấy thông tin về Google Sheet đang sử dụng"""
        try:
            if hasattr(self, 'spreadsheet') and self.spreadsheet:
                return {
                    'title': self.spreadsheet.title,
                    'id': self.spreadsheet.id,
                    'url': f"https://docs.google.com/spreadsheets/d/{self.spreadsheet.id}",
                    'worksheet': self.worksheet.title if hasattr(self, 'worksheet') else None
                }
            return None
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông tin sheet: {str(e)}")
            return None

    def get_latest_expense(self, user):
        """Lấy chi tiêu mới nhất của một người dùng"""
        try:
            # Lấy tất cả dữ liệu
            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:  # Chỉ có hàng tiêu đề
                return None, None
                
            # Lấy tiêu đề
            headers = all_values[0]
            user_idx = headers.index("Người dùng") if "Người dùng" in headers else 3
            
            # Tìm chi tiêu mới nhất
            for i in range(len(all_values)-1, 0, -1):
                row = all_values[i]
                if row[user_idx] == user:
                    # Tạo dictionary từ row với headers
                    expense = {}
                    for j, header in enumerate(headers):
                        if j < len(row):
                            expense[header] = row[j]
                    
                    # Chuyển đổi số tiền thành số
                    if "Số tiền" in expense:
                        try:
                            expense["Số tiền"] = int(expense["Số tiền"])
                        except:
                            pass
                            
                    return expense, i+1  # +1 vì index trong worksheet bắt đầu từ 1
                    
            return None, None
        except Exception as e:
            logger.error(f"Lỗi khi lấy chi tiêu mới nhất: {str(e)}")
            return None, None

    def delete_expense(self, row_index):
        """Xóa chi tiêu theo row_index"""
        try:
            if row_index:
                self.worksheet.delete_rows(row_index)
                logger.info(f"Đã xóa chi tiêu ở hàng {row_index}")
                return True
            return False
        except Exception as e:
            logger.error(f"Lỗi khi xóa chi tiêu: {str(e)}")
            return False
            
    def get_daily_expenses(self, date):
        """Lấy chi tiêu theo ngày"""
        try:
            # Lấy tất cả dữ liệu
            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:  # Chỉ có hàng tiêu đề
                return []
                
            # Lấy tiêu đề
            headers = all_values[0]
            datetime_idx = headers.index("Thời gian") if "Thời gian" in headers else 0
            
            # Tìm các chi tiêu theo ngày
            expenses = []
            for i in range(1, len(all_values)):
                row = all_values[i]
                # Kiểm tra nếu ngày trong chuỗi datetime trùng với ngày được yêu cầu
                if row[datetime_idx].startswith(date):
                    # Tạo dictionary từ row với headers
                    expense = {}
                    for j, header in enumerate(headers):
                        if j < len(row):
                            expense[header] = row[j]
                    
                    # Chuyển đổi số tiền thành số
                    if "Số tiền" in expense:
                        try:
                            expense["Số tiền"] = int(expense["Số tiền"])
                        except:
                            pass
                            
                    expenses.append(expense)
                    
            return expenses
        except Exception as e:
            logger.error(f"Lỗi khi lấy chi tiêu theo ngày: {str(e)}")
            return []