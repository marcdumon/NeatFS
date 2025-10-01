#!/usr/bin/env python3
"""
Duplicate Files and Directories Finder

A script that finds all duplicate files and directories in a given directory path.

File Workflow:
1. Walks the directory tree
2. Groups by file size (fast filter)  
3. Hashes only equal-sized files
4. Reports sets of duplicate files

Directory Workflow:
1. Scans all directories
2. Analyzes directory contents (file names, sizes, hashes)
3. Compares directory signatures
4. Reports directories with identical contents
"""

import sys
import hashlib
import argparse
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class DuplicateItem:
    """Represents a duplicate item (file or directory) with its metadata."""
    path: Path
    size: int
    item_type: str  # 'file' or 'directory'


@dataclass
class DuplicateSet:
    """Represents a set of duplicate items."""
    hash_signature: str
    items: List[DuplicateItem]
    item_type: str  # 'file' or 'directory'
    
    @property
    def total_size(self) -> int:
        """Total size of one item (all items in set have same size)."""
        return self.items[0].size if self.items else 0
    
    @property
    def wasted_space(self) -> int:
        """Space wasted by duplicates (size * number of extra copies)."""
        return self.total_size * (len(self.items) - 1)
    
    @property
    def duplicate_count(self) -> int:
        """Number of duplicate items (excluding the original)."""
        return len(self.items) - 1


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )


def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, OSError) as e:
        logging.warning(f"Could not read file {file_path}: {e}")
        return ""


def walk_directory_tree_and_group_by_size(root_path: Path) -> Dict[int, List[Path]]:
    """
    Walk the directory tree and directly group files by size.
    Returns a dictionary mapping file_size -> list of file paths.
    """
    size_groups: Dict[int, List[Path]] = defaultdict(list)
    
    try:
        for file_path in root_path.rglob('*'):
            if file_path.is_file():
                try:
                    file_size: int = file_path.stat().st_size
                    size_groups[file_size].append(file_path)
                except (OSError, FileNotFoundError) as e:
                    logging.warning(f"Could not get size for {file_path}: {e}")
    except (OSError, PermissionError) as e:
        logging.error(f"Error accessing directory {root_path}: {e}")
    
    return size_groups


def find_duplicates_by_hash(size_groups: Dict[int, List[Path]]) -> List[DuplicateSet]:
    """Hash files of equal size and group by hash to find duplicates."""
    duplicate_sets: List[DuplicateSet] = []
    
    for size, file_paths in size_groups.items():
        # Skip single files - they can't be duplicates by size
        if len(file_paths) < 2:
            continue
            
        logging.info(f"Hashing {len(file_paths)} files of size {size:,} bytes...")
        
        hash_groups: Dict[str, List[Path]] = defaultdict(list)
        for file_path in file_paths:
            file_hash: str = calculate_file_hash(file_path)
            if file_hash:  # Only add if hash was successfully calculated
                hash_groups[file_hash].append(file_path)
        
        # Only keep groups with multiple files (actual duplicates)
        for file_hash, paths in hash_groups.items():
            if len(paths) > 1:
                items: List[DuplicateItem] = [
                    DuplicateItem(path=path, size=size, item_type='file') 
                    for path in paths
                ]
                duplicate_sets.append(DuplicateSet(
                    hash_signature=file_hash,
                    items=items,
                    item_type='file'
                ))
    
    return duplicate_sets


def get_directory_signature(directory_path: Path) -> Tuple[str, int]:
    """
    Calculate a signature for a directory based on its contents.
    Returns a tuple of (content_hash, total_size).
    """
    files_info: List[str] = []
    total_size: int = 0
    
    try:
        # Get all files in the directory (non-recursive)
        files: List[Path] = [f for f in directory_path.iterdir() if f.is_file()]
        
        # Sort files by name for consistent ordering
        files.sort(key=lambda x: x.name)
        
        for file_path in files:
            try:
                file_size: int = file_path.stat().st_size
                file_hash: str = calculate_file_hash(file_path)
                if file_hash:  # Only include if hash was successful
                    files_info.append(f"{file_path.name}:{file_size}:{file_hash}")
                    total_size += file_size
            except (OSError, FileNotFoundError) as e:
                logging.warning(f"Could not process file {file_path}: {e}")
        
        # Create a hash of all file information
        content_string: str = "|".join(files_info)
        content_hash: str = hashlib.md5(content_string.encode()).hexdigest()
        
        return content_hash, total_size
        
    except (OSError, PermissionError) as e:
        logging.warning(f"Could not access directory {directory_path}: {e}")
        return "", 0


def find_duplicate_directories(root_path: Path) -> List[DuplicateSet]:
    """
    Find directories that contain exactly the same files.
    Returns a list of DuplicateSet objects for duplicate directories.
    """
    directory_signatures: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)
    
    try:
        # Walk through all directories using pathlib
        for directory_path in root_path.rglob('*'):
            if not directory_path.is_dir():
                continue
            
            # Check if directory has files (not empty)
            has_files: bool = any(item.is_file() for item in directory_path.iterdir())
            if not has_files:
                continue
            
            # Calculate signature for this directory
            content_hash, total_size = get_directory_signature(directory_path)
            
            if content_hash and total_size > 0:  # Only consider directories with content
                directory_signatures[content_hash].append((directory_path, total_size))
    
    except (OSError, PermissionError) as e:
        logging.error(f"Error walking directories in {root_path}: {e}")
    
    # Convert to DuplicateSet objects
    duplicate_sets: List[DuplicateSet] = []
    for content_hash, dir_info_list in directory_signatures.items():
        if len(dir_info_list) > 1:  # Only actual duplicates
            items: List[DuplicateItem] = [
                DuplicateItem(path=path, size=size, item_type='directory')
                for path, size in dir_info_list
            ]
            duplicate_sets.append(DuplicateSet(
                hash_signature=content_hash,
                items=items,
                item_type='directory'
            ))
    
    return duplicate_sets


