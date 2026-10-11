import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import mss
from PIL import Image
import pytesseract
from deep_translator import GoogleTranslator


APP_TITLE = "مترجم نصوص الألعاب"


class ScreenTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("500x330")
        self.root.resizable(False, False)

        self.region = None
        self.running = False
        self.busy = False
        self.last_text = ""
        self.last_translation = ""
        self.messages = queue.Queue()
        self.lang_by_name = self.load_languages()

        default_language = "arabic" if "arabic" in self.lang_by_name else next(iter(self.lang_by_name))
        self.target_name = tk.StringVar(value=default_language)
        self.ocr_lang = tk.StringVar(value="eng")
        self.status = tk.StringVar(value="اختر مساحة النص في اللعبة أولاً.")

        self.build_ui()
        self.build_overlay()
        self.root.after(200, self.check_messages)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    @staticmethod
    def load_languages():
        # قاموس ثابت ومتوافق مع deep_translator
        return {
            "arabic": "ar",
            "english": "en",
            "french": "fr",
            "spanish": "es",
            "german": "de",
            "italian": "it",
            "japanese": "ja",
            "korean": "ko",
            "chinese (simplified)": "zh-CN",
            "russian": "ru",
            "turkish": "tr",
            "portuguese": "pt",
            "hindi": "hi",
            "dutch": "nl",
            "polish": "pl",
            "swedish": "sv",
            "norwegian": "no",
            "danish": "da",
            "finnish": "fi",
            "greek": "el",
            "ukrainian": "uk",
            "romanian": "ro",
            "czech": "cs",
            "hungarian": "hu",
            "thai": "th",
            "vietnamese": "vi",
            "indonesian": "id",
            "malay": "ms",
            "hebrew": "he",
        }

    def build_ui(self):
        pad = {"padx": 12, "pady": 6}
        ttk.Label(self.root, text="مترجم نصوص الألعاب", font=("Arial", 17, "bold")).pack(pady=(12, 4))
        ttk.Label(
            self.root,
            text="يقرأ النص من مساحة تختارها ويعرض الترجمة في نافذة عائمة.",
            wraplength=455,
            justify="center",
        ).pack(**pad)

        row = ttk.Frame(self.root)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="لغة الترجمة:").pack(side="right", padx=6)
        self.language_combo = ttk.Combobox(
            row,
            textvariable=self.target_name,
            values=sorted(self.lang_by_name.keys()),
            state="readonly",
            width=26,
        )
        self.language_combo.pack(side="right")
        self.language_combo.bind("<<ComboboxSelected>>", self.target_changed)

        row2 = ttk.Frame(self.root)
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="لغة OCR:").pack(side="right", padx=6)
        ttk.Entry(row2, textvariable=self.ocr_lang, width=18, justify="left").pack(side="right")
        ttk.Label(row2, text="مثال: eng أو jpn أو eng+jpn").pack(side="right", padx=8)

        buttons = ttk.Frame(self.root)
        buttons.pack(pady=10)
        ttk.Button(buttons, text="1) تحديد مساحة النص", command=self.select_region).pack(side="right", padx=5)
        self.start_button = ttk.Button(buttons, text="2) ابدأ الترجمة", command=self.toggle_running)
        self.start_button.pack(side="right", padx=5)

        ttk.Label(self.root, textvariable=self.status, wraplength=460, foreground="#245b83", justify="center").pack(**pad)
        ttk.Label(
            self.root,
            text="ملاحظة: يحتاج Tesseract للـ OCR واتصال إنترنت للترجمة. أفضل توافق للألعاب يكون بوضع Windowed/Borderless.",
            wraplength=455,
            justify="center",
            foreground="#555",
        ).pack(pady=(3, 10), padx=12)

    def build_overlay(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.withdraw()
        self.overlay.title("الترجمة")
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.92)
        self.overlay.configure(bg="#111827")
        self.overlay.geometry("760x150+80+80")

        self.output = tk.Label(
            self.overlay,
            text="ستظهر الترجمة هنا",
            bg="#111827",
            fg="white",
            font=("Arial", 16, "bold"),
            justify="center",
            wraplength=720,
            padx=18,
            pady=18,
        )
        self.output.pack(fill="both", expand=True)
        self.output.bind("<Button-1>", self.start_drag)
        self.output.bind("<B1-Motion>", self.drag_overlay)
        self.drag_offset = (0, 0)

    def start_drag(self, event):
        self.drag_offset = (event.x_root - self.overlay.winfo_x(), event.y_root - self.overlay.winfo_y())

    def drag_overlay(self, event):
        x = event.x_root - self.drag_offset[0]
        y = event.y_root - self.drag_offset[1]
        self.overlay.geometry(f"+{x}+{y}")

    def select_region(self):
        self.root.withdraw()
        selector = tk.Toplevel(self.root)
        selector.attributes("-fullscreen", True)
        selector.attributes("-topmost", True)
        selector.attributes("-alpha", 0.30)
        selector.configure(bg="black", cursor="crosshair")
        canvas = tk.Canvas(selector, bg="black", highlightthickness=0, cursor="crosshair")
        canvas.pack(fill="both", expand=True)
        canvas.create_text(
            30, 25, anchor="nw", fill="white", font=("Arial", 18, "bold"),
            text="اسحب بالماوس لتحديد مكان النص داخل اللعبة — اضغط Esc للإلغاء",
        )
        selection = {"x": 0, "y": 0, "rect": None}

        def down(event):
            selection["x"], selection["y"] = event.x_root, event.y_root
            selection["rect"] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#00ff88", width=3)

        def move(event):
            if selection["rect"] is not None:
                canvas.coords(selection["rect"], selection["x"], selection["y"], event.x_root, event.y_root)

        def up(event):
            x1, y1 = selection["x"], selection["y"]
            x2, y2 = event.x_root, event.y_root
            left, top = min(x1, x2), min(y1, y2)
            width, height = abs(x2 - x1), abs(y2 - y1)
            selector.destroy()
            self.root.deiconify()
            if width >= 20 and height >= 12:
                self.region = {"left": left, "top": top, "width": width, "height": height}
                self.status.set(f"تم تحديد مساحة النص: {width} × {height} بكسل. اضغط ابدأ.")
            else:
                self.status.set("لم يتم اختيار مساحة كافية؛ حاول مرة أخرى.")

        def cancel(_event=None):
            selector.destroy()
            self.root.deiconify()
            self.status.set("تم إلغاء تحديد المساحة.")

        canvas.bind("<ButtonPress-1>", down)
        canvas.bind("<B1-Motion>", move)
        canvas.bind("<ButtonRelease-1>", up)
        selector.bind("<Escape>", cancel)
        selector.focus_force()

    def toggle_running(self):
        if not self.running:
            if not self.region:
                messagebox.showinfo(APP_TITLE, "حدد مساحة النص أولاً.")
                return
            self.running = True
            self.start_button.configure(text="إيقاف الترجمة")
            self.status.set("الترجمة تعمل. يمكنك تصغير هذه النافذة؛ نافذة الترجمة العائمة تبقى ظاهرة.")
            self.overlay.deiconify()
            self.schedule_capture(100)
        else:
            self.running = False
            self.start_button.configure(text="2) ابدأ الترجمة")
            self.status.set("تم إيقاف الترجمة.")

    def schedule_capture(self, delay=1400):
        if self.running and self.root.winfo_exists():
            self.root.after(delay, self.capture_screen)

    def capture_screen(self):
        if not self.running or not self.root.winfo_exists():
            return
        if self.busy:
            self.schedule_capture(700)
            return
        self.overlay.withdraw()
        self.root.after(120, self.grab_after_hide)

    def grab_after_hide(self):
        if not self.running or not self.root.winfo_exists():
            return
        try:
            with mss.mss() as sct:
                shot = sct.grab(self.region)
                image = Image.frombytes("RGB", shot.size, shot.rgb)
            self.overlay.deiconify()
            self.busy = True
            ocr_language = self.ocr_lang.get().strip() or "eng"
            target_code = self.lang_by_name.get(self.target_name.get(), "ar")
            threading.Thread(target=self.process_image, args=(image, ocr_language, target_code), daemon=True).start()
        except Exception as exc:
            self.overlay.deiconify()
            self.messages.put(("error", f"تعذر التقاط الشاشة: {exc}"))
        self.schedule_capture(1400)

    def process_image(self, image, ocr_language, target_code):
        try:
            text = pytesseract.image_to_string(image, lang=ocr_language, config="--psm 6")
            text = " ".join(text.split())
            if len(text) < 2:
                self.messages.put(("empty", ""))
                return
            if text == self.last_text and self.last_translation:
                self.messages.put(("same", self.last_translation))
                return
            self.last_text = text
            translated = self.translate(text, target_code)
            self.last_translation = translated
            self.messages.put(("translated", translated))
        except Exception as exc:
            self.messages.put(("error", str(exc)))
        finally:
            self.busy = False

    def translate(self, text, target_code):
        try:
            return GoogleTranslator(source="auto", target=target_code).translate(text)
        except Exception as e:
            return f"[فشل الترجمة] {text}"

    def target_changed(self, _event=None):
        if self.last_text:
            self.busy = True
            target_code = self.lang_by_name.get(self.target_name.get(), "ar")
            threading.Thread(target=self.retranslate_last, args=(target_code,), daemon=True).start()

    def retranslate_last(self, target_code):
        try:
            translated = self.translate(self.last_text, target_code)
            self.last_translation = translated
            self.messages.put(("translated", translated))
        except Exception as exc:
            self.messages.put(("error", str(exc)))
        finally:
            self.busy = False

    def check_messages(self):
        if not self.root.winfo_exists():
            return
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == "translated":
                    self.output.configure(text=value)
                    self.status.set("تم تحديث الترجمة.")
                elif kind == "empty":
                    self.output.configure(text="لم أتعرف على نص واضح. جرّب تكبير مساحة النص أو تغيير لغة OCR.")
                elif kind == "same":
                    self.output.configure(text=value)
                elif kind == "error":
                    self.status.set("خطأ: " + value[:180])
                    self.output.configure(text="تعذر إتمام الترجمة. تحقق من إعداد OCR والإنترنت.")
        except queue.Empty:
            pass
        self.root.after(200, self.check_messages)

    def close(self):
        self.running = False
        if self.root.winfo_exists():
            self.root.destroy()


def main():
    root = tk.Tk()
    ScreenTranslator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
