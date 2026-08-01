#!/usr/bin/env python3
"""
生成 Suki 健康管理 PWA 图标
- 从 source 图抠出小新，去掉白底
- 参考 liquid glass 风格加圆角半透明玻璃边框
- 输出 192/512/1024 + apple-touch-icon
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

SRC = '/Users/a13249605744/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/c0pe_10_8f6a/temp/RWTemp/2026-08/c2b619f5e1f8875b02e16d65c5bc64e4.jpg'
OUT_DIR = '/Users/a13249605744/WorkBuddy/2026-07-31-20-43-36/diet-tracker-web'
SIZES = {
    'icon-192.png': 192,
    'icon-512.png': 512,
    'icon-1024.png': 1024,
    'apple-touch-icon.png': 180,
}

def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))

def remove_white_background(img, threshold=38):
    """用边缘 flood fill 去除连续白色背景，保留主体内部白色。"""
    img = img.convert('RGBA')
    w, h = img.size
    pixels = img.load()
    # 创建背景 mask：True = 已访问/背景
    visited = [[False] * h for _ in range(w)]
    stack = []
    # 从四边边界开始
    for x in range(w):
        stack.append((x, 0))
        stack.append((x, h - 1))
    for y in range(1, h - 1):
        stack.append((0, y))
        stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if x < 0 or x >= w or y < 0 or y >= h or visited[x][y]:
            continue
        r, g, b, _ = pixels[x, y]
        if color_distance((r, g, b), (255, 255, 255)) < threshold:
            visited[x][y] = True
            stack.append((x + 1, y))
            stack.append((x - 1, y))
            stack.append((x, y + 1))
            stack.append((x, y - 1))
    # 设置透明
    for x in range(w):
        for y in range(h):
            if visited[x][y]:
                pixels[x, y] = (0, 0, 0, 0)
    return img

def feather_edges(img, iterations=2):
    """轻微羽化边缘，让去背更自然。"""
    r, g, b, a = img.split()
    # 轻微模糊 alpha 以抗锯齿
    a = a.filter(ImageFilter.GaussianBlur(radius=1.2))
    # 增强一点对比度让主体清晰
    a = ImageEnhance.Contrast(a).enhance(1.4)
    return Image.merge('RGBA', (r, g, b, a))

def crop_to_content(img, padding_ratio=0.08):
    """裁剪到主体 bounding box，保留 padding。"""
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    content_w = right - left
    content_h = bottom - top
    pad = int(max(content_w, content_h) * padding_ratio)
    w, h = img.size
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(w, right + pad)
    bottom = min(h, bottom + pad)
    return img.crop((left, top, right, bottom))

def make_liquid_glass_bg(size, radius_ratio=0.26):
    """制作 liquid glass 风格圆角背景（参考图1：半透明浅灰玻璃 + 柔和高光 + 边缘彩色反光）。"""
    W = H = size
    radius = int(size * radius_ratio)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    # 1. 柔和阴影
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    off = int(size * 0.04)
    sdraw.rounded_rectangle(
        [off, off + int(size * 0.02), W - off, H - off + int(size * 0.02)],
        radius=radius,
        fill=(20, 24, 36, 80)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=int(size * 0.08)))
    base = Image.alpha_composite(base, shadow)

    # 2. 玻璃底板：浅灰白半透明（更像图1的 glass 卡片）
    glass = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glass)
    for y in range(H):
        ratio = y / H
        # 顶部亮、底部略暗，整体偏浅灰蓝
        r = int(230 - ratio * 35)
        g = int(234 - ratio * 32)
        b = int(242 - ratio * 28)
        a = int(165 - ratio * 25)
        gdraw.line([(0, y), (W, y)], fill=(r, g, b, a))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W, H], radius=radius, fill=255)
    glass.putalpha(mask)
    base = Image.alpha_composite(base, glass)

    # 3. 顶部/左上柔和高光
    highlight = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(highlight)
    line_w = max(2, int(size * 0.006))
    # 顶部细条高光
    hdraw.rounded_rectangle(
        [line_w * 2, line_w * 2, W - line_w * 2, int(H * 0.07)],
        radius=radius // 2,
        fill=(255, 255, 255, 34)
    )
    # 左上大面积柔光
    hdraw.ellipse([int(W * -0.25), int(H * -0.25), int(W * 0.45), int(H * 0.45)],
                  fill=(255, 255, 255, 22))
    highlight = highlight.filter(ImageFilter.GaussianBlur(radius=int(size * 0.06)))
    # 裁剪高光到圆角
    highlight.putalpha(mask)
    base = Image.alpha_composite(base, highlight)

    # 4. 边缘极细白色描边
    edge = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    edraw = ImageDraw.Draw(edge)
    ew = max(1, int(size * 0.004))
    edraw.rounded_rectangle(
        [ew, ew, W - ew, H - ew],
        radius=radius - ew,
        outline=(255, 255, 255, 60),
        width=ew
    )
    base = Image.alpha_composite(base, edge)

    # 5. 边缘淡淡的彩色柔光（紫/青/粉）
    color_glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cgdraw = ImageDraw.Draw(color_glow)
    cgdraw.ellipse([int(W * 0.7), int(H * 0.7), int(W * 1.05), int(H * 1.05)],
                   fill=(160, 120, 255, 7))
    cgdraw.ellipse([int(W * -0.05), int(H * 0.7), int(W * 0.3), int(H * 1.05)],
                   fill=(100, 220, 210, 5))
    cgdraw.ellipse([int(W * 0.7), int(H * -0.05), int(W * 1.0), int(H * 0.25)],
                   fill=(255, 150, 180, 5))
    color_glow = color_glow.filter(ImageFilter.GaussianBlur(radius=int(size * 0.32)))
    color_glow.putalpha(mask)
    base = Image.alpha_composite(base, color_glow)

    return base

def make_solid_rounded_bg(size, radius_ratio=0.26):
    """深色渐变圆角背景，让图标自成一体。"""
    W = H = size
    radius = int(size * radius_ratio)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 深色渐变：左上灰蓝 → 右下深紫
    for y in range(H):
        ratio = y / H
        r = int(55 - ratio * 25)
        g = int(60 - ratio * 22)
        b = int(78 - ratio * 18)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W, H], radius=radius, fill=255)
    img.putalpha(mask)
    return img

def compose_icon(size):
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    # 1. 实色圆角背景
    canvas = Image.alpha_composite(canvas, make_solid_rounded_bg(size))
    # 2. liquid glass 层
    bg = make_liquid_glass_bg(size)
    canvas = Image.alpha_composite(canvas, bg)

    # 加载并缩放小新
    xiao = Image.open(SRC)
    xiao = remove_white_background(xiao)
    xiao = feather_edges(xiao)
    xiao = crop_to_content(xiao, padding_ratio=0.04)

    # 缩放小新到占画布约 80-84%
    target_ratio = 0.82
    target_w = int(size * target_ratio)
    xiao.thumbnail((target_w, target_w), Image.Resampling.LANCZOS)

    # 居中粘贴
    xw, xh = xiao.size
    paste_x = (size - xw) // 2
    paste_y = (size - xh) // 2 + int(size * 0.02)  # 略下移一点更稳
    canvas.paste(xiao, (paste_x, paste_y), xiao)

    return canvas

def main():
    for filename, size in SIZES.items():
        icon = compose_icon(size)
        out_path = os.path.join(OUT_DIR, filename)
        icon.save(out_path, 'PNG')
        print(f'Saved {out_path} ({size}x{size})')

if __name__ == '__main__':
    main()
