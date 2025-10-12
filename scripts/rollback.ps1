# Zero Tolerance - Rollback from .bak files
# بازگشت سریع با استفاده از فایل‌های backup

param(
    [string]$Path = ".",
    [switch]$WhatIf,
    [switch]$Verbose
)

Write-Host "🔄 Zero Tolerance Rollback Tool" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$count = 0
$errors = 0

Get-ChildItem -Path $Path -Recurse -Filter "*.bak" -ErrorAction SilentlyContinue | ForEach-Object {
    $bakFile = $_.FullName
    $origFile = $bakFile -replace '\.bak$', ''
    
    if ($Verbose) {
        Write-Host "Found: $bakFile" -ForegroundColor Gray
    }
    
    if (Test-Path $origFile) {
        if ($WhatIf) {
            Write-Host "[DRY-RUN] Would restore: $origFile" -ForegroundColor Yellow
            $count++
        } else {
            try {
                Copy-Item $bakFile $origFile -Force
                Write-Host "✅ Restored: $origFile" -ForegroundColor Green
                $count++
            } catch {
                Write-Host "❌ Failed: $origFile - $($_.Exception.Message)" -ForegroundColor Red
                $errors++
            }
        }
    } else {
        Write-Host "⚠️  Original not found: $origFile" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan

if ($WhatIf) {
    Write-Host "🔍 Dry-run complete: Would restore $count files" -ForegroundColor Yellow
} else {
    Write-Host "✅ Rollback complete: $count files restored" -ForegroundColor Green
    if ($errors -gt 0) {
        Write-Host "⚠️  Errors: $errors files failed" -ForegroundColor Red
    }
}

Write-Host ""
