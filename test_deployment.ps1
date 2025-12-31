# Script kiểm tra bot deployment

# Sau khi deploy thành công, lấy URL từ Koyeb (ví dụ: https://bot-chi-tieu-xxx.koyeb.app)
# Thay YOUR_APP_URL bằng URL thực tế

$APP_URL = "YOUR_APP_URL"  # Ví dụ: https://bot-chi-tieu-xxx.koyeb.app

Write-Host "=== KIỂM TRA DEPLOYMENT ===" -ForegroundColor Green

# Test 1: Homepage
Write-Host "`n1. Kiểm tra homepage..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$APP_URL/" -UseBasicParsing
    Write-Host "✅ Homepage OK: $($response.Content)" -ForegroundColor Green
} catch {
    Write-Host "❌ Lỗi homepage: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Health check
Write-Host "`n2. Kiểm tra health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$APP_URL/health" -Method Get
    Write-Host "✅ Health check OK:" -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "❌ Lỗi health check: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Status
Write-Host "`n3. Kiểm tra status endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$APP_URL/status" -Method Get
    Write-Host "✅ Status OK:" -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "❌ Lỗi status: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== HOÀN TẤT ===" -ForegroundColor Green
Write-Host "`nNếu tất cả đều ✅, bot đã deploy thành công!" -ForegroundColor Cyan
Write-Host "Bước tiếp theo: Mở Telegram và test bot" -ForegroundColor Cyan
