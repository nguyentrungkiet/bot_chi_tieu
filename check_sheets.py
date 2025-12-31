import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sys
import json

def check_connection():
    try:
        print("Đang kiểm tra kết nối đến Google Sheets...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials_path = "credentials.json"
        
        print(f"Đang đọc file credentials từ: {credentials_path}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        
        print("Đang xác thực với Google API...")
        client = gspread.authorize(creds)
        
        # Liệt kê tất cả spreadsheets mà service account có quyền truy cập
        print("\nDanh sách spreadsheets có thể truy cập:")
        spreadsheets = client.openall()
        if not spreadsheets:
            print("❌ Không tìm thấy spreadsheet nào! Service account không có quyền truy cập vào bất kỳ spreadsheet nào.")
            print("\nHướng dẫn: Chia sẻ spreadsheet với email trong file credentials.json")
            try:
                with open(credentials_path, 'r') as f:
                    cred_data = json.load(f)
                    client_email = cred_data.get('client_email', 'Unknown')
                    print(f"Email của service account: {client_email}")
                    print("Hãy chia sẻ quyền Editor cho email này trong Google Sheets của bạn")
            except Exception as e:
                print(f"Không thể đọc email từ credentials: {e}")
            return False
        
        for i, sheet in enumerate(spreadsheets, 1):
            print(f"{i}. {sheet.title} (ID: {sheet.id})")
        
        print("\nThử kết nối bằng ID thay vì tên...")
        # Dùng spreadsheet đầu tiên để kiểm tra
        if spreadsheets:
            test_sheet = spreadsheets[0]
            print(f"Đang thử kết nối đến: {test_sheet.title}")
            
            # Truy cập worksheets
            worksheets = test_sheet.worksheets()
            print(f"Các worksheet có sẵn: {[ws.title for ws in worksheets]}")
            
            if worksheets:
                worksheet = worksheets[0]
                print(f"Đang sử dụng worksheet: {worksheet.title}")
                
                # Thử đọc dữ liệu
                print("Đang đọc dữ liệu...")
                rows = worksheet.get_all_values()
                print(f"✅ Kết nối thành công! Đã đọc được {len(rows)} dòng dữ liệu.")
                
                # Thử ghi dữ liệu kiểm tra
                print("Đang thử ghi dữ liệu test...")
                worksheet.append_row(["TEST", "TEST", "TEST", "0", "TEST"])
                print("✅ Ghi dữ liệu thành công!")
                
                # Xóa dữ liệu test
                rows = worksheet.get_all_values()
                if rows[-1][0] == "TEST":
                    worksheet.delete_rows(len(rows))
                    print("✅ Đã xóa dữ liệu test!")
                
                print("\n✅ THÔNG TIN KẾT NỐI THÀNH CÔNG:")
                print(f"- Spreadsheet ID: {test_sheet.id}")
                print(f"- Spreadsheet title: {test_sheet.title}")
                print(f"- Worksheet title: {worksheet.title}")
                print("\nHãy cập nhật file database.py với thông tin này!")
                return True
        
        return False
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Lỗi: Không tìm thấy spreadsheet 'Chi tiêu'")
        print("Vui lòng kiểm tra tên spreadsheet hoặc chia sẻ quyền cho service account.")
        return False
    except gspread.exceptions.APIError as e:
        print(f"❌ Lỗi API: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_connection()
    if not success:
        sys.exit(1)
