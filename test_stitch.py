import math
import os
from PIL import Image

def stitch_images(media_dir):
    sheets_dir = os.path.join(media_dir, "contact_sheets")
    sheet_files = sorted([f for f in os.listdir(sheets_dir) if f.endswith(".jpg")])
    images = [Image.open(os.path.join(sheets_dir, f)) for f in sheet_files]
    
    # We want to create a grid of these contact sheets
    cols = 3
    rows = math.ceil(len(images) / cols)
    w, h = images[0].size
    
    # Optional: resize them to be smaller to fit in a reasonable image size
    # But wait, resizing doesn't matter for tokens, but it matters for RAM.
    # Let's resize each sheet to 800 width (maintain aspect)
    w_new = 400
    h_new = int(h * (w_new / w))
    
    stitched = Image.new('RGB', (cols * w_new, rows * h_new), (255, 255, 255))
    
    for i, img in enumerate(images):
        img_resized = img.resize((w_new, h_new))
        x = (i % cols) * w_new
        y = (i // cols) * h_new
        stitched.paste(img_resized, (x, y))
        
    stitched_path = os.path.join(media_dir, "master_contact_sheet.jpg")
    stitched.save(stitched_path)
    print("Stitched successfully.")
    
stitch_images("/Users/athakur/Downloads/taliban")
