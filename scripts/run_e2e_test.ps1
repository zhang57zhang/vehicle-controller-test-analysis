# 端到端功能测试脚本

# 配置
$BACKEND_URL = "http://localhost:8000"
$PROJECT_NAME = "E2E测试项目_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# 测试结果
$TEST_RESULTS = @()

# 辅助函数
function Invoke-ApiCall {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body
    )

    $url = "$BACKEND_URL$Endpoint"
    $headers = @{"Content-Type" = "application/json"}

    try {
        if ($Body) {
            $bodyJson = $Body | ConvertTo-Json -Depth 10
            $response = Invoke-WebRequest -Uri $url -Method $Method -Body $bodyJson -Headers $headers -UseBasicParsing -TimeoutSec 30
        } else {
            $response = Invoke-WebRequest -Uri $url -Method $Method -Headers $headers -UseBasicParsing -TimeoutSec 30
        }
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Content = $response.Content | ConvertFrom-Json
        }
    } catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# 测试1：创建项目
Write-Host "`n=== 测试1：创建项目 ===" -ForegroundColor Cyan
$createProjectBody = @{
    name = $PROJECT_NAME
    description = "端到端测试项目"
    test_phase = "MIL"
}
$result = Invoke-ApiCall -Method "POST" -Endpoint "/api/projects/" -Body $createProjectBody
if ($result.Success) {
    Write-Host "✓ 项目创建成功" -ForegroundColor Green
    Write-Host "  项目ID: $($result.Content.id)" -ForegroundColor Gray
    Write-Host "  项目名称: $($result.Content.name)" -ForegroundColor Gray
    $PROJECT_ID = $result.Content.id
    $TEST_RESULTS += "创建项目: PASS"
} else {
    Write-Host "✗ 项目创建失败: $($result.Error)" -ForegroundColor Red
    $TEST_RESULTS += "创建项目: FAIL"
    exit 1
}

# 测试2：上传CSV文件
Write-Host "`n=== 测试2：上传CSV文件 ===" -ForegroundColor Cyan
$csvFilePath = "C:\Users\Administrator\.openclaw\workspace\vehicle-controller-test-analysis\backend\tests\test_data\sample.csv"
if (-not (Test-Path $csvFilePath)) {
    Write-Host "✗ CSV文件不存在: $csvFilePath" -ForegroundColor Red
    $TEST_RESULTS += "上传CSV文件: FAIL"
    exit 1
}

$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$bodyLines = @()
$bodyLines += "--$boundary"
$bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"sample.csv`""
$bodyLines += "Content-Type: text/csv"
$bodyLines += ""
$bodyLines += [System.IO.File]::ReadAllText($csvFilePath)
$bodyLines += "--$boundary--"
$body = $bodyLines -join $LF

try {
    $response = Invoke-WebRequest -Uri "$BACKEND_URL/api/files/upload" -Method POST -Body $body -ContentType "multipart/form-data; boundary=$boundary" -UseBasicParsing
    $fileUploadResult = $response.Content | ConvertFrom-Json
    Write-Host "✓ CSV文件上传成功" -ForegroundColor Green
    Write-Host "  文件ID: $($fileUploadResult.file_id)" -ForegroundColor Gray
    Write-Host "  文件大小: $($fileUploadResult.file_size) bytes" -ForegroundColor Gray
    $CSV_FILE_ID = $fileUploadResult.file_id
    $CSV_FILE_PATH = $fileUploadResult.file_path -replace "\\", "\\"
    $TEST_RESULTS += "上传CSV文件: PASS"
} catch {
    Write-Host "✗ CSV文件上传失败: $_" -ForegroundColor Red
    $TEST_RESULTS += "上传CSV文件: FAIL"
    exit 1
}

# 测试3：上传DBC文件
Write-Host "`n=== 测试3：上传DBC文件 ===" -ForegroundColor Cyan
$dbcFilePath = "C:\Users\Administrator\.openclaw\workspace\vehicle-controller-test-analysis\backend\tests\test_data\sample.dbc"
if (-not (Test-Path $dbcFilePath)) {
    Write-Host "✗ DBC文件不存在: $dbcFilePath" -ForegroundColor Red
    $TEST_RESULTS += "上传DBC文件: FAIL"
    exit 1
}

$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$bodyLines = @()
$bodyLines += "--$boundary"
$bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"sample.dbc`""
$bodyLines += "Content-Type: application/octet-stream"
$bodyLines += ""
$bodyLines += [System.IO.File]::ReadAllText($dbcFilePath)
$bodyLines += "--$boundary--"
$body = $bodyLines -join $LF

