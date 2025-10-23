from pathlib import Path
import pandas as pd
from neat_fs.utils import parse_file_mode

def walk_directory_tree(root_path: str | Path = '.', output_file: str = 'fs_index.csv', batch_size: int = 100_000):
    """
    Walk the directory tree and save metadata to CSV in batches.
    """
    if isinstance(root_path, str):
        root_path = Path(root_path)

    files = []
    first_batch = True
    
    for file_path in root_path.rglob('*'):
        print(file_path)

        try:
            s = file_path.stat()
        except FileNotFoundError:
            print(f'File not found: {file_path}')
            continue
        except PermissionError:
            print(f'Permission error: {file_path}')
            continue
        except Exception as e:
            print(f'Error: {e}')
            continue
        
        if file_path.is_file():
            s = file_path.stat()    
            files.append(
                {
                    'path': file_path,
                    'name': file_path.name,
                    'stem': file_path.stem,
                    'suffix': file_path.suffix,
                    'parent': file_path.parent,
                    'size': s.st_size,
                    'mode': s.st_mode,
                    'type': parse_file_mode(s.st_mode)[0],
                    'perm': parse_file_mode(s.st_mode)[1],
                    'uid': s.st_uid,
                    'gid': s.st_gid,
                    'nlink': s.st_nlink,
                    'inode': s.st_ino,
                    'is_symlink': file_path.is_symlink(),
                    'is_hardlink': s.st_nlink > 1,
                    'symlink_target': file_path.readlink() if file_path.is_symlink() else None,
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
    walk_directory_tree('/', 'data/fs_index.csv', batch_size=100000)


