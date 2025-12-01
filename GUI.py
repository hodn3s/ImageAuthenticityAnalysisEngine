from importlib.resources import path
from tkinter import *
from tkinter import filedialog, ttk, messagebox
from PIL import ImageTk, Image, ExifTags, ImageChops
from optparse import OptionParser
from datetime import datetime
from prettytable import PrettyTable
import numpy as np
import random
import sys
import cv2
import re
import os
from ForgeryDetection import Detect
import double_jpeg_compression
import noise_variance
import copy_move_cfa

# ----------------- GLOBAL VARIABLES -----------------
IMG_WIDTH = 400
IMG_HEIGHT = 400
uploaded_image = None

# ----------------- COLOR THEME -----------------
BG_COLOR = "#1E1E1E"
FG_COLOR = "#CA690E"
BTN_BG = "#2E2E2E"
BTN_HOVER = "#E25F07"
PROGRESS_BG = "#FF4C4C"

# ----------------- IMAGE HELPERS -----------------
def resize_image(img, width, height):
    try:
        resample_method = Image.Resampling.BICUBIC
    except AttributeError:
        resample_method = Image.BICUBIC
    return img.resize((width, height), resample_method)

def getImage(path, width, height):
    img = Image.open(path)
    img = resize_image(img, width, height)
    return ImageTk.PhotoImage(img)

# ----------------- FILE BROWSING -----------------
def browseFile():
    global uploaded_image
    filename = filedialog.askopenfilename(title="Select an image",
                                          filetypes=[("Image files", ".jpeg .jpg .png")])
    if filename == "":
        return

    uploaded_image = filename
    progressBar['value'] = 0
    fileLabel.configure(text=filename)

    img = getImage(filename, IMG_WIDTH, IMG_HEIGHT)
    inputPanel.configure(image=img)
    inputPanel.image = img

    blank_img = getImage("images/output.png", IMG_WIDTH, IMG_HEIGHT)
    resultPanel.configure(image=blank_img)
    resultPanel.image = blank_img

    middle_img = getImage("images/middle.png", IMG_WIDTH, IMG_HEIGHT)
    middlePanel.configure(image=middle_img)
    middlePanel.image = middle_img

    resultLabel.configure(text="Select Function", foreground="orange")

