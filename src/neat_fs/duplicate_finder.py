"""Duplicate finder module."""

import pandas as pd
import hashlib
from pathlib import Path



def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, OSError):
        return ""


def group_files_by_size(files: pd.DataFrame) -> dict[int, list[Path]]:
    """Group files by size."""
    # Convert paths to Path objects
    files['file_path'] = files['path'].apply(Path)
    
    # Group by size and aggregate paths into lists
    grouped = files.groupby('size')['file_path'].apply(list).to_dict()
    
    return grouped


def find_duplicates(files: pd.DataFrame) -> pd.DataFrame:
    """Find duplicate files and update DataFrame with is_dup and hash columns."""
    # Add is_dup and hash columns initialized to 0 and empty string
    files = files.copy()
    files['is_dup'] = 0
    files['hash'] = ""
    
    # Group files by size
    grouped = group_files_by_size(files)
    
    # Process each size group
    for size, file_paths in grouped.items():
        if len(file_paths) <= 1:
            # Single files get empty hash
            for path in file_paths:
                files.loc[files['file_path'] == path, 'hash'] = ""
            continue
        
        # Calculate hashes for all files of this size
        hash_map = {}
        for file_path in file_paths:
            file_hash = calculate_file_hash(file_path)
            if file_hash:
                # Store hash in DataFrame
                files.loc[files['file_path'] == file_path, 'hash'] = file_hash
                
                if file_hash not in hash_map:
                    hash_map[file_hash] = []
                hash_map[file_hash].append(file_path)
        
        # Mark duplicates (files with same hash)
        for file_hash, duplicate_paths in hash_map.items():
            if len(duplicate_paths) > 1:
                # Mark all files with this hash as duplicates
                for path in duplicate_paths:
                    files.loc[files['file_path'] == path, 'is_dup'] = 1
    
    # Clean up temporary column
    files = files.drop('file_path', axis=1)
    
    return files








if __name__ == '__main__':
    # Load CSV and find duplicates
    df = pd.read_csv('./data/files.csv')
    print(f"Loaded {len(df)} files")
    
    # Find duplicates
    df_with_duplicates = find_duplicates(df)
    
    # Show statistics
    duplicate_count = df_with_duplicates['is_dup'].sum()
    print(f"Found {duplicate_count} duplicate files")
    
    # Save updated CSV
    df_with_duplicates.to_csv('./data/files_with_duplicates.csv', index=False)
    print("Saved results to ./data/files_with_duplicates.csv")

