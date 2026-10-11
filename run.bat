@echo off
chcp 65001 >nul
echo ===============================================
echo      مترجم نصوص الألعاب - Game Translator
echo ===============================================
echo.
echo جاري التحقق من المتطلبات...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python غير مثبت. يرجى تثبيت Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python مثبت
echo.
echo جاري تثبيت المكتبات المطلوبة...
python -m pip install -q -r requirements.txt
echo ✅ تم تثبيت المكتبات
echo.
echo تنبيه مهم:
echo - يجب أن يكون Tesseract مثبتاً على النظام
echo - حمله من: https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo جاري تشغيل البرنامج...
echo.

python main.py
pause
