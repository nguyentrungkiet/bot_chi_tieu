# Hướng dẫn Deploy Bot trên Windows VPS

## Bước 1: Chuẩn bị VPS

### 1.1. Cài đặt Git
Download và cài đặt Git: https://git-scm.com/download/win

### 1.2. Cài đặt Python 3.11+
Download và cài đặt Python: https://www.python.org/downloads/

**Lưu ý:** Tick vào "Add Python to PATH" khi cài đặt

### 1.3. Kiểm tra cài đặt
```powershell
python --version
git --version
```

## Bước 2: Clone Repository

```powershell
# Di chuyển đến thư mục muốn lưu code
cd C:\

# Clone repository
git clone https://github.com/nguyentrungkiet/bot_chi_tieu.git
cd bot_chi_tieu
```

## Bước 3: Cài đặt Dependencies

```powershell
# Tạo virtual environment
python -m venv venv

# Cho phép chạy script PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Kích hoạt venv
.\venv\Scripts\Activate.ps1

# Cài đặt các thư viện
pip install -r requirements.txt
```

## Bước 4: Cấu hình Bot

### 4.1. Upload file credentials.json
- Copy file `credentials.json` từ máy local vào thư mục `bot_chi_tieu`
- Dùng Remote Desktop để copy paste

### 4.2. Tạo file config_local.py
```powershell
notepad config_local.py
```

Thêm nội dung (thay token và ID của bạn):
```python
TOKEN = '7682518935:AAFNBfeNcdhUup7JrOR9iBwV1i1p2idM8Pc'
GOOGLE_SHEETS_CREDENTIALS = 'credentials.json'
SPREADSHEET_NAME = 'Chi tiêu hàng ngày'
WORKSHEET_NAME = 'Chi tiêu'
SPREADSHEET_ID = '1nqSKi1q8wXZeP66DYYKmZhSvWnrh1RrrXjB4rx6rT6s'
```

## Bước 5: Test Bot

```powershell
# Chạy thử bot
python bot.py

# Nhấn Ctrl+C để dừng
```

## Bước 6: Cài đặt Bot như Windows Service

### Cách 1: Sử dụng script tự động (Khuyến nghị)

```powershell
# Chạy PowerShell với quyền Administrator
# Right-click PowerShell -> Run as Administrator

# Di chuyển đến thư mục bot
cd C:\bot_chi_tieu

# Cài đặt service
.\deploy_windows.ps1 -Action install

# Khởi động service
.\deploy_windows.ps1 -Action start

# Kiểm tra trạng thái
.\deploy_windows.ps1 -Action status

# Xem logs
.\deploy_windows.ps1 -Action logs
```

### Các lệnh khác:

```powershell
# Dừng bot
.\deploy_windows.ps1 -Action stop

# Khởi động lại bot
.\deploy_windows.ps1 -Action restart

# Gỡ bỏ service
.\deploy_windows.ps1 -Action remove

# Xem hướng dẫn
.\deploy_windows.ps1 -Action help
```

### Cách 2: Chạy bot dưới nền với PowerShell

```powershell
# Chạy bot ẩn (không hiển thị cửa sổ)
Start-Process -FilePath "C:\bot_chi_tieu\venv\Scripts\python.exe" `
              -ArgumentList "C:\bot_chi_tieu\bot.py" `
              -WindowStyle Hidden `
              -WorkingDirectory "C:\bot_chi_tieu"

# Tìm process đang chạy
Get-Process python

# Dừng bot
Stop-Process -Name python -Force
```

### Cách 3: Sử dụng Task Scheduler

1. Mở Task Scheduler (taskschd.msc)
2. Create Task -> General:
   - Name: Telegram Expense Bot
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges
3. Triggers:
   - New -> At startup
4. Actions:
   - Program: `C:\bot_chi_tieu\venv\Scripts\python.exe`
   - Arguments: `bot.py`
   - Start in: `C:\bot_chi_tieu`
5. Settings:
   - ✅ Allow task to be run on demand
   - ✅ If task fails, restart every: 1 minute
   - Attempt to restart up to: 3 times

## Bước 7: Kiểm tra và Monitoring

### Xem logs
```powershell
# Xem bot logs
Get-Content bot_log.txt -Tail 50 -Wait

# Xem service logs
Get-Content service_output.log -Tail 30 -Wait
```

### Kiểm tra service
```powershell
# Xem status
Get-Service TelegramExpenseBot

# Xem process
Get-Process python | Where-Object {$_.Path -like "*bot_chi_tieu*"}
```

### Mở port cho webhook (nếu cần)
```powershell
# Mở port trong Windows Firewall
New-NetFirewallRule -DisplayName "Telegram Bot" `
                    -Direction Inbound `
                    -Protocol TCP `
                    -LocalPort 8443 `
                    -Action Allow
```

## Troubleshooting

### Bot không khởi động
1. Kiểm tra Python đã cài đúng: `python --version`
2. Kiểm tra credentials.json có đúng vị trí
3. Kiểm tra config_local.py có đúng thông tin
4. Xem logs để biết lỗi cụ thể

### Service không start
1. Chạy PowerShell với quyền Administrator
2. Kiểm tra đường dẫn Python trong service
3. Xem Event Viewer -> Windows Logs -> Application

### Bot bị disconnect
1. Kiểm tra internet connection
2. Kiểm tra Google API credentials còn hạn
3. Kiểm tra Telegram token còn hoạt động
4. Xem logs để tìm lỗi

## Cập nhật Code

```powershell
# Dừng bot
.\deploy_windows.ps1 -Action stop

# Pull code mới
git pull origin main

# Cài đặt dependencies mới (nếu có)
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Khởi động lại
.\deploy_windows.ps1 -Action start
```

## Backup và Restore

### Backup
```powershell
# Backup các file quan trọng
Copy-Item credentials.json, config_local.py, bot_log.txt C:\backup\
```

### Restore
```powershell
# Restore từ backup
Copy-Item C:\backup\* C:\bot_chi_tieu\
```

## Bảo mật

⚠️ **Quan trọng:**
- Không share file `credentials.json`
- Không commit `config_local.py` lên git
- Sử dụng tài khoản có quyền hạn chế để chạy service
- Thường xuyên backup credentials
- Đổi token nếu bị lộ

## Liên hệ & Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs: `.\deploy_windows.ps1 -Action logs`
2. Xem GitHub Issues: https://github.com/nguyentrungkiet/bot_chi_tieu/issues
3. Tạo issue mới với đầy đủ thông tin lỗi
