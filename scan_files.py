import argparse
import hashlib
import logging
import sys
from collections import defaultdict # noqa: F401
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format='%(message)s', handlers=[logging.StreamHandler()]
    )


def walk_directory_tree(root_path: Path) -> pd.DataFrame:
    """
    Walk the directory tree and return a pandas DataFrame with the file metadata.
    """
    files = []
    for file_path in root_path.rglob('*'):
        if file_path.is_file():
            try:
                s = (
                    file_path.stat()
                )  # Todo: Factor out these things into a separate function.
                # Extract only permission bits and convert to octal numeric
                perm = oct(s.st_mode & 0o777)[2:]  # e.g., '644', '700'
                files.append(  # Todo: Factor out these things into a separate function.
                    {
                        'path': file_path,
                        'name': file_path.name,
                        'stem': file_path.stem,
                        'suffix': file_path.suffix,
                        'parent': str(file_path.parent),
                        'size': s.st_size,
                        'mode': s.st_mode,
                        'perm': perm,
                        'uid': s.st_uid,
                        'gid': s.st_gid,
                        'nlink': s.st_nlink,
                    }
                )
            except (OSError, FileNotFoundError) as e:
                logging.warning(f"Could not get stats for {file_path}: {e}")
    return pd.DataFrame(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Scan a directory tree and return a pandas DataFrame with the file information.'
    )
    parser.add_argument('root_path', type=Path, help='The root path to scan.')
    args = parser.parse_args()
    df = walk_directory_tree(args.root_path)
    print(df)
    print(df[['uid', 'gid']])
    df.to_csv('files.csv', index=False)
    xx = df.groupby(['size', 'stem']).agg({'path': 'count'}).reset_index()
    print(xx)
