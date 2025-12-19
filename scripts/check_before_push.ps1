# Git 推送前数据安全检查脚本 (Windows PowerShell版本)
# 使用方法: .\check_before_push.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Git 推送前数据安全检查" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$checkPassed = $true

# 1. 检查暂存区是否有CSV文件
Write-Host "1. 检查 CSV/Excel 文件..." -ForegroundColor Yellow
$csvFiles = git diff --cached --name-only | Select-String -Pattern '\.(csv|xlsx|xls)$'
if ($csvFiles.Count -eq 0) {
    Write-Host "✓ 没有CSV/Excel文件将被推送" -ForegroundColor Green
} else {
    Write-Host "✗ 发现CSV/Excel文件:" -ForegroundColor Red
    $csvFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    $checkPassed = $false
}
Write-Host ""

# 2. 检查数据目录
Write-Host "2. 检查数据目录..." -ForegroundColor Yellow
$dataFiles = git diff --cached --name-only | Select-String -Pattern '^(data|原始词)/'
if ($dataFiles.Count -eq 0) {
    Write-Host "✓ 没有数据目录文件将被推送" -ForegroundColor Green
} else {
    Write-Host "✗ 发现数据目录文件:" -ForegroundColor Red
    $dataFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    $checkPassed = $false
}
Write-Host ""

# 3. 检查 .env 文件
Write-Host "3. 检查环境变量文件..." -ForegroundColor Yellow
$envFiles = git diff --cached --name-only | Select-String -Pattern '^\.env$'
if ($envFiles.Count -eq 0) {
    Write-Host "✓ .env 文件不会被推送" -ForegroundColor Green
} else {
    Write-Host "✗ 发现 .env 文件将被推送！" -ForegroundColor Red
    $checkPassed = $false
}
Write-Host ""

# 4. 检查数据库文件
Write-Host "4. 检查数据库文件..." -ForegroundColor Yellow
$dbFiles = git diff --cached --name-only | Select-String -Pattern '\.(db|sqlite|sqlite3)$'
if ($dbFiles.Count -eq 0) {
    Write-Host "✓ 没有数据库文件将被推送" -ForegroundColor Green
} else {
    Write-Host "✗ 发现数据库文件:" -ForegroundColor Red
    $dbFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    $checkPassed = $false
}
Write-Host ""

# 5. 显示将要推送的文件
Write-Host "5. 将要推送的文件列表:" -ForegroundColor Yellow
Write-Host "----------------------------------------"
git diff --cached --name-only
Write-Host "----------------------------------------"
Write-Host ""

# 最终结果
Write-Host "==========================================" -ForegroundColor Cyan
if ($checkPassed) {
    Write-Host "✓ 安全检查通过！可以安全推送。" -ForegroundColor Green
    Write-Host ""
    Write-Host "执行以下命令推送:"
    Write-Host "  git push" -ForegroundColor White
} else {
    Write-Host "✗ 安全检查失败！发现敏感数据。" -ForegroundColor Red
    Write-Host ""
    Write-Host "请执行以下命令移除敏感文件:"
    Write-Host "  git reset HEAD <文件路径>" -ForegroundColor White
    Write-Host ""
    Write-Host "或者重置所有暂存区:"
    Write-Host "  git reset HEAD" -ForegroundColor White
}
Write-Host "==========================================" -ForegroundColor Cyan
