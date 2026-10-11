from setuptools import setup

setup(
    name="Game-Translator",
    version="1.0.0",
    description="Real-time game text translator using OCR and AI",
    author="p0ki1",
    license="MIT",
    py_modules=["main"],
    entry_points={
        "console_scripts": [
            "game-translator=main:main",
        ],
    },
    install_requires=[
        "mss>=9.0.1",
        "Pillow>=10.0.0",
        "pytesseract>=0.3.10",
        "deep-translator>=1.11.4",
    ],
    python_requires=">=3.8",
)