try {
    $response = Invoke-WebRequest -Uri "$BACKEND_URL/api/files/upload" -Method POST -Body $body -ContentType "multipart/form-data; boundary=$boundary" -UseBasicParsing
    $dbcUploadResult = $response.Content | ConvertFrom-Json
    Write-Host "✓ DBC文件上传成功" -ForegroundColor Green
    Write-Host "  文件ID: $($dbcUploadResult.file_id)" -ForegroundColor Gray
    $DBC_FILE_NAME = "sample.dbc"
    $TEST_RESULTS += "上传DBC文件: PASS"
} catch {
    Write-Host "✗ DBC文件上传失败: $_" -ForegroundColor Red
    $TEST_RESULTS += "上传DBC文件: FAIL"
    exit 1
}

# 测试4：更新项目关联DBC文件
Write-Host "`n=== 测试4：更新项目关联DBC文件 ===" -ForegroundColor Cyan
$updateProjectBody = @{
    name = $PROJECT_NAME
    description = "端到端测试项目 - 已关联DBC"
    dbc_file = $DBC_FILE_NAME
}
$result = Invoke-ApiCall -Method "PUT" -Endpoint "/api/projects/$PROJECT_ID" -Body $updateProjectBody
if ($result.Success) {
    Write-Host "✓ 项目DBC关联成功" -ForegroundColor Green
    Write-Host "  DBC文件: $($result.Content.dbc_file)" -ForegroundColor Gray
    $TEST_RESULTS += "关联DBC文件: PASS"
} else {
    Write-Host "✗ 项目DBC关联失败: $($result.Error)" -ForegroundColor Red
    $TEST_RESULTS += "关联DBC文件: FAIL"
}

# 测试5：导入CSV数据到项目
Write-Host "`n=== 测试5：导入CSV数据到项目 ===" -ForegroundColor Cyan
$importBody = @{
    project_id = $PROJECT_ID
    file_id = $CSV_FILE_ID
    file_type = "csv"
    file_path = "C:\Users\Administrator\.openclaw\workspace\vehicle-controller-test-analysis\backend\$CSV_FILE_PATH"
    data_type = "MANUAL"
}
$result = Invoke-ApiCall -Method "POST" -Endpoint "/api/data/import" -Body $importBody
if ($result.Success) {
    Write-Host "✓ 数据导入成功" -ForegroundColor Green
    Write-Host "  测试数据ID: $($result.Content.test_data_id)" -ForegroundColor Gray
    Write-Host "  处理记录数: $($result.Content.import_stats.total_records)" -ForegroundColor Gray
    Write-Host "  字段数: $($result.Content.import_stats.fields_count)" -ForegroundColor Gray
    $TEST_DATA_ID = $result.Content.test_data_id
    $TEST_RESULTS += "导入数据: PASS"
} else {
    Write-Host "✗ 数据导入失败: $($result.Error)" -ForegroundColor Red
    $TEST_RESULTS += "导入数据: FAIL"
    exit 1
}

# 测试6：查询项目列表
Write-Host "`n=== 测试6：查询项目列表 ===" -ForegroundColor Cyan
$result = Invoke-ApiCall -Method "GET" -Endpoint "/api/projects/"
if ($result.Success) {
    Write-Host "✓ 项目列表查询成功" -ForegroundColor Green
    Write-Host "  项目数量: $($result.Content.Count)" -ForegroundColor Gray
    $TEST_RESULTS += "查询项目列表: PASS"
} else {
    Write-Host "✗ 项目列表查询失败: $($result.Error)" -ForegroundColor Red
    $TEST_RESULTS += "查询项目列表: FAIL"
}

# 测试7：查询项目详情
Write-Host "`n=== 测试7：查询项目详情 ===" -ForegroundColor Cyan
$result = Invoke-ApiCall -Method "GET" -Endpoint "/api/projects/$PROJECT_ID"
if ($result.Success) {
    Write-Host "✓ 项目详情查询成功" -ForegroundColor Green
    Write-Host "  项目名称: $($result.Content.name)" -ForegroundColor Gray
    Write-Host "  DBC文件: $($result.Content.dbc_file)" -ForegroundColor Gray
    Write-Host "  创建时间: $($result.Content.created_at)" -ForegroundColor Gray
    $TEST_RESULTS += "查询项目详情: PASS"
} else {
    Write-Host "✗ 项目详情查询失败: $($result.Error)" -ForegroundColor Red
    $TEST_RESULTS += "查询项目详情: FAIL"
}

# 测试8：上传并导入第二个CSV文件（模拟多文件导入）
Write-Host "`n=== 测试8：上传并导入第二个CSV文件 ===" -ForegroundColor Cyan
$csvFilePath2 = "C:\Users\Administrator\.openclaw\workspace\vehicle-controller-test-analysis\backend\tests\test_data\sample.csv"
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$bodyLines = @()
$bodyLines += "--$boundary"
$bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"sample2.csv`""
$bodyLines += "Content-Type: text/csv"
$bodyLines += ""
$bodyLines += [System.IO.File]::ReadAllText($csvFilePath2)
$bodyLines += "--$boundary--"
$body = $bodyLines -join $LF

