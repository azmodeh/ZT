@echo off
REM Zero Tolerance Python Contract Enforcer - Pre-commit Hook
REM Validates code before allowing commit

echo Zero Tolerance: Running pre-commit validation...

REM Change to the project root directory
cd /d "%~dp0\.."

REM Run the validator to check for contract violations
python enforcement/validator.py

REM Check the exit code
if %errorlevel% neq 0 (
    echo ❌ Zero Tolerance: Commit blocked - contract violations detected!
    echo Please fix the violations before committing.
    exit /b 1
)

echo ✅ Zero Tolerance: All contract rules satisfied - commit allowed
exit /b 0
