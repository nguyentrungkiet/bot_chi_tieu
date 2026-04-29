# Script deploy bot trên Windows VPS
# Chạy script này với quyền Administrator

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "install"
)

$BotPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServiceName = "TelegramExpenseBot"
$ServiceDisplayName = "Telegram Expense Tracking Bot"
$ServiceDescription = "Bot Telegram để ghi chép chi tiêu hàng ngày"
$PythonExe = Join-Path $BotPath "venv\Scripts\python.exe"
$BotScript = Join-Path $BotPath "bot.py"

function Install-Service {
    Write-Host "=== Cài đặt Windows Service ===" -ForegroundColor Green
    
    # Kiểm tra Python và venv
    if (-not (Test-Path $PythonExe)) {
        Write-Host "Error: Không tìm thấy Python trong venv. Vui lòng chạy setup trước." -ForegroundColor Red
        Write-Host "Chạy: python -m venv venv" -ForegroundColor Yellow
        Write-Host "Chạy: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
        Write-Host "Chạy: pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
    
    # Kiểm tra credentials
    $CredentialsPath = Join-Path $BotPath "credentials.json"
    if (-not (Test-Path $CredentialsPath)) {
        Write-Host "Warning: Không tìm thấy credentials.json" -ForegroundColor Yellow
    }
    
    # Kiểm tra config
    $ConfigPath = Join-Path $BotPath "config_local.py"
    if (-not (Test-Path $ConfigPath)) {
        Write-Host "Warning: Không tìm thấy config_local.py" -ForegroundColor Yellow
        Write-Host "Tạo file config_local.py với nội dung:" -ForegroundColor Yellow
        Write-Host @"
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
GOOGLE_SHEETS_CREDENTIALS = 'credentials.json'
SPREADSHEET_NAME = 'Chi tiêu hàng ngày'
WORKSHEET_NAME = 'Chi tiêu'
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'
"@ -ForegroundColor Cyan
    }
    
    # Tạo wrapper script để chạy bot
    $WrapperScript = Join-Path $BotPath "run_bot.ps1"
    @"
Set-Location '$BotPath'
& '$PythonExe' '$BotScript'
"@ | Out-File -FilePath $WrapperScript -Encoding UTF8
    
    # Sử dụng NSSM để tạo service
    $NssmPath = Join-Path $BotPath "nssm.exe"
    
    if (-not (Test-Path $NssmPath)) {
        Write-Host "Downloading NSSM (Non-Sucking Service Manager)..." -ForegroundColor Yellow
        $NssmUrl = "https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip"
        $NssmZip = Join-Path $BotPath "nssm.zip"
        
        try {
            Invoke-WebRequest -Uri $NssmUrl -OutFile $NssmZip
            Expand-Archive -Path $NssmZip -DestinationPath $BotPath -Force
            Copy-Item (Join-Path $BotPath "nssm-2.24-101-g897c7ad\win64\nssm.exe") $NssmPath
            Remove-Item $NssmZip -Force
            Remove-Item (Join-Path $BotPath "nssm-2.24-101-g897c7ad") -Recurse -Force
        } catch {
            Write-Host "Error downloading NSSM. Vui lòng tải thủ công từ https://nssm.cc/download" -ForegroundColor Red
            exit 1
        }
    }
    
    # Xóa service cũ nếu có
    $ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($ExistingService) {
        Write-Host "Removing existing service..." -ForegroundColor Yellow
        & $NssmPath stop $ServiceName
        & $NssmPath remove $ServiceName confirm
        Start-Sleep -Seconds 2
    }
    
    # Cài đặt service mới
    Write-Host "Installing service..." -ForegroundColor Green
    & $NssmPath install $ServiceName $PythonExe $BotScript
    & $NssmPath set $ServiceName AppDirectory $BotPath
    & $NssmPath set $ServiceName DisplayName $ServiceDisplayName
    & $NssmPath set $ServiceName Description $ServiceDescription
    & $NssmPath set $ServiceName Start SERVICE_AUTO_START
    & $NssmPath set $ServiceName AppStdout (Join-Path $BotPath "service_output.log")
    & $NssmPath set $ServiceName AppStderr (Join-Path $BotPath "service_error.log")
    & $NssmPath set $ServiceName AppRotateFiles 1
    & $NssmPath set $ServiceName AppRotateBytes 10485760  # 10MB
    
    Write-Host "`nService installed successfully!" -ForegroundColor Green
    Write-Host "Để start service, chạy: .\deploy_windows.ps1 -Action start" -ForegroundColor Cyan
}

function Start-BotService {
    Write-Host "Starting $ServiceName..." -ForegroundColor Green
    Start-Service -Name $ServiceName
    Start-Sleep -Seconds 2
    Get-Service -Name $ServiceName | Format-Table -AutoSize
    Write-Host "`nĐể xem logs, chạy: .\deploy_windows.ps1 -Action logs" -ForegroundColor Cyan
}

function Stop-BotService {
    Write-Host "Stopping $ServiceName..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force
    Get-Service -Name $ServiceName | Format-Table -AutoSize
}

function Restart-BotService {
    Write-Host "Restarting $ServiceName..." -ForegroundColor Yellow
    Restart-Service -Name $ServiceName -Force
    Start-Sleep -Seconds 2
    Get-Service -Name $ServiceName | Format-Table -AutoSize
}

function Get-BotStatus {
    Write-Host "=== Service Status ===" -ForegroundColor Green
    Get-Service -Name $ServiceName -ErrorAction SilentlyContinue | Format-Table -AutoSize
    
    Write-Host "`n=== Process Info ===" -ForegroundColor Green
    Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$BotPath*" } | Format-Table Id, ProcessName, CPU, WorkingSet, StartTime -AutoSize
}

function Show-Logs {
    $LogFile = Join-Path $BotPath "bot_log.txt"
    $ServiceLog = Join-Path $BotPath "service_output.log"
    
    Write-Host "=== Bot Logs (Last 50 lines) ===" -ForegroundColor Green
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 50
    } else {
        Write-Host "No log file found at $LogFile" -ForegroundColor Yellow
    }
    
    Write-Host "`n=== Service Logs (Last 20 lines) ===" -ForegroundColor Green
    if (Test-Path $ServiceLog) {
        Get-Content $ServiceLog -Tail 20
    } else {
        Write-Host "No service log found" -ForegroundColor Yellow
    }
}

