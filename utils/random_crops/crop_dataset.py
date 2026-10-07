#!/usr/bin/env python3
"""
Randomly crop images into 2 or 4 pieces and save them (optionally zipped).

Usage:
    python crop_dataset.py --input /path/to/images --output /path/to/save
    python crop_dataset.py -i ./images -o ./cropped --zip --seed 42
"""

import argparse
import glob
import os
import random
import shutil
import sys

import cv2

IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png", "*.bmp")


def get_random_ratio():
    ratio = random.choice([0.5, 0.4, 0.3, 0.2])
    if random.choice([True, False]):
        ratio = 1.0 - ratio
    return ratio


def crop_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return []

    h, w = img.shape[:2]
    crop_type = random.choice(["2-piece-horizontal", "2-piece-vertical", "4-piece"])
    pieces = []

    if crop_type == "2-piece-horizontal":
        split_col = int(w * get_random_ratio())
        pieces.append(img[:, :split_col])
        pieces.append(img[:, split_col:])

    elif crop_type == "2-piece-vertical":
        split_row = int(h * get_random_ratio())
        pieces.append(img[:split_row, :])
        pieces.append(img[split_row:, :])

    elif crop_type == "4-piece":
        split_row = int(h * get_random_ratio())
        split_col = int(w * get_random_ratio())
        pieces.append(img[:split_row, :split_col])
        pieces.append(img[:split_row, split_col:])
        pieces.append(img[split_row:, :split_col])
        pieces.append(img[split_row:, split_col:])

    # Drop any empty pieces (e.g. extremely small images)
    return [p for p in pieces if p.size > 0]


def find_images(input_dir):
    paths = []
    for ext in IMAGE_EXTENSIONS:
        paths.extend(glob.glob(os.path.join(input_dir, "**", ext), recursive=True))
        # also match uppercase extensions on case-sensitive filesystems
        paths.extend(glob.glob(os.path.join(input_dir, "**", ext.upper()), recursive=True))
    return sorted(set(paths))


def parse_args():
    parser = argparse.ArgumentParser(
        prog="crop_dataset.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Randomly crop every image in a folder into 2 or 4 pieces.\n"
            "\n"
            "For each image, one of these is chosen at random:\n"
            "  - 2 pieces (split left/right)\n"
            "  - 2 pieces (split top/bottom)\n"
            "  - 4 pieces (split both ways)\n"
            "Split positions are random (20%%-80%% of the image).\n"
            "Supported formats: jpg, jpeg, png, bmp"
        ),
        epilog=(
            "examples:\n"
            "  python crop_dataset.py --input ./images --output ./cropped\n"
            "  python crop_dataset.py -i ./images -o ./cropped --zip\n"
            "  python crop_dataset.py -i ./images -o ./cropped --zip --seed 42\n"
            "\n"
            "output files are named <original_name>_crop_<n>.<ext>"
        ),
    )
    parser.add_argument("-i", "--input", required=True, metavar="FOLDER",
                        help="path to the folder containing images "
                             "(searched recursively, including subfolders)")
    parser.add_argument("-o", "--output", required=True, metavar="FOLDER",
                        help="path to the folder where cropped images will be saved "
                             "(created if it doesn't exist)")
    parser.add_argument("-z", "--zip", action="store_true",
                        help="also create a zip archive of the output folder "
                             "(saved next to it as <output>.zip)")
    parser.add_argument("--seed", type=int, default=None, metavar="N",
                        help="random seed (integer) to get the same crops every run")

    # Running with no arguments at all -> show the help instead of an error
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isdir(args.input):
        sys.exit(f"Error: input folder not found: {args.input}")

    if args.seed is not None:
        random.seed(args.seed)

    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    image_paths = find_images(args.input)
    print(f"Found {len(image_paths)} images to process...")

    saved = 0
    for path in image_paths:
        pieces = crop_image(path)
        base_name, ext = os.path.splitext(os.path.basename(path))

        for piece_idx, piece in enumerate(pieces):
            out_path = os.path.join(output_dir, f"{base_name}_crop_{piece_idx}{ext}")
            cv2.imwrite(out_path, piece)
            saved += 1

    print(f"Cropping complete. Saved {saved} pieces to {output_dir}")

    if args.zip:
        print("Creating zip archive...")
        archive = shutil.make_archive(output_dir, "zip", output_dir)
        print(f"Zip file created at {archive}")


if __name__ == "__main__":
    main()