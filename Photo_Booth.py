# -*- coding: utf-8 -*-
"""
Created on Sun Nov 23 16:20:43 2025

@author: tools_and_rides
"""

import os
import time
import subprocess

import win32file
import win32event
import win32con
import win32ui
import win32print

from PIL import Image, ImageWin


# =========================
# Einstellungen
# =========================

# Folder for pictures from camera:
INPUT_DIR = r"C:\Photo_booth\new_images"

# Folder for finished and framed pictures:
OUTPUT_DIR = r"C:\Photo_booth\output_folder"

# Frame File:
FRAME_PATH = r"C:\Photo_booth\frames\example.png"

# Name of both printers:
PRINTER_1 = "canon_selphy_1"
PRINTER_2 = "canon_selphy_2"

# FreeFileSync-Exe und Batch-Datei:
FFS_EXE = r"C:\Program Files\FreeFileSync\FreeFileSync.exe"
FFS_BATCH = r"C:\Photo_booth\check_camera_and_transfer_images.ffs_batch"

# Start free file sinc every SYNC_INTERVAL seconds:
SYNC_INTERVAL = 2  # 

# =========================
# Preparation
# =========================

printer_toggle = 0  # 0 -> PRINTER_1, 1 -> PRINTER_2
last_sync = 0       # Timestamp for last sync

# load frame
frame_base = Image.open(FRAME_PATH).convert("RGBA")

# Resampling-Method for scaling of the frame
try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

path_to_watch = os.path.abspath(INPUT_DIR)

# make sure, folder exists
os.makedirs(path_to_watch, exist_ok=True)

change_handle = win32file.FindFirstChangeNotification(
    path_to_watch,
    0,
    win32con.FILE_NOTIFY_CHANGE_FILE_NAME
)

# =========================
# Helper Functions
# =========================

def run_sync():
    """Start free filer sync with batch file"""
    try:
        subprocess.run([FFS_EXE, FFS_BATCH], check=True)
        print("FreeFileSync-Sync ausgeführt.")
    except Exception as e:
        print(f"FreeFileSync-Sync fehlgeschlagen: {e}")


def create_framed_image(input_path, output_path):
    """Scales frame to picture"""
    # Wait for completion
    for _ in range(10):
        try:
            base_img = Image.open(input_path).convert("RGBA")
            break
        except OSError:
            time.sleep(0.5)
    else:
        print(f"Could not open image: {input_path}")
        return None

    # Frame to image size
    frame_resized = frame_base.resize(base_img.size, RESAMPLE)

    # place frame on picture
    combined = Image.alpha_composite(base_img, frame_resized)

    # Transform to rgb for jpeg
    out_img = combined.convert("RGB")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_img.save(output_path, quality=95)
    print(f"Gerahmtes Bild gespeichert: {output_path}")
    return output_path


def print_image(file_name):
    """Prints alternating on both selphy printers"""
    global printer_toggle

    # alternate Printers
    if printer_toggle == 0:
        win32print.SetDefaultPrinter(PRINTER_1)
        printer_name = win32print.GetDefaultPrinter()
        printer_toggle = 1
    else:
        win32print.SetDefaultPrinter(PRINTER_2)
        printer_name = win32print.GetDefaultPrinter()
        printer_toggle = 0

    # DeviceCaps-Indizes
    HORZRES = 8          # width of printable area (px)
    VERTRES = 10         # heights of printable area  (px)
    PHYSICALWIDTH = 110  # paper width (px)
    PHYSICALHEIGHT = 111 # paper heights (px)
    PHYSICALOFFSETX = 112
    PHYSICALOFFSETY = 113

    bmp = Image.open(file_name).convert("RGB")

    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)

    printable_area = (
        hDC.GetDeviceCaps(HORZRES),
        hDC.GetDeviceCaps(VERTRES),
    )
    printer_size = (
        hDC.GetDeviceCaps(PHYSICALWIDTH),
        hDC.GetDeviceCaps(PHYSICALHEIGHT),
    )
    printer_margins = (
        hDC.GetDeviceCaps(PHYSICALOFFSETX),
        hDC.GetDeviceCaps(PHYSICALOFFSETY),
    )

    ratios = [
        printable_area[0] / bmp.size[0],
        printable_area[1] / bmp.size[1],
    ]
    scale = min(ratios)
    scaled_width, scaled_height = [int(scale * i) for i in bmp.size]

    x1 = int((printer_size[0] - scaled_width) / 2)
    y1 = int((printer_size[1] - scaled_height) / 2)
    x2 = x1 + scaled_width
    y2 = y1 + scaled_height

    hDC.StartDoc(file_name)
    hDC.StartPage()

    dib = ImageWin.Dib(bmp)
    dib.draw(hDC.GetHandleOutput(), (x1, y1, x2, y2))

    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()

    print(f"printed on: {printer_name}")



# =========================
# main loop: Sync + supervise folder
# =========================

try:
    old_path_contents = dict((f, None) for f in os.listdir(path_to_watch))

    while True:
        # open FreeFileSync regularly
        now = time.time()
        if now - last_sync > SYNC_INTERVAL:
            run_sync()
            last_sync = now
        # wait for changes in folder (0,5 s Timeout)
        result = win32event.WaitForSingleObject(change_handle, 500)

        if result == win32con.WAIT_OBJECT_0:
            new_path_contents = dict((f, None) for f in os.listdir(path_to_watch))
            added = [f for f in new_path_contents if f not in old_path_contents]
            deleted = [f for f in old_path_contents if f not in new_path_contents]

            if added:
                print("New File:", ", ".join(added))

            for filename in added:
                # Only Image data
                if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue

                input_path = os.path.join(INPUT_DIR, filename)
                output_path = os.path.join(OUTPUT_DIR, filename)

                framed_path = create_framed_image(input_path, output_path)
                if framed_path is None:
                    continue

                print_image(framed_path)

            if deleted:
                print("Deleted:", ", ".join(deleted))

            old_path_contents = new_path_contents
            win32file.FindNextChangeNotification(change_handle)
            
           

finally:

    win32file.FindCloseChangeNotification(change_handle)
