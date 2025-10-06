"""Duplicate finder module."""

import pandas as pd
import hashlib
from pathlib import Path



def calculate_file_hash(file_path: Path, chunk_size: int = 256*1024) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
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

        if len(file_paths) <= 1: # Single files don't need processing.
            continue

        hash_map = {}
        print('--------------------------------')

        for file_path in file_paths:

            print(size/1024/1024,file_path)

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


def find_duplicates_chunked(df: pd.DataFrame, chunk_size: int = 1000, output_file: str = './data/files_with_duplicates.csv') -> None:
    """Find duplicates in chunks and update CSV incrementally."""
    # Initialize output CSV with headers including is_dup and hash columns
    df_with_headers = df.copy()
    df_with_headers['is_dup'] = 0
    df_with_headers['hash'] = ""
    df_with_headers.head(0).to_csv(output_file, index=False)
    
    total_files = len(df)
    processed_files = 0
    
    print(f"Processing {total_files} files in chunks of {chunk_size}")
    
    # Process data in chunks
    for i in range(0, total_files, chunk_size):
        chunk_end = min(i + chunk_size, total_files)
        chunk = df.iloc[i:chunk_end].copy()
        
        print(f"Processing chunk {i//chunk_size + 1}: files {i+1}-{chunk_end}")
        
        # Find duplicates in this chunk
        chunk_with_duplicates = find_duplicates(chunk)
        
        # Append to CSV (skip header for subsequent chunks)
        chunk_with_duplicates.to_csv(output_file, mode='a', header=False, index=False)
        
        processed_files += len(chunk)
        print(f"Processed {processed_files}/{total_files} files")
    
    print(f"Completed processing all files. Results saved to {output_file}")








if __name__ == '__main__':
    # Load CSV and find duplicates
    df = pd.read_csv('./data/files.csv')
    print(f"Loaded {len(df)} files")
    
    # Find duplicates using chunked processing
    find_duplicates_chunked(df, chunk_size=10_000)
    
    # Load and show statistics
    df_with_duplicates = pd.read_csv('./data/files_with_duplicates.csv')
    duplicate_count = df_with_duplicates['is_dup'].sum()
    print(f"Found {duplicate_count} duplicate files")

