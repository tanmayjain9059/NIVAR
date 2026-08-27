import cv2
import tkinter as tk
from tkinter import filedialog
import pytesseract


# ============================================================
# 1. CREATE FILE SELECTION WINDOW
# ============================================================

root = tk.Tk()
root.withdraw()


# ============================================================
# 2. ASK USER TO SELECT AN IMAGE
# ============================================================

file_path = filedialog.askopenfilename(
    title="Select a Food Package Image",
    filetypes=[
        ("Image files", "*.jpg *.jpeg *.png *.webp"),
        ("JPG files", "*.jpg *.jpeg"),
        ("PNG files", "*.png"),
        ("All files", "*.*")
    ]
)


# ============================================================
# 3. CHECK WHETHER AN IMAGE WAS SELECTED
# ============================================================

if not file_path:
    print("No image selected.")
    exit()


# ============================================================
# 4. LOAD IMAGE USING OPENCV
# ============================================================

image = cv2.imread(file_path)

print("Selected file:", file_path)


# Check if OpenCV successfully loaded the image
if image is None:
    print("Could not load the image.")
    exit()


# ============================================================
# 5. GET IMAGE INFORMATION
# ============================================================

height, width, channels = image.shape

print("\nImage loaded successfully!")
print("Width:", width)
print("Height:", height)
print("Channels:", channels)


# ============================================================
# 6. CONVERT IMAGE TO GRAYSCALE
# ============================================================

gray_image = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2GRAY
)

print("\nGrayscale image created!")
print("Grayscale dimensions:", gray_image.shape)


# ============================================================
# 7. DISPLAY ORIGINAL IMAGE
# ============================================================

cv2.imshow(
    "Original Image",
    image
)


# ============================================================
# 8. DISPLAY GRAYSCALE IMAGE
# ============================================================

cv2.imshow(
    "Grayscale Image",
    gray_image
)


# ============================================================
# 9. LET USER SELECT A REGION OF INTEREST (ROI)
# ============================================================

print("\nSelect the region you want to analyze.")
print("Click and drag around the text.")
print("Press ENTER after selecting the region.")

x, y, w, h = cv2.selectROI(
    "Select Region",
    image
)


# ============================================================
# 10. CHECK WHETHER A REGION WAS SELECTED
# ============================================================

if w == 0 or h == 0:
    print("No region selected.")
    cv2.destroyAllWindows()
    exit()


# ============================================================
# 11. CROP THE SELECTED REGION
# ============================================================

roi = image[
    y:y + h,
    x:x + w
]


# ============================================================
# 12. DISPLAY SELECTED REGION
# ============================================================

cv2.imshow(
    "Selected Region",
    roi
)


# ============================================================
# 13. SEND ONLY THE SELECTED REGION TO TESSERACT
# ============================================================

print("\nReading text from selected region...")

text = pytesseract.image_to_string(
    roi
)


# ============================================================
# 14. DISPLAY EXTRACTED TEXT
# ============================================================

print("\n====================================")
print("        EXTRACTED TEXT")
print("====================================")

print(text)

print("====================================")


# ============================================================
# 15. WAIT FOR USER TO PRESS A KEY
# ============================================================

cv2.waitKey(0)


# ============================================================
# 16. CLOSE ALL OPENCV WINDOWS
# ============================================================

cv2.destroyAllWindows()