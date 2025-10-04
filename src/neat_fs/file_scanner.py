import argparse
import logging
from pathlib import Path

import pandas as pd

from neat_fs.utils import parse_file_mode, setup_logging


def walk_directory_tree(root_path: Path) -> pd.DataFrame:
    """
    Walk the directory tree and return a pandas DataFrame with the file metadata.
    """
    files = []
    for file_path in root_path.rglob('*'):
        if file_path.is_file():
            try:
                s = file_path.stat()
                # Extract only permission bits and convert to octal numeric
                file_type, permissions = parse_file_mode(s.st_mode)
                
                # Get symlink target if it's a symlink
                symlink_target = None
                if file_path.is_symlink():
                    try:
                        symlink_target = str(file_path.readlink())
                    except (OSError, FileNotFoundError) as e:
                        logging.warning(f'Could not read symlink target for {file_path}: {e}')
                        symlink_target = 'broken_link'
                
                files.append(
                    {
                        'path': file_path,
                        'name': file_path.name,
                        'stem': file_path.stem,
                        'suffix': file_path.suffix,
                        'parent': str(file_path.parent),
                        'size': s.st_size,
                        'mode': s.st_mode,
                        'type': file_type,
                        'perm': permissions,
                        'uid': s.st_uid,
                        'gid': s.st_gid,
                        'nlink': s.st_nlink,
                        'inode': s.st_ino,
                        'is_symlink': file_path.is_symlink(),
                        'symlink_target': symlink_target,
                    }
                )
            except (OSError, FileNotFoundError) as e:
                logging.warning(f'Could not get stats for {file_path}: {e}')
    return pd.DataFrame(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Scan a directory tree and return a pandas DataFrame with the file information.'
    )
    parser.add_argument(
        'root_path',
        type=Path,
        help='The root path to scan.',
        default=Path('/mnt/Media/'),
        nargs='?',
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Enable verbose output'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    df = walk_directory_tree(args.root_path)
    logging.debug(df)
    df.to_csv('./data/files.csv', index=False)
