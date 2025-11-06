import os
import argparse
from PIL import Image


def is_image_file(filename: str) -> bool:
    name = filename.lower()
    return name.endswith('.jpg') or name.endswith('.jpeg') or name.endswith('.png')


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def optimize_image(src_path: str, dst_path: str, max_size: int, quality: int) -> bool:
    try:
        with Image.open(src_path) as img:
            # Convert paletted/RGBA to RGB for JPEG
            if img.mode in ("P", "RGBA"):
                img = img.convert("RGB")
            # Resize in-place if larger than max_size
            img.thumbnail((max_size, max_size), Image.LANCZOS)

            # Save as JPEG (even from PNG) to cut bytes for photos
            img.save(dst_path, format='JPEG', quality=quality, optimize=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed optimize {src_path}: {e}")
        return False


def generate_thumb(src_path: str, thumb_path: str, thumb_size: int, quality: int) -> bool:
    try:
        with Image.open(src_path) as img:
            if img.mode in ("P", "RGBA"):
                img = img.convert("RGB")
            img.thumbnail((thumb_size, thumb_size), Image.LANCZOS)
            img.save(thumb_path, format='WEBP', quality=quality, method=6)
        return True
    except Exception as e:
        print(f"[ERROR] Failed thumb {src_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Optimize existing upload images and generate fast thumbnails (WebP).')
    parser.add_argument('--uploads', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads'), help='Path to static/uploads directory')
    parser.add_argument('--max-size', type=int, default=1200, help='Max dimension for optimized main image')
    parser.add_argument('--quality', type=int, default=75, help='JPEG/WebP quality (1-95)')
    parser.add_argument('--thumb-size', type=int, default=256, help='Max dimension for thumbnails')
    parser.add_argument('--replace-webp', action='store_true', help='Replace original image with a WEBP of same base name and delete the original')
    parser.add_argument('--force', action='store_true', help='Recreate outputs even if they exist')
    args = parser.parse_args()

    uploads_dir = args.uploads
    thumbs_dir = os.path.join(uploads_dir, 'thumbs')
    ensure_dir(thumbs_dir)

    total = 0
    optimized = 0
    thumbed = 0

    for fname in os.listdir(uploads_dir):
        src_path = os.path.join(uploads_dir, fname)
        if not os.path.isfile(src_path):
            continue
        if fname.lower() == 'default.jpg':
            continue
        if not is_image_file(fname):
            continue

        total += 1

        name_no_ext, ext = os.path.splitext(fname)
        # Optimized main target (JPEG), keeping same lowercase name with .jpg extension
        optimized_name = f"{name_no_ext.lower()}.jpg"
        optimized_path = os.path.join(uploads_dir, optimized_name)

        # Create/overwrite optimized main only if force or file is very large
        try_optimize = args.force or (os.path.getsize(src_path) > 800 * 1024)
        if try_optimize:
            if args.force or not os.path.exists(optimized_path) or optimized_path == src_path:
                if optimize_image(src_path, optimized_path, args.max_size, args.quality):
                    optimized += 1

        # Thumbnail
        thumb_path = os.path.join(thumbs_dir, f"{name_no_ext.lower()}_thumb.webp")
        if args.force or not os.path.exists(thumb_path):
            if generate_thumb(optimized_path if os.path.exists(optimized_path) else src_path, thumb_path, args.thumb_size, args.quality):
                thumbed += 1

        # Replace originals with WEBP if requested
        if args.replace_webp:
            webp_target = os.path.join(uploads_dir, f"{name_no_ext.lower()}.webp")
            # Only convert if missing or forced
            if args.force or not os.path.exists(webp_target):
                try:
                    with Image.open(optimized_path if os.path.exists(optimized_path) else src_path) as img:
                        if img.mode in ("P", "RGBA"):
                            img = img.convert("RGB")
                        img.thumbnail((args.max_size, args.max_size), Image.LANCZOS)
                        img.save(webp_target, format='WEBP', quality=args.quality, method=6)
                except Exception as e:
                    print(f"[ERROR] Failed convert to webp {src_path}: {e}")
            # Delete the original non-webp file (safeguard)
            try:
                if os.path.exists(src_path) and src_path.lower() != webp_target.lower() and ext.lower() != '.webp':
                    os.remove(src_path)
            except Exception as e:
                print(f"[WARN] Could not delete {src_path}: {e}")

    print(f"Processed {total} images. Optimized: {optimized}, Thumbs: {thumbed}")


if __name__ == '__main__':
    main()


