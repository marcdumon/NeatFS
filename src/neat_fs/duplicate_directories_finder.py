"""Duplicate directory finder module."""

import pandas as pd
from collections import defaultdict


def find_duplicate_directories(csv_file: str = './data/files_with_duplicates.csv', output_file: str = './data/duplicate_directories.csv') -> pd.DataFrame:
    """Find duplicate directories where all files in both directories are equal.
    
    Two directories are considered duplicates if and only if every file in one directory
    has a duplicate (same hash) in the other directory, AND both directories have the same
    number of files.
    """
    # Load the CSV
    df = pd.read_csv(csv_file)
    
    # Group ALL files by parent directory
    all_dir_files = defaultdict(list)
    
    for _, row in df.iterrows():
        parent = row['parent']
        file_info = {
            'name': row['name'],
            'hash': row['hash'],
            'size': row['size'],
            'is_dup': row['is_dup']
        }
        all_dir_files[parent].append(file_info)
    
    # Create directory signatures: sorted tuple of hashes for ALL files
    dir_signatures = {}
    
    for directory, files in all_dir_files.items():
        # Check if ALL files in the directory have valid hashes
        all_have_hashes = True
        file_hashes = []
        
        for f in files:
            # Check if hash is valid (not NaN, not empty)
            if pd.isna(f['hash']) or str(f['hash']).strip() == '' or str(f['hash']) == 'nan':
                all_have_hashes = False
                break
            file_hashes.append(str(f['hash']))
        
        # Skip directories where not all files have hashes
        if not all_have_hashes or len(file_hashes) == 0:
            continue
        
        # Create signature from sorted hashes
        sorted_hashes = tuple(sorted(file_hashes))
        
        if sorted_hashes not in dir_signatures:
            dir_signatures[sorted_hashes] = []
        dir_signatures[sorted_hashes].append({
            'directory': directory,
            'file_count': len(files),
            'total_size': sum(f['size'] for f in files)
        })
    
    # Find duplicate directories (signatures with 2+ directories)
    duplicate_dirs = []
    group_id = 0
    
    for signature, dirs in dir_signatures.items():
        if len(dirs) >= 2:
            # All directories with this signature are duplicates of each other
            group_id += 1
            for dir_info in dirs:
                duplicate_dirs.append({
                    'directory': dir_info['directory'],
                    'file_count': dir_info['file_count'],
                    'total_size': dir_info['total_size'],
                    'group_id': group_id
                })
    
    # Create DataFrame
    duplicates_df = pd.DataFrame(duplicate_dirs)
    
    if len(duplicates_df) > 0:
        # Sort by group_id to group duplicates together
        duplicates_df = duplicates_df.sort_values(['group_id', 'directory'])
        
        # Save to CSV
        duplicates_df.to_csv(output_file, index=False)
        
        unique_groups = duplicates_df['group_id'].nunique()
        print(f"Found {unique_groups} groups of duplicate directories")
        print(f"Total duplicate directories: {len(duplicates_df)}")
        print(f"Saved results to {output_file}")
    else:
        print("No duplicate directories found")
    
    return duplicates_df


if __name__ == '__main__':
    # Find duplicate directories
    duplicate_dirs = find_duplicate_directories()
    
    if len(duplicate_dirs) > 0:
        print("\nDuplicate directory groups:")
        for group_id in duplicate_dirs['group_id'].unique():
            group = duplicate_dirs[duplicate_dirs['group_id'] == group_id]
            print(f"\nGroup {group_id} ({group.iloc[0]['file_count']} files, {group.iloc[0]['total_size']/1024/1024:.2f} MB):")
            for _, row in group.iterrows():
                print(f"  - {row['directory']}")

