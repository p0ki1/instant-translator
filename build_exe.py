import os
import sys
import shutil
from pathlib import Path

try:
    from PyInstaller import __main__ as pyi_main
except ImportError:
    print("تثبيت PyInstaller...")
    os.system(f"{sys.executable} -m pip install pyinstaller")
    from PyInstaller import __main__ as pyi_main

# المسار الحالي
base_path = Path(__file__).parent

# إنشاء مجلد البناء
build_dir = base_path / "dist"
if build_dir.exists():
    shutil.rmtree(build_dir)

print("🔨 بناء البرنامج الموثق...")

# أوامر PyInstaller
pyi_main.run([
    "main.py",
    f"--onefile",
    f"--windowed",
    f"--name=GameTranslator",
    f"--icon=icon.ico" if (base_path / "icon.ico").exists() else "",
    f"--distpath={build_dir}",
    f"--buildpath={base_path / 'build'}",
    f"--specpath={base_path / 'build'}",
    "--hidden-import=PIL",
    "--hidden-import=mss",
    "--hidden-import=pytesseract",
    "--hidden-import=deep_translator",
])

print("✅ تم بناء البرنامج بنجاح!")
print(f"📂 الملف التنفيذي: {build_dir / 'GameTranslator.exe'}")
print(f"\n✨ يمكنك تشغيل البرنامج من {build_dir / 'GameTranslator.exe'}")
