#!/usr/bin/env python3
"""BloomArtPixel DPI Fixer — sets images to 300 DPI (PNG/JPG/JPEG/TIF/TIFF)"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# ---- Claude-inspired theme ----
BG        = "#F5F1EC"   # warm cream background
CARD_BG   = "#FAF9F5"
ACCENT    = "#CC785C"   # terracotta / rust
ACCENT_HV = "#B8674E"
ACCENT_DISABLED = "#D9D3C7"
TEXT_DARK = "#2B2823"
TEXT_GRAY = "#8A8577"
BORDER    = "#D9D3C7"

EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
DONE_SOUND = "/System/Library/Sounds/Glass.aiff"  # macOS only


class RoundButton(tk.Canvas):
    """A Canvas-drawn button so the fill color actually applies on macOS
    (native tk.Button ignores bg colors under Aqua)."""

    def __init__(self, parent, text, command, width=110, height=38, radius=10,
                 bg=BG, fill=ACCENT, fill_hover=ACCENT_HV,
                 fg="white", font=("Helvetica Neue", 12, "bold")):
        super().__init__(parent, width=width, height=height, bg=bg,
                          highlightthickness=0, cursor="pointinghand" if not IS_WINDOWS else "hand2")
        self.command = command
        self.width = width
        self.height = height
        self.radius = radius
        self.fill = fill
        self.fill_hover = fill_hover
        self.fg = fg
        self.font = font
        self.text = text
        self.enabled = True

        self._draw(self.fill)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self._draw(self.fill_hover) if self.enabled else None)
        self.bind("<Leave>", lambda e: self._draw(self.fill) if self.enabled else None)

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(2, 2, self.width - 2, self.height - 2, self.radius,
                          fill=color, outline=color)
        self.create_text(self.width / 2, self.height / 2, text=self.text,
                          fill=self.fg, font=self.font)

    def _on_click(self, event):
        if self.enabled and self.command:
            self.command()

    def set_state(self, state):
        if state == "disabled":
            self.enabled = False
            self.config(cursor="arrow")
            self._draw(ACCENT_DISABLED)
        else:
            self.enabled = True
            self.config(cursor="pointinghand" if not IS_WINDOWS else "hand2")
            self._draw(self.fill)


class DPIFixerApp:
    def __init__(self, root):
        self.root = root
        root.title("DPI DOCTOR")
        root.geometry("440x420")
        root.configure(bg=BG)
        root.resizable(False, False)

        tk.Label(root, text="DPI DOCTOR", font=("Helvetica Neue", 18, "bold"),
                 bg=BG, fg=TEXT_DARK).pack(pady=(24, 0))
        tk.Label(root, text="by ZEGSTER · sets images to 300 DPI", font=("Helvetica Neue", 11),
                 bg=BG, fg=TEXT_GRAY).pack(pady=(2, 18))

        # Drop zone (dashed border, drawn on a canvas)
        self.canvas = tk.Canvas(root, width=380, height=140, bg=CARD_BG, highlightthickness=0)
        self.canvas.pack(pady=(0, 6))
        self._draw_dropzone("Drag a folder here")
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.on_drop)

        tk.Label(root, text="— or —", font=("Helvetica Neue", 10),
                 bg=BG, fg=TEXT_GRAY).pack(pady=(4, 4))

        # Paste path row
        row = tk.Frame(root, bg=BG)
        row.pack(pady=(0, 14))
        self.path_var = tk.StringVar()
        entry = tk.Entry(row, textvariable=self.path_var, width=27,
                          font=("Helvetica Neue", 11), relief="flat",
                          highlightthickness=1, highlightbackground=BORDER,
                          highlightcolor=ACCENT, bg=CARD_BG, fg=TEXT_DARK)
        entry.pack(side="left", ipady=6, padx=(0, 8))

        self.process_btn = RoundButton(row, "Process", self.on_process_click)
        self.process_btn.pack(side="left")

        # Progress bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Accent.Horizontal.TProgressbar",
                         troughcolor=BORDER, background=ACCENT, thickness=8)
        self.progress = ttk.Progressbar(root, style="Accent.Horizontal.TProgressbar",
                                         length=380, mode="determinate")
        self.progress.pack(pady=(6, 8))

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_var, font=("Helvetica Neue", 10),
                 bg=BG, fg=TEXT_GRAY).pack()

    def _draw_dropzone(self, text):
        self.canvas.delete("all")
        self.canvas.create_rectangle(4, 4, 376, 136, outline=BORDER, width=2, dash=(6, 4))
        self.canvas.create_text(190, 70, text=text, font=("Helvetica Neue", 12), fill=TEXT_GRAY)

    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        if not paths:
            return
        folder = paths[0]
        if os.path.isdir(folder):
            self.path_var.set(folder)
            self.start_processing(folder)
        else:
            self.status_var.set("Please drop a folder, not a file.")

    def on_process_click(self):
        folder = self.path_var.get().strip().strip('"')
        if not folder or not os.path.isdir(folder):
            self.status_var.set("That folder path doesn't exist.")
            return
        self.start_processing(folder)

    def start_processing(self, folder):
        self.process_btn.set_state("disabled")
        self._draw_dropzone("Processing…")
        threading.Thread(target=self._process_folder, args=(folder,), daemon=True).start()

    def _process_folder(self, folder):
        files = [f for f in os.listdir(folder) if f.lower().endswith(EXTENSIONS)]
        total = len(files)

        if total == 0:
            self.root.after(0, self._finish, 0)
            return

        self.root.after(0, lambda: self.progress.config(maximum=total, value=0))

        done = 0
        for f in files:
            full_path = os.path.join(folder, f)
            self._set_dpi(full_path)
            done += 1
            self.root.after(0, self._update_progress, done, total)

        self.root.after(0, self._finish, done)

    def _set_dpi(self, full_path):
        """Set an image's DPI to 300x300. Uses macOS 'sips' on macOS,
        and Pillow (cross-platform) everywhere else, including Windows."""
        if IS_MAC:
            subprocess.run(
                ["sips", "-s", "dpiHeight", "300", "-s", "dpiWidth", "300", full_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        else:
            try:
                img = Image.open(full_path)
                img.save(full_path, dpi=(300, 300))
            except Exception:
                pass

    def _update_progress(self, done, total):
        self.progress.config(value=done)
        self.status_var.set(f"{done} / {total} processed")

    def _finish(self, count):
        self.process_btn.set_state("normal")
        self._draw_dropzone("Drag a folder here")
        self.status_var.set(f"Done! {count} file(s) set to 300 DPI." if count
                             else "No matching images found in that folder.")
        if count:
            self._play_done_sound()

    def _play_done_sound(self):
        try:
            if IS_MAC:
                subprocess.Popen(["afplay", DONE_SOUND])
            elif IS_WINDOWS:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    DPIFixerApp(root)
    root.mainloop()