try {
    $response = Invoke-WebRequest -Uri "$BACKEND_URL/api/files/upload" -Method POST -Body $body -ContentType "multipart/form-data; boundary=$boundary" -UseBasicParsing
    $fileUploadResult2 = $response.Content | ConvertFrom-Json
    Write-Host "✓ 第二个CSV文件上传成功" -ForegroundColor Green
    $CSV_FILE_ID_2 = $fileUploadResult2.file_id
    $CSV_FILE_PATH_2 = $fileUploadResult2.file_path -replace "\\", "\\"

    # 导入第二个文件
    $importBody2 = @{
        project_id = $PROJECT_ID
        file_id = $CSV_FILE_ID_2
        file_type = "csv"
        file_path = "C:\Users\Administrator\.openclaw\workspace\vehicle-controller-test-analysis\backend\$CSV_FILE_PATH_2"
        data_type = "MANUAL"
    }
    $result = Invoke-ApiCall -Method "POST" -Endpoint "/api/data/import" -Body $importBody2
    if ($result.Success) {
        Write-Host "✓ 第二个CSV文件导入成功" -ForegroundColor Green
        Write-Host "  测试数据ID: $($result.Content.test_data_id)" -ForegroundColor Gray
        $TEST_RESULTS += "多文件导入: PASS"
    } else {
        Write-Host "✗ 第二个CSV文件导入失败: $($result.Error)" -ForegroundColor Red
        $TEST_RESULTS += "多文件导入: FAIL"
    }
} catch {
    Write-Host "✗ 第二个CSV文件上传失败: $_" -ForegroundColor Red
    $TEST_RESULTS += "多文件导入: FAIL"
}

# 测试9：删除项目
Write-Host "`n=== 测试9：删除项目 ===" -ForegroundColor Cyan
$result = Invoke-ApiCall -Method "DELETE" -Endpoint "/api/projects/$PROJECT_ID"
if ($result.Success) {
    Write-Host "✓ 项目删除成功" -ForegroundColor Green
    $TEST_RESULTS += "删除项目: PASS"
} else {
    Write-Host "✗ 项目删除失败: $($result.Error)" -ForegroundColor Red
    $TEST_RESULTS += "删除项目: FAIL"
}

# 测试10：验证项目已删除
Write-Host "`n=== 测试10：验证项目已删除 ===" -ForegroundColor Cyan
$result = Invoke-ApiCall -Method "GET" -Endpoint "/api/projects/$PROJECT_ID"
if (-not $result.Success) {
    Write-Host "✓ 项目已成功删除（查询失败是预期的）" -ForegroundColor Green
    $TEST_RESULTS += "验证项目删除: PASS"
} else {
    Write-Host "✗ 项目删除验证失败：项目仍然存在" -ForegroundColor Red
    $TEST_RESULTS += "验证项目删除: FAIL"
}

# 测试结果汇总
Write-Host "`n`n=== 测试结果汇总 ===" -ForegroundColor Cyan
$passCount = ($TEST_RESULTS | Where-Object { $_ -like "*: PASS" }).Count
$failCount = ($TEST_RESULTS | Where-Object { $_ -like "*: FAIL" }).Count
$totalCount = $TEST_RESULTS.Count

Write-Host "总测试数: $totalCount" -ForegroundColor White
Write-Host "通过: $passCount" -ForegroundColor Green
Write-Host "失败: $failCount" -ForegroundColor Red
Write-Host "通过率: $([math]::Round($passCount / $totalCount * 100, 2))%" -ForegroundColor Cyan

Write-Host "`n详细结果:" -ForegroundColor Gray
foreach ($result in $TEST_RESULTS) {
    if ($result -like "*: PASS") {
        Write-Host "  $result" -ForegroundColor Green
    } else {
        Write-Host "  $result" -ForegroundColor Red
    }
}

# 保存测试报告
$reportPath = "C:\Users\Administrator\.openclaw\workspace\vehicle-controller-test-analysis\E2E_TEST_REPORT_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
@"
# 端到端功能测试报告

**测试时间：** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**项目名称：** $PROJECT_NAME
**后端URL：** $BACKEND_URL

## 测试结果

- 总测试数：$totalCount
- 通过：$passCount
- 失败：$failCount
- 通过率：$([math]::Round($passCount / $totalCount * 100, 2))%

## 测试详情

$($TEST_RESULTS | ForEach-Object { "  - $_" })

## 测试数据

- 项目ID：$PROJECT_ID
- 测试数据ID1：$TEST_DATA_ID
- CSV文件ID1：$CSV_FILE_ID
- CSV文件ID2：$CSV_FILE_ID_2
- DBC文件名称：$DBC_FILE_NAME

"@ | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "`n测试报告已保存: $reportPath" -ForegroundColor Yellow

# 退出码
if ($failCount -gt 0) {
    exit 1
} else {
    exit 0
}
