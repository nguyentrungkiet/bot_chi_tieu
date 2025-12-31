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

- `TELEGRAM_BOT_TOKEN`: Token bot Telegram của bạn
- `SPREADSHEET_NAME`: Tên Google Sheet
- `WORKSHEET_NAME`: Tên worksheet
- `GOOGLE_CREDENTIALS`: Nội dung file credentials.json (paste toàn bộ JSON)

### Bước 2: Sửa code để đọc từ environment variables

File `config.py` sẽ tự động đọc từ environment variables khi deploy.

### Bước 3: Deploy

1. Kết nối GitHub repository với Koyeb
2. Chọn branch `main`
3. Koyeb sẽ tự động detect Python app qua `requirements.txt`
4. Set build command: `pip install -r requirements.txt`
5. Set run command: `python bot.py`

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
