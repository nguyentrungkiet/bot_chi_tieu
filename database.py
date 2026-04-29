import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import traceback
import logging
import json
import os
from config import SPREADSHEET_ID

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        try:
            # Tạo phạm vi quyền truy cập
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            
            # Kiểm tra xem có Google credentials từ environment variable không
            google_creds_env = os.getenv('GOOGLE_CREDENTIALS')
            
            if google_creds_env:
                # Nếu có credentials từ environment variable (dành cho deployment)
                logger.info("Sử dụng Google credentials từ environment variable")
                creds_dict = json.loads(google_creds_env)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            else:
                # Nếu không có, sử dụng file credentials.json (dành cho local)
                credentials_path = "credentials.json"
                logger.info("Sử dụng Google credentials từ file credentials.json")
                creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
            
            client = gspread.authorize(creds)
            
            # Sử dụng spreadsheet ID từ config
            logger.info(f"Đang kết nối đến Google Sheet với ID: {SPREADSHEET_ID}")
            
            try:
                # Mở spreadsheet bằng ID
                self.spreadsheet = client.open_by_key(SPREADSHEET_ID)
                logger.info(f"Đã kết nối thành công đến spreadsheet: {self.spreadsheet.title}")
                
                # Kiểm tra và sử dụng worksheet
                try:
                    # Ưu tiên sử dụng worksheet "Chi tiêu"
                    self.worksheet = self.spreadsheet.worksheet("Chi tiêu")
                    logger.info("Đã kết nối đến worksheet: Chi tiêu")
                    
                    # Kiểm tra tiêu đề
                    headers = self.worksheet.row_values(1)
                    if not headers:
                        # Nếu worksheet trống, tạo tiêu đề mới
                        logger.info("Worksheet trống, thêm tiêu đề mới")
                        self.worksheet.append_row(["Ngày", "Nội dung", "Số tiền", "Người nhập"])
                        
                except gspread.exceptions.WorksheetNotFound:
                    # Nếu không tìm thấy "Chi tiêu", thử "Sheet1"
                    try:
                        self.worksheet = self.spreadsheet.worksheet("Sheet1")
                        logger.info("Đã kết nối đến worksheet: Sheet1")
                    except gspread.exceptions.WorksheetNotFound:
                        # Sử dụng worksheet đầu tiên
                        self.worksheet = self.spreadsheet.get_worksheet(0)
                        logger.info(f"Sử dụng worksheet đầu tiên: {self.worksheet.title}")
                    
                    # Kiểm tra nếu worksheet trống, thêm tiêu đề
                    values = self.worksheet.get_all_values()
                    if not values:
                        logger.info("Worksheet trống, thêm tiêu đề")
                        self.worksheet.append_row(["Ngày", "Nội dung", "Số tiền", "Người nhập"])
                
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
            # Tìm index cột người dùng - hỗ trợ nhiều tên
            user_idx = None
            for idx, h in enumerate(headers):
                if h.strip() in ["Người dùng", "Người nhập", "User"]:
                    user_idx = idx
                    break
            if user_idx is None:
                user_idx = 3  # Default
            
            # Tìm chi tiêu mới nhất
            for i in range(len(all_values)-1, 0, -1):
                row = all_values[i]
                if len(row) > user_idx and row[user_idx] == user:
                    # Tạo dictionary từ row với mapping chuẩn
                    expense = self._map_row_to_expense(headers, row)
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
    
    def _map_row_to_expense(self, headers, row):
        """Map dữ liệu từ row sang dictionary với tên chuẩn"""
        expense = {}
        
        # Mapping tên cột
        column_mapping = {
            "Thời gian": ["Thời gian", "Ngày", "Ngày ", "Date"],
            "Mô tả": ["Mô tả", "Nội dung", "Description"],
            "Số tiền": ["Số tiền", "Amount"],
            "Người dùng": ["Người dùng", "Người nhập", "User"]
        }
        
        # Tạo reverse mapping
        header_to_standard = {}
        for standard, alternatives in column_mapping.items():
            for alt in alternatives:
                header_to_standard[alt.strip()] = standard
        
        # Map dữ liệu
        for j, header in enumerate(headers):
            if j < len(row):
                standard_name = header_to_standard.get(header.strip(), header)
                expense[standard_name] = row[j]
        
        # Chuyển đổi số tiền thành số
        if "Số tiền" in expense:
            try:
                # Loại bỏ các ký tự không phải số
                amount_str = expense["Số tiền"].replace("đ", "").replace(",", "").replace(".", "").strip()
                expense["Số tiền"] = int(amount_str) if amount_str else 0
            except:
                expense["Số tiền"] = 0
        
        return expense
            
    def get_daily_expenses(self, date):
        """Lấy chi tiêu theo ngày"""
        try:
            # Lấy tất cả dữ liệu
            all_values = self.worksheet.get_all_values()
            if len(all_values) <= 1:  # Chỉ có hàng tiêu đề
                return []
                
            # Lấy tiêu đề
            headers = all_values[0]
            # Tìm index cột ngày/thời gian - hỗ trợ nhiều tên
            datetime_idx = None
            for idx, h in enumerate(headers):
                if h.strip() in ["Thời gian", "Ngày", "Ngày ", "Date"]:
                    datetime_idx = idx
                    break
            if datetime_idx is None:
                datetime_idx = 0  # Default
            
            # Tìm các chi tiêu theo ngày
            expenses = []
            for i in range(1, len(all_values)):
                row = all_values[i]
                if len(row) > datetime_idx:
                    # Kiểm tra nếu ngày trong chuỗi datetime trùng với ngày được yêu cầu
                    if row[datetime_idx].startswith(date):
                        expense = self._map_row_to_expense(headers, row)
                        expenses.append(expense)
                    
            return expenses
        except Exception as e:
            logger.error(f"Lỗi khi lấy chi tiêu theo ngày: {str(e)}")
            return []