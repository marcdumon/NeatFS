from pathlib import Path

import pandas as pd

from neat_fs.utils import parse_file_mode


def walk_directory_tree(
    root_path: str | Path = '.',
    exclude_paths: list[str] = [],
    output_file: str = 'data/fs_index.csv',
    batch_size: int = 100_000,
    hash_algo: str = 'sha1',
):
    """
    Walk the directory tree and save metadata to CSV in batches.
    """
    if isinstance(root_path, str):
        root_path = Path(root_path)

    files = []
    first_batch = True

    for path in root_path.rglob('*'):
        if any(path.is_relative_to(Path(exclude_path)) for exclude_path in exclude_paths):
            continue

        print(path)

        try:
            s = path.stat()
        except FileNotFoundError:
            print(f'File not found: {path}')
            continue
        except PermissionError:
            print(f'Permission error: {path}')
            continue
        except Exception as e:
            print(f'Error: {e}')
            continue

        if path.is_file() or path.is_dir():
            s = path.stat()
            files.append(
                {
                    'path': path,
                    'name': path.name,
                    'stem': path.stem,
                    'suffix': path.suffix,
                    'parent': path.parent,
                    'size': s.st_size,
                    'mode': s.st_mode,
                    'type': parse_file_mode(s.st_mode)[0],
                    'perm': parse_file_mode(s.st_mode)[1],
                    'uid': s.st_uid,
                    'gid': s.st_gid,
                    'nlink': s.st_nlink,
                    'inode': s.st_ino,
                    'is_symlink': path.is_symlink(),
                    'is_hardlink': s.st_nlink > 1,
                    'symlink_target': path.readlink() if path.is_symlink() else None,
                    'created_at': pd.to_datetime(s.st_ctime, unit='s'),
                    'modified_at': pd.to_datetime(s.st_mtime, unit='s'),
                    'accessed_at': pd.to_datetime(s.st_atime, unit='s'),
                    'device': s.st_dev,
                }
            )

            # Save batch when reaching batch_size
            if len(files) >= batch_size:
                df = pd.DataFrame(files)
                df.to_csv(output_file, mode='a', header=first_batch, index=False)
                print(f'Saved batch of {len(files)} files')
                first_batch = False
                files.clear()

    # Save remaining files
    if files:
        df = pd.DataFrame(files)
        df.to_csv(output_file, mode='a', header=first_batch, index=False)
        print(f'Saved final batch of {len(files)} files')


if __name__ == '__main__':
    import time

    start_time = time.time()
    walk_directory_tree(
        '/',
        exclude_paths=['/mnt/Backup'],
        output_file='data/fs_index.csv',
        batch_size=100000,
        hash_algo='sha1',
    )
    end_time = time.time()

    print(f'Total indexing time: {end_time - start_time:.2f} seconds')
