from pathlib import Path
from PIL import Image

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def is_valid_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()  # 只校验，不加载像素
        return True
    except Exception:
        return False


def scan_images(root: Path):
    images = []

    for p in root.rglob('*'):
        if not p.is_file():
            continue

        if p.suffix.lower() not in IMAGE_EXTS:
            continue

        if is_valid_image(p):
            images.append(p)
        else:
            # 生产中建议记录日志
            print(f"[跳过非法图片] {p}")

    return images

