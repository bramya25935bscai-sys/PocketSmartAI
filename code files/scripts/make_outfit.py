"""Generate a simple sample outfit image (no copyrighted photos)."""
from pathlib import Path
from PIL import Image, ImageDraw

out = Path(__file__).resolve().parent.parent / "pocketsmart" / "static" / "img" / "sample_outfit.png"
out.parent.mkdir(parents=True, exist_ok=True)
img = Image.new("RGB", (480, 720), (244, 228, 214))
d = ImageDraw.Draw(img)
d.rectangle([140, 40, 340, 160], fill=(232, 190, 160))  # face
d.rectangle([80, 180, 400, 520], fill=(196, 92, 92))  # peach-red kurta
d.polygon([(80, 180), (240, 80), (400, 180)], fill=(139, 35, 50))  # dupatta hint
d.rectangle([160, 520, 320, 700], fill=(45, 40, 60))  # palazzo
d.ellipse([200, 200, 280, 250], outline=(201, 162, 39), width=6)  # necklace
img.save(out)
print("wrote", out)