# ----------------- IMAGE ANALYSIS FUNCTIONS -----------------
def copy_move_forgery():
    path = uploaded_image
    eps = 60
    min_samples = 2
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    detect = Detect(path)
    key_points, descriptors = detect.siftDetector()
    forgery = detect.locateForgery(eps, min_samples)
    progressBar['value'] = 100
    if forgery is None:
        img = getImage("images/no_copy_move.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="ORIGINAL IMAGE", foreground="green")
    else:
        img = getImage("images/copy_move.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Image Forged", foreground="red")
        cv2.imshow('Forgery', forgery)
        while cv2.getWindowProperty('Forgery', 0) >= 0:
            keyCode = cv2.waitKey(1000)
            if keyCode in [ord('q'), ord('Q')]:
                cv2.destroyAllWindows()
                break
            elif keyCode in [ord('s'), ord('S')]:
                name = re.findall(r'(.+?)(\.[^.]*$|$)', path)
                date = datetime.today().strftime('%Y_%m_%d_%H_%M_%S')
                new_file_name = f"{name[0][0]}_{eps}_{min_samples}_{date}{name[0][1]}"
                cv2.imwrite(new_file_name, forgery)
                print('Image Saved as....', new_file_name)

def metadata_analysis():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    img = Image.open(path)
    img_exif = img.getexif()
    progressBar['value'] = 100
    if not img_exif:
        img = getImage("images/no_metadata.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="NO Data Found", foreground="red")
    else:
        img = getImage("images/metadata.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Metadata Details", foreground="green")
        with open('Metadata_analysis.txt', 'w') as f:
            for key, val in img_exif.items():
                if key in ExifTags.TAGS:
                    f.write(f'{ExifTags.TAGS[key]} : {val}\n')
        os.startfile('Metadata_analysis.txt')

def noise_variance_inconsistency():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    noise_forgery = noise_variance.detect(path)
    progressBar['value'] = 100
    if noise_forgery:
        img = getImage("images/varience.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Noise variance", foreground="red")
    else:
        img = getImage("images/no_varience.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="No Noise variance", foreground="green")

def cfa_artifact():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    identical_regions_cfa = copy_move_cfa.detect(path, OptionParser().parse_args()[0], [])
    progressBar['value'] = 100
    if identical_regions_cfa:
        img = getImage("images/cfa.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text=f"{str(identical_regions_cfa)}, CFA artifacts detected", foreground="red")
    else:
        img = getImage("images/no_cfa.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="NO-CFA artifacts detected", foreground="green")

def ela_analysis():
    path = uploaded_image
    TEMP = 'temp.jpg'
    SCALE = 10
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    original = Image.open(path)
    original.save(TEMP, quality=90)
    temporary = Image.open(TEMP)
    diff = ImageChops.difference(original, temporary)
    d = diff.load()
    WIDTH, HEIGHT = diff.size
    for x in range(WIDTH):
        for y in range(HEIGHT):
            d[x, y] = tuple(k * SCALE for k in d[x, y])
    progressBar['value'] = 100
    diff.show()

def jpeg_Compression():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    double_compressed = double_jpeg_compression.detect(path)
    progressBar['value'] = 100
    if double_compressed:
        img = getImage("images/double_compression.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Double compression", foreground="red")
    else:
        img = getImage("images/single_compression.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Single compression", foreground="green")

def image_decode():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    img = cv2.imread(path)
    width, height = img.shape[0], img.shape[1]
    img1 = np.zeros((width, height, 3), np.uint8)
    img2 = np.zeros((width, height, 3), np.uint8)
    for i in range(width):
        for j in range(height):
            for l in range(3):
                v1 = format(img[i][j][l], '08b')
                v2 = v1[:4] + chr(random.randint(0, 1)+48) * 4
                v3 = v1[4:] + chr(random.randint(0, 1)+48) * 4
                img1[i][j][l]= int(v2, 2)
                img2[i][j][l]= int(v3, 2)
    progressBar['value'] = 100
    cv2.imwrite('output.png', img2)
    Image.open('output.png').show()

def string_analysis():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    x = PrettyTable()
    x.field_names = ["Bytes", "8-bit", "string"]
    with open(path, "rb") as f:
        n = 0
        b = f.read(16)
        while b:
            s1 = " ".join([f"{i:02x}" for i in b])
            s1 = s1[0:23] + " " + s1[23:]
            s2 = "".join([chr(i) if 32 <= i <= 127 else "." for i in b])
            x.add_row([f"{n * 16:08x}", f"{s1:<48}", f"{s2}"])
            n += 1
            b = f.read(16)
        progressBar['value'] = 100
        with open('hex_viewer.txt', 'w') as w:
            w.write(str(x))
        os.startfile('hex_viewer.txt')

# ----------------- GUI SETUP -----------------
root = Tk()
root.title("Image Authenticity Analysis Engine")
root.iconbitmap('images/favicon.ico')
root.protocol("WM_DELETE_WINDOW", root.quit)
root.state("zoomed")
root.configure(bg=BG_COLOR)

# ----------------- LABELS -----------------
resultLabel = Label(root, text="Image Authenticity Analysis Engine", font=("Times New Roman", 30),
                    bg=BG_COLOR, fg=FG_COLOR)
resultLabel.pack(pady=20)

fileLabel = Label(root, text="No file selected", fg="white", bg=BG_COLOR, font=("Times", 15))
fileLabel.pack(pady=5)

# ----------------- IMAGE DISPLAY -----------------
image_frame = Frame(root, bg=BG_COLOR)
image_frame.pack(pady=10)

inputPanel = Label(image_frame, bg=BG_COLOR)
inputPanel.pack(side=LEFT, padx=10)

middlePanel = Label(image_frame, bg=BG_COLOR)
middlePanel.pack(side=LEFT, padx=10)

resultPanel = Label(image_frame, bg=BG_COLOR)
resultPanel.pack(side=LEFT, padx=10)

# ----------------- PROGRESS BAR -----------------
progressBar = ttk.Progressbar(root, length=600)
progressBar.pack(pady=10)

# ----------------- UPLOAD BUTTON -----------------
uploadButton = Button(root, text="Upload Image", font=("Times", 15), fg=FG_COLOR,
                      bg=BTN_BG, relief=RIDGE, bd=2, command=browseFile)
uploadButton.pack(pady=15)

# ----------------- ANALYSIS BUTTONS FRAME -----------------
buttons_frame = Frame(root, bg=BG_COLOR)
buttons_frame.pack(pady=10)

# ----------------- DESCRIPTION LABEL -----------------
descriptionLabel = Label(root, text="Hover over a button to see its description",
                         font=("Times New Roman", 14), bg=BG_COLOR, fg=FG_COLOR,
                         justify="left", anchor="w", wraplength=1000)
descriptionLabel.pack(pady=15)

# ----------------- HELPER FUNCTION FOR BUTTONS WITH HOVER & DESCRIPTION -----------------
def make_hover_button(parent, text, command, description):
    btn = Button(parent, text=text, font=("Times", 12), fg=FG_COLOR, bg=BTN_BG,
                 relief=RIDGE, bd=5, padx=15, pady=5, command=command)
    btn.pack(side=LEFT, padx=10)

    def on_enter(e):
        btn['bg'] = BTN_HOVER
        btn['fg'] = 'white'
        descriptionLabel.config(text=description)

    def on_leave(e):
        btn['bg'] = BTN_BG
        btn['fg'] = FG_COLOR
        descriptionLabel.config(text="Hover over a button to see its description")

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn

# ----------------- CREATE BUTTONS -----------------
make_hover_button(buttons_frame, "Compression Detection", jpeg_Compression,
                  "Detects single or double JPEG compression in the image.")
make_hover_button(buttons_frame, "Metadata Analysis", metadata_analysis,
                  "Displays image metadata information including EXIF data.")
make_hover_button(buttons_frame, "CFA Artifact Detection", cfa_artifact,
                  "Detects sensor pattern inconsistencies indicating manipulations.")
make_hover_button(buttons_frame, "Noise Inconsistency", noise_variance_inconsistency,
                  "Detects unusual noise patterns which may indicate tampering.")
make_hover_button(buttons_frame, "Copy-Move Detection", copy_move_forgery,
                  "Finds duplicated regions within the image indicating forgery.")
make_hover_button(buttons_frame, "Error-Level Analysis", ela_analysis,
                  "Highlights manipulated areas based on compression artifacts.")
make_hover_button(buttons_frame, "Image Extraction", image_decode,
                  "Decodes hidden or steganography data from the image.")
make_hover_button(buttons_frame, "String Extraction", string_analysis,
                  "Shows the raw byte content of the image.")
make_hover_button(buttons_frame, "Exit Program", root.destroy,
                  "Closes the application.")

# ----------------- RUN GUI -----------------
root.mainloop()
