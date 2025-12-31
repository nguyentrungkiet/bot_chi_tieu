# Bot Chi Tiêu Telegram

Bot Telegram để quản lý chi tiêu hàng ngày với Google Sheets.

## Tính năng

- Ghi nhận chi tiêu hàng ngày
- Tự động lưu vào Google Sheets
- Xem thống kê chi tiêu
- Phân loại chi tiêu theo danh mục

## Yêu cầu

- Python 3.11+
- Tài khoản Telegram Bot (từ BotFather)
- Google Service Account với quyền truy cập Google Sheets

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/nguyentrungkiet/bot_chi_tieu.git
cd bot_chi_tieu
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Tạo file `config.py` từ template:
```python
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
GOOGLE_SHEETS_CREDENTIALS = 'credentials.json'
SPREADSHEET_NAME = 'Chi tiêu hàng ngày'
WORKSHEET_NAME = 'Chi tiêu'
```

4. Thêm file `credentials.json` (Google Service Account credentials)

5. Chạy bot:
```bash
python bot.py
```

## Deploy lên Koyeb

### Bước 1: Chuẩn bị environment variables

Trên Koyeb Dashboard, thêm các environment variables sau:

**Bắt buộc:**
- `TELEGRAM_BOT_TOKEN`: Token bot Telegram của bạn (từ BotFather)
- `GOOGLE_CREDENTIALS`: Nội dung file credentials.json (paste toàn bộ JSON)
- `SPREADSHEET_ID`: ID của Google Sheet (lấy từ URL)

**Tùy chọn:**
- `SPREADSHEET_NAME`: Tên Google Sheet (mặc định: "Chi tiêu hàng ngày")
- `WORKSHEET_NAME`: Tên worksheet (mặc định: "Chi tiêu")
- `PORT`: Port cho web server (Koyeb tự động set)

### Bước 2: Deploy trên Koyeb

1. Truy cập [Koyeb Dashboard](https://app.koyeb.com)
2. Click **Create App** → **Deploy from GitHub**
3. Chọn repository: `nguyentrungkiet/bot_chi_tieu`
4. Chọn branch: `main`
5. **Builder**: Buildpack
6. **Build command**: Để trống (tự động detect)
7. **Run command**: `python web.py` (từ Procfile)
8. **Instance type**: Nano hoặc Micro
9. **Regions**: Chọn 1 region gần bạn
10. Thêm **Environment variables** như ở Bước 1
11. Click **Deploy**

### Bước 3: Lấy Google Credentials JSON

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo Service Account và download file JSON
3. Copy toàn bộ nội dung file JSON
4. Paste vào biến `GOOGLE_CREDENTIALS` trên Koyeb

### Lưu ý quan trọng

- Bot chạy với Flask web server để pass health check của Koyeb
- Web server expose các endpoint: `/`, `/health`, `/status`
- Bot Telegram chạy trong background thread
- Koyeb sẽ tự động restart nếu service down

## Cấu trúc project

```
bot_chi_tieu/
├── bot.py              # Bot chính
├── database.py         # Xử lý Google Sheets
├── config.py          # Cấu hình (không commit)
├── credentials.json   # Google credentials (không commit)
├── requirements.txt   # Dependencies
├── Procfile          # Process definition
├── runtime.txt       # Python version
├── .gitignore        # Git ignore rules
└── README.md         # Documentation
```

## Bảo mật

Đảm bảo không commit các file sau:
- `config.py` (chứa bot token)
- `credentials.json` (Google credentials)
- `bot_log.txt` (logs)

Các file này đã được thêm vào `.gitignore`.
