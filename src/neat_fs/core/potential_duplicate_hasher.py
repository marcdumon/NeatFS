import hashlib
from pathlib import Path

import pandas as pd


def calculate_file_hash(
    hash_algo: str, file_path: str | Path, chunk_size: int = 256 * 1024
) -> str:
    """Calculate hash of a file using the given hash algorithm."""
    if hash_algo not in hashlib.algorithms_available:
        raise ValueError(f'Hash algorithm {hash_algo} is not available in hashlib.')
    if isinstance(file_path, str):
        file_path = Path(file_path)
    try:
        hash_algo = hashlib.new(hash_algo)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_algo.update(chunk)
        return hash_algo.hexdigest()
    except (IOError, OSError) as e:
        print(e)
        return ''


def hash_potential_duplicates(df: pd.DataFrame, output_file: str = 'data/hashed_duplicates.csv', batch_size: int = 1000) -> pd.DataFrame:
    """Hash files that have other files with the same size. These are potential duplicates."""
    # Count file sizes
    df['size_count'] = df.groupby('size')['size'].transform('count')
    
    # Get files that need hashing
    files_to_hash = df[(df['size_count'] > 1) & (df['type'] == 'file')&(df['size'] > 0)].copy()
    
    batch_count = 0
    first_batch = True
    processed_indices = []
    
    for i, row in files_to_hash.iterrows():
        print(f"Hashing: {row['path']} ({row['size']} bytes)")
        hash_value = calculate_file_hash('sha1', row['path'])
        df.at[i, 'hash'] = hash_value
        processed_indices.append(i)
        
        batch_count += 1
        
        # Save batch when reaching batch_size
        if batch_count >= batch_size:
            # Save only the hashed rows from this batch
            batch_df = df.loc[processed_indices[-batch_size:]]
            batch_df.to_csv(output_file, mode='a', header=first_batch, index=False)
            print(f'Saved batch of {batch_count} hashed files')
            first_batch = False
            batch_count = 0
    
    # Save remaining files
    if batch_count > 0:
        batch_df = df.loc[processed_indices[-batch_count:]]
        batch_df.to_csv(output_file, mode='a', header=first_batch, index=False)
        print(f'Saved final batch of {batch_count} hashed files')
    
    return df



if __name__ == "__main__":
    import time

    start_time = time.time()
    df = pd.read_csv('data/fs_index.csv')
    hash_potential_duplicates(df, 'data/hashed_duplicates.csv', batch_size=1000)
    end_time = time.time()
    print(f'Total time: {end_time - start_time:.2f} seconds')

