"""Generate DictaFlow icon as .ico file"""
from PIL import Image, ImageDraw

sizes = [16, 32, 48, 64, 128, 256]
images = []

for size in sizes:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Purple circle background
    margin = max(1, size // 16)
    draw.ellipse([margin, margin, size - margin - 1, size - margin - 1], fill=(130, 80, 255, 255))
    
    # Microphone body (white rounded rect)
    cx, cy = size // 2, size // 2
    mic_w = max(2, size // 6)
    mic_h = max(3, int(size * 0.22))
    mic_top = cy - int(size * 0.16)
    r = max(1, mic_w // 2)
    draw.rounded_rectangle(
        [cx - mic_w, mic_top, cx + mic_w, mic_top + mic_h],
        radius=r, fill=(255, 255, 255, 255)
    )
    
    # Mic arc (U shape below body)
    arc_w = max(3, int(mic_w * 1.8))
    arc_top = mic_top + max(1, mic_h // 3)
    arc_bottom = mic_top + mic_h + max(2, size // 10)
    lw = max(1, size // 32)
    draw.arc(
        [cx - arc_w, arc_top, cx + arc_w, arc_bottom + max(2, size // 12)],
        0, 180, fill=(255, 255, 255, 255), width=lw
    )
    
    # Mic stand (vertical line)
    stand_top = arc_bottom
    stand_bottom = stand_top + max(2, size // 10)
    draw.rectangle(
        [cx - max(1, lw // 2), stand_top, cx + max(1, lw // 2), stand_bottom],
        fill=(255, 255, 255, 255)
    )
    
    # Mic base (horizontal line)
    base_w = max(2, int(mic_w * 1.5))
    draw.rectangle(
        [cx - base_w, stand_bottom, cx + base_w, stand_bottom + lw],
        fill=(255, 255, 255, 255)
    )
    
    images.append(img)

# Save as .ico
images[-1].save(
    r"B:\Aplicaciones\dictaflow\assets\icon.ico",
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=images[:-1]
)
print("Icon saved OK")
