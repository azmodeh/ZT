# Zero Tolerance API - Smoke Test Suite (PowerShell)
# تست سریع تمام endpoints

param(
    [string]$ApiUrl = "http://127.0.0.1:8088",
    [int]$Timeout = 10
)

Write-Host "🧪 Zero Tolerance API - Smoke Test Suite" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "API URL: $ApiUrl"
Write-Host ""

$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [string]$Data = $null,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host -NoNewline "Testing $Name... "
    
    try {
        $uri = "$ApiUrl$Endpoint"
        
        if ($Data) {
            $response = Invoke-WebRequest -Uri $uri -Method $Method `
                -ContentType "application/json" `
                -Body $Data `
                -TimeoutSec $Timeout `
                -ErrorAction Stop
        } else {
            $response = Invoke-WebRequest -Uri $uri -Method $Method `
                -TimeoutSec $Timeout `
                -ErrorAction Stop
        }
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✅ PASS" -ForegroundColor Green -NoNewline
            Write-Host " (HTTP $($response.StatusCode))"
            $script:passed++
            return $true
        } else {
            Write-Host "❌ FAIL" -ForegroundColor Red -NoNewline
            Write-Host " (HTTP $($response.StatusCode), expected $ExpectedStatus)"
            $script:failed++
            return $false
        }
    } catch {
        Write-Host "❌ FAIL" -ForegroundColor Red -NoNewline
        Write-Host " ($($_.Exception.Message))"
        $script:failed++
        return $false
    }
}

# Run tests
Write-Host "1️⃣  Health Checks" -ForegroundColor Cyan
Test-Endpoint "/health" "GET" "/health"
Test-Endpoint "/ready" "GET" "/ready"
Test-Endpoint "/live" "GET" "/live"
Write-Host ""

Write-Host "2️⃣  Validation" -ForegroundColor Cyan
Test-Endpoint "/validate (empty)" "POST" "/validate" "{}"
Write-Host ""

Write-Host "3️⃣  Queue (Dry-Run)" -ForegroundColor Cyan
$env:ZT_DRY_RUN = "1"
Test-Endpoint "/queue (safe)" "POST" "/queue" '{"mode":"safe"}'
Write-Host ""

Write-Host "4️⃣  Learning" -ForegroundColor Cyan
Test-Endpoint "/learn" "POST" "/learn" "{}"
Write-Host ""

# Summary
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Passed: $passed" -ForegroundColor Green

if ($failed -gt 0) {
    Write-Host "❌ Failed: $failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Some tests failed. Please check the API server." -ForegroundColor Red
    exit 1
} else {
    Write-Host "🎉 All smoke tests passed!" -ForegroundColor Green
    exit 0
}