def report_duplicates(duplicate_sets: List[DuplicateSet]) -> None:
    """Report the sets of duplicate items (files or directories)."""
    if not duplicate_sets:
        logging.info("No duplicates found.")
        return
    
    item_type: str = duplicate_sets[0].item_type
    item_type_plural: str = f"{item_type}s"
    
    logging.info(f"\nFound {len(duplicate_sets)} sets of duplicate {item_type_plural}:\n")
    
    total_duplicates: int = 0
    total_wasted_space: int = 0
    
    for i, duplicate_set in enumerate(duplicate_sets, 1):
        total_wasted_space += duplicate_set.wasted_space
        total_duplicates += duplicate_set.duplicate_count
        
        logging.info(f"Duplicate {item_type.title()} Set #{i} (Hash: {duplicate_set.hash_signature[:12]}...):")
        logging.info(f"  Size: {duplicate_set.total_size:,} bytes")
        logging.info(f"  {item_type_plural.title()}: {len(duplicate_set.items)}")
        logging.info(f"  Wasted space: {duplicate_set.wasted_space:,} bytes")
        
        # For directories, show sample contents
        if item_type == 'directory' and duplicate_set.items:
            sample_dir: Path = duplicate_set.items[0].path
            try:
                sample_files: List[str] = [f.name for f in sample_dir.iterdir() if f.is_file()]
                logging.info(f"  Sample contents ({len(sample_files)} files): {', '.join(sample_files[:5])}")
                if len(sample_files) > 5:
                    logging.info(f"    ... and {len(sample_files) - 5} more files")
            except (OSError, PermissionError):
                logging.info("  Could not list sample contents")
        
        logging.info(f"  Duplicate {item_type_plural}:")
        for item in duplicate_set.items:
            logging.info(f"    {item.path}")
        logging.info("")
    
    logging.info(f"{item_type_plural.title()} Duplicates Summary:")
    logging.info(f"  Total duplicate {item_type} sets: {len(duplicate_sets)}")
    logging.info(f"  Total duplicate {item_type_plural}: {total_duplicates}")
    wasted_mb: float = total_wasted_space / (1024 * 1024)
    logging.info(f"  Total wasted space: {total_wasted_space:,} bytes ({wasted_mb:.2f} MB)")


def main() -> None:
    """Main function to orchestrate the duplicate file finding process."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Find duplicate files and directories in a directory tree",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py /path/to/search
  python main.py ~/Documents
  python main.py .  # Search current directory
  python main.py --files-only /path/to/search
  python main.py --dirs-only /path/to/search
        """
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory path to search for duplicates (default: current directory)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--dirs-only',
        action='store_true',
        help='Only find duplicate directories (skip file duplicates)'
    )
    parser.add_argument(
        '--files-only',
        action='store_true',
        help='Only find duplicate files (skip directory duplicates)'
    )
    
    args: argparse.Namespace = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Convert to Path object and resolve
    search_path: Path = Path(args.path).resolve()
    
    if not search_path.exists():
        logging.error(f"Error: Path '{search_path}' does not exist.")
        sys.exit(1)
    
    if not search_path.is_dir():
        logging.error(f"Error: Path '{search_path}' is not a directory.")
        sys.exit(1)
    
    # Validate conflicting options
    if args.dirs_only and args.files_only:
        logging.error("Error: Cannot specify both --dirs-only and --files-only")
        sys.exit(1)
    
    search_files: bool = not args.dirs_only
    search_dirs: bool = not args.files_only
    
    search_type: List[str] = []
    if search_files:
        search_type.append("files")
    if search_dirs:
        search_type.append("directories")
    
    logging.info(f"Searching for duplicate {' and '.join(search_type)} in: {search_path}")
    logging.info("=" * 60)
    
    # File duplicate detection
    if search_files:
        # Step 1: Walk directory tree and group by size in single pass
        logging.info("Step 1: Walking directory tree and grouping by size...")
        size_groups: Dict[int, List[Path]] = walk_directory_tree_and_group_by_size(search_path)
        
        total_files: int = sum(len(paths) for paths in size_groups.values())
        potential_duplicates: int = sum(len(paths) for paths in size_groups.values() if len(paths) > 1)
        size_groups_with_duplicates: int = sum(1 for paths in size_groups.values() if len(paths) > 1)
        
        logging.info(f"Found {total_files} total files.")
        if potential_duplicates > 0:
            logging.info(f"Found {potential_duplicates} files in {size_groups_with_duplicates} size groups that could be duplicates.")
            
            # Step 2: Hash only equal-sized files
            logging.info("\nStep 2: Calculating hashes for potential file duplicates...")
            file_duplicates: List[DuplicateSet] = find_duplicates_by_hash(size_groups)
            
            # Step 3: Report sets of duplicates
            logging.info("\nStep 3: Reporting file duplicates...")
            report_duplicates(file_duplicates)
        else:
            logging.info("No potential file duplicates found (no files with matching sizes).")
    
    # Directory duplicate detection
    if search_dirs:
        step_num: str = "Step 4" if search_files else "Step 1"
        logging.info(f"\n{step_num}: Finding duplicate directories...")
        directory_duplicates: List[DuplicateSet] = find_duplicate_directories(search_path)
        
        step_num = "Step 5" if search_files else "Step 2"
        logging.info(f"\n{step_num}: Reporting directory duplicates...")
        report_duplicates(directory_duplicates)


if __name__ == "__main__":
    main()
