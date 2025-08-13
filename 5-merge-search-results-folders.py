import os
import shutil
from pathlib import Path

def move_media_files(input_dir, output_dir):
    """
    Moves all files from subfolders (with 'images' and 'videos') into a single output folder.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directories if they don't exist
    (output_path / "images").mkdir(parents=True, exist_ok=True)
    (output_path / "videos").mkdir(parents=True, exist_ok=True)

    # Track moved files to avoid overwrites
    moved_files = set()

    # Walk through input directory
    for root, _, files in os.walk(input_dir):
        root_path = Path(root)

        # Determine if this is an 'images' or 'videos' subfolder
        if root_path.name == "images":
            dest_folder = output_path / "images"
        elif root_path.name == "videos":
            dest_folder = output_path / "videos"
        else:
            continue  # Skip non-media folders

        # Move each file to the consolidated folder
        for file in files:
            src_file = root_path / file
            dest_file = dest_folder / file

            # Handle filename conflicts by appending a number
            counter = 1
            while dest_file.exists():
                stem = dest_file.stem
                suffix = dest_file.suffix
                dest_file = dest_folder / f"{stem}_{counter}{suffix}"
                counter += 1

            shutil.move(str(src_file), str(dest_file))  # Move instead of copy
            moved_files.add(str(dest_file))

    print(f"\n✅ Successfully moved files to: {output_dir}")
    print(f"📂 Total images: {len(list((output_path / 'images').glob('*')))}")
    print(f"🎥 Total videos: {len(list((output_path / 'videos').glob('*')))}")

if __name__ == "__main__":
    print("=== Media Folder Merger (Move Files) ===")
    input_dir = input("Enter input directory (e.g., './search-results/media/nikkemobile'): ").strip()
    output_dir = input("Enter output directory (e.g., './merged_media'): ").strip()

    if not os.path.exists(input_dir):
        print(f"❌ Error: Input directory '{input_dir}' does not exist!")
        exit(1)

    move_media_files(input_dir, output_dir)