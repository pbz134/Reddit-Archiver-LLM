import os
import re
import argparse
from pathlib import Path

def find_and_remove_duplicates(directory):
    """
    Recursively scan directory for 'images' and 'videos' subfolders and remove duplicate files.
    Now handles more complex duplicate patterns including multiple underscores and post-extension markers.
    """
    media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi'}
    # More comprehensive pattern that matches:
    # 1. filename_x.ext
    # 2. filename_x_y.ext
    # 3. filename.ext_x
    # 4. filename.ext_x_y
    pattern = re.compile(r'^(.*?)(?:_\d+)+(\.[a-zA-Z0-9]+)?$')
    
    # Walk through the directory tree
    for root, dirs, files in os.walk(directory):
        # Only process 'images' and 'videos' folders
        if os.path.basename(root).lower() not in {'images', 'videos'}:
            continue
            
        for filename in files:
            filepath = Path(root) / filename
            ext = filepath.suffix.lower()
            
            # Skip non-media files
            if ext not in media_extensions and not any(filename.endswith(ext + suffix) for ext in media_extensions for suffix in ['_' + str(i) for i in range(1, 20)]):
                continue
                
            # Check if file matches any duplicate pattern
            match = pattern.match(filename)
            if match:
                # Try multiple possible original filenames
                possible_originals = []
                
                # Case 1: filename_x.ext → filename.ext
                if match.group(2):  # Has extension
                    possible_originals.append(match.group(1) + match.group(2))
                
                # Case 2: filename.ext_x → filename.ext
                if '.' in match.group(1):
                    base, old_ext = match.group(1).rsplit('.', 1)
                    possible_originals.append(f"{base}.{old_ext}")
                
                # Case 3: filename_x_y.ext → filename.ext
                parts = match.group(1).split('_')
                if len(parts) > 1:
                    possible_originals.append('_'.join(parts[:-1]) + (match.group(2) or ''))
                
                # Check all possible originals
                for original_name in possible_originals:
                    original_path = Path(root) / original_name
                    if original_path.exists() and original_path != filepath:
                        try:
                            filepath.unlink()
                            print(f"Removed duplicate: {filepath} (original: {original_path})")
                            break  # Stop checking after first successful removal
                        except OSError as e:
                            print(f"Error removing {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate media files (with _x suffix) from 'images' and 'videos' subfolders."
    )
    parser.add_argument(
        "directory",
        help="Root directory containing 'images' and 'videos' subfolders"
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    print(f"Scanning for duplicates in {args.directory}...")
    find_and_remove_duplicates(args.directory)
    print("Duplicate removal complete.")

if __name__ == "__main__":
    main()