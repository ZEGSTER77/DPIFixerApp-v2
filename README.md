# DPI DOCTOR

A small desktop app that sets your images to **300 DPI** in one click. Drop a folder, and every image inside is fixed in seconds.

Built for print-ready workflows (printable papers, wall art, digital products) where a 72 DPI export is not good enough.

## Features

- Drag & drop a folder, or paste its path and click **Process**
- Sets every image to **300 × 300 DPI**
- Supported formats: `PNG`, `JPG`, `JPEG`, `TIF`, `TIFF`
- Progress bar with live counter (`12 / 40 processed`)
- Sound notification when the batch is finished
- Works on **macOS** and **Windows**

## Usage

1. Open DPI DOCTOR.
2. Drag a folder onto the drop zone, or paste a folder path and click **Process**.
3. Wait for the "Done!" message.

> **Note:** images are updated **in place** and only the top level of the chosen folder is processed (no sub-folders). Work on a copy if you want to keep the originals untouched. Only the DPI metadata changes — pixel dimensions stay the same.

## Download

| Platform | How to get it |
|----------|---------------|
| **Windows** | Open the [Actions](../../actions/workflows/build-windows.yml) tab, select the latest successful run of **Build Windows EXE**, and download the `DPI-DOCTOR-Windows` artifact (contains `DPI DOCTOR.exe`). |
| **macOS** | Run from source (see below). |

## Run from source

Requires Python 3.11+ with Tkinter.

```bash
git clone https://github.com/ZEGSTER77/DPIFixerApp-v2.git
cd DPIFixerApp-v2
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install pillow tkinterdnd2
python main.py
```

## How it works

- **macOS:** uses the built-in `sips` command to write the DPI metadata.
- **Windows / Linux:** uses [Pillow](https://python-pillow.org/) to re-save each image with `dpi=(300, 300)`.

---

Made by **ZEGSTER**
