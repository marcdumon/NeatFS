#!/usr/bin/env python3
"""
Test dataset creator for neat_fs duplicate finder testing.

Creates a structured test dataset with:
- Main directories: small, medium, large, xlarge, xxlarge
- Subdirectories: orig, dup, sym, hard
- Various file types: originals, duplicates, symbolic links, hard links
- Subdir with unique files of differennt sizes
"""

import os
import shutil
from pathlib import Path


def create_test_dataset(base_dir='test_dataset'):
    """Create the complete test dataset structure."""

    # File sizes for each category
    sizes = {
        'small': 1024,  # 1KB
        'medium': 102400,  # 100KB
        'large': 1048576,  # 1MB
        'xlarge': 104857600,  # 100MB
        'xxlarge': 1073741824,  # 1GB
    }

    # Create base directory
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    for category, size in sizes.items():
        print(f'Creating {category} dataset ({size} bytes)...')

        # Create main category directory
        cat_dir = base_path / category
        cat_dir.mkdir(exist_ok=True)

        # Create subdirectories
        orig_dir = cat_dir / 'orig'
        dup_dir = cat_dir / 'dup'
        sym_dir = cat_dir / 'sym'
        hard_dir = cat_dir / 'hard'

        for subdir in [orig_dir, dup_dir, sym_dir, hard_dir]:
            subdir.mkdir(exist_ok=True)

        # Create original files
        create_file(orig_dir / 'dup_orig.bin', size)
        create_file(orig_dir / 'nodup_orig.bin', size)
        create_file(orig_dir / 'sym_orig.bin', size)
        create_file(orig_dir / 'hard_orig.bin', size)

        # Create duplicate files
        create_file(dup_dir / 'nodup_dup.bin', size)
        shutil.copy2(orig_dir / 'dup_orig.bin', dup_dir / 'dup_dup.bin')

        # Create symbolic links
        create_file(sym_dir / 'nodup_sym.bin', size)
        (sym_dir / 'dup_sym.bin').symlink_to(orig_dir / 'sym_orig.bin')

        # Create hard links
        create_file(hard_dir / 'nodup_hard.bin', size)
        os.link(orig_dir / 'hard_orig.bin', hard_dir / 'dup_hard.bin')

    # Create unique files directory with files of sizes that are not in the main categories
    print('Creating unique files directory...')
    unique_dir = base_path / 'unique'
    unique_dir.mkdir(exist_ok=True)

    for category, size in sizes.items():
        create_file(unique_dir / f'unique_{category}.bin', size * 2)

    print(f"Test dataset created successfully in '{base_dir}' directory")


def create_file(file_path, size):
    """Create a file with specified size filled with random data."""
    with open(file_path, 'wb') as f:
        # Write random data to fill the file
        remaining = size
        chunk_size = min(8192, remaining)  # Write in 8KB chunks

        while remaining > 0:
            chunk_size = min(chunk_size, remaining)
            f.write(os.urandom(chunk_size))
            remaining -= chunk_size


def main():
    """Main function to create the test dataset."""
    import argparse

    parser = argparse.ArgumentParser(description='Create test dataset for neat_fs')
    parser.add_argument(
        '--output-dir',
        '-o',
        default='/mnt/Databases/neat_fs_test_dataset',
        help='Output directory for test dataset',
    )

    args = parser.parse_args()

    create_test_dataset(args.output_dir)


if __name__ == '__main__':
    main()
