import os
from PIL import Image, ImageDraw, ImageFont

base_dir = "/Users/athakur/Downloads/taliban/keyframes"
folders = sorted([f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))])

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    images = sorted([img for img in os.listdir(folder_path) if img.endswith(".jpg")])
    if not images:
        continue
    
    # Load first image to get dimensions
    sample_img = Image.open(os.path.join(folder_path, images[0]))
    w, h = sample_img.size
    
    # Calculate grid size (e.g., 4 columns)
    cols = 4
    rows = (len(images) + cols - 1) // cols
    
    # Create large canvas
    grid_w = w * cols
    grid_h = h * rows
    canvas = Image.new("RGB", (grid_w, grid_h), "white")
    draw = ImageDraw.Draw(canvas)
    
    for idx, img_name in enumerate(images):
        img_path = os.path.join(folder_path, img_name)
        img = Image.open(img_path)
        
        # Calculate position
        c = idx % cols
        r = idx // cols
        x = c * w
        y = r * h
        
        # Paste image
        canvas.paste(img, (x, y))
        
        # Draw frame number
        draw.rectangle([x, y, x + 80, y + 40], fill="black")
        draw.text((x + 10, y + 10), f"#{idx+1}", fill="white")
        
    # Save contact sheet
    sheet_path = os.path.join(base_dir, f"{folder}_contact_sheet.jpg")
    canvas.save(sheet_path)
    print(f"Created contact sheet: {sheet_path}")