function Remove-BotService {
    Write-Host "Removing $ServiceName..." -ForegroundColor Red
    $NssmPath = Join-Path $BotPath "nssm.exe"
    
    if (Test-Path $NssmPath) {
        & $NssmPath stop $ServiceName
        & $NssmPath remove $ServiceName confirm
        Write-Host "Service removed!" -ForegroundColor Green
    } else {
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        sc.exe delete $ServiceName
    }
}

function Show-Help {
    Write-Host @"
=== Deploy Script cho Telegram Expense Bot trên Windows ===

Cách sử dụng:
    .\deploy_windows.ps1 -Action <action>

Actions:
    install     - Cài đặt bot như Windows Service
    start       - Khởi động service
    stop        - Dừng service
    restart     - Khởi động lại service
    status      - Xem trạng thái service
    logs        - Xem logs
    remove      - Gỡ bỏ service
    help        - Hiển thị hướng dẫn

Ví dụ:
    .\deploy_windows.ps1 -Action install
    .\deploy_windows.ps1 -Action start
    .\deploy_windows.ps1 -Action status
    .\deploy_windows.ps1 -Action logs

Lưu ý:
    - Chạy PowerShell với quyền Administrator
    - Đảm bảo đã cài đặt Python và tạo venv
    - Đảm bảo có file credentials.json và config_local.py

"@ -ForegroundColor Cyan
}

# Main
switch ($Action.ToLower()) {
    "install" { Install-Service }
    "start" { Start-BotService }
    "stop" { Stop-BotService }
    "restart" { Restart-BotService }
    "status" { Get-BotStatus }
    "logs" { Show-Logs }
    "remove" { Remove-BotService }
    "help" { Show-Help }
    default { 
        Write-Host "Action không hợp lệ: $Action" -ForegroundColor Red
        Show-Help
    }
}
