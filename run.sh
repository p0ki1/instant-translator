#!/bin/bash

echo "==============================================="
echo "      مترجم نصوص الألعاب - Game Translator"
echo "==============================================="
echo ""
echo "جاري التحقق من المتطلبات..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 غير مثبت. يرجى تثبيت Python 3.8+"
    exit 1
fi

echo "✅ Python مثبت"
echo ""
echo "جاري تثبيت المكتبات المطلوبة..."
python3 -m pip install -q -r requirements.txt
echo "✅ تم تثبيت المكتبات"
echo ""
echo "تنبيه مهم:"
echo "- يجب أن يكون Tesseract مثبتاً على النظام"
echo "- على Linux: sudo apt-get install tesseract-ocr"
echo "- على macOS: brew install tesseract"
echo ""
echo "جاري تشغيل البرنامج..."
echo ""

python3 main.py
