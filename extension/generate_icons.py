#!/usr/bin/env python3
"""
Run this to generate placeholder extension icons.
pip install Pillow
python generate_icons.py
"""
try:
    from PIL import Image, ImageDraw, ImageFont
    import os

    os.makedirs('icons', exist_ok=True)

    for size in [16, 48, 128]:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Cyan gradient background circle
        draw.rounded_rectangle([0, 0, size-1, size-1], radius=size//5,
                                fill=(8, 145, 178, 255))
        # "B" letter
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size//2)
        except:
            font = ImageFont.load_default()
        text = '⚡'
        draw.text((size//2, size//2), '⚡', fill='white', anchor='mm', font=font)
        img.save(f'icons/icon{size}.png')
        print(f'Generated icon{size}.png')
    print('Icons generated! ✅')
except ImportError:
    print('Pillow not installed. Run: pip install Pillow')
    print('Or manually add PNG icons to extension/icons/ folder (16px, 48px, 128px)')
