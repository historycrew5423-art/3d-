"""Put the walk-cycle frames side by side in one image.

Usage: blender-py make_sheet.py <out_dir>    (needs Pillow: bpyenv/bin/pip install pillow)
"""
import sys

from PIL import Image

out = sys.argv[1]
frames = [Image.open(f"{out}/walk_{f:02d}.png").convert("RGB") for f in (0, 12, 24, 36)]
w, h = frames[0].size
sheet = Image.new("RGB", (w * len(frames), h))
for i, im in enumerate(frames):
    sheet.paste(im, (i * w, 0))
sheet.save(f"{out}/walk_sheet.png")
print("saved", f"{out}/walk_sheet.png", sheet.size)
