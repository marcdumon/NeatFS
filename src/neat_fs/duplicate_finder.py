"""Duplicate finder module."""

import argparse
import pprint
import pandas as pd
from pathlib import Path

from neat_fs.file_scanner import walk_directory_tree
from neat_fs.utils import setup_logging


def group_files_by_size(files: pd.DataFrame) -> dict[int, list[Path]]:
    """Group files by size."""
    # Convert paths to Path objects
    files['path_obj'] = files['path'].apply(Path)
    
    # Group by size and aggregate paths into lists
    grouped = files.groupby('size')['path_obj'].apply(list).to_dict()
    
    return grouped



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Find duplicate files by size.')
    parser.add_argument('root_path', type=Path, help='The root path to scan.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output.')
    args = parser.parse_args()
    setup_logging(args.verbose)
    files = walk_directory_tree(args.root_path)
    g=group_files_by_size(files)
    pprint.pprint(g)