# Duplicate Files Finder

A Python script that efficiently finds duplicate files and directories in a directory tree.

## Workflow

### For Files:
1. **Walks directory tree and groups by size** - Single pass: scan files and group by size simultaneously
2. **Hashes only equal-sized files** - Calculates MD5 hashes only for files that could be duplicates
3. **Reports sets of duplicates** - Shows organized groups of duplicate files with size and space information

### For Directories:
1. **Scans all directories** - Identifies directories that contain files
2. **Analyzes directory contents** - Creates signatures based on file names, sizes, and hashes
3. **Compares directory signatures** - Groups directories with identical content
4. **Reports duplicate directories** - Shows directories that contain exactly the same files

## Usage

```bash
# Search current directory for both files and directories
python main.py

# Search specific directory
python main.py /path/to/search

# Search home Documents folder
python main.py ~/Documents

# Only find duplicate files (skip directories)
python main.py --files-only /path/to/search

# Only find duplicate directories (skip files)
python main.py --dirs-only /path/to/search

# Show help
python main.py --help
```

## Features

- **Efficient processing**: Only hashes files with matching sizes for file duplicates
- **Single-pass optimization**: Groups files by size during directory traversal to eliminate redundant loops and filesystem calls
- **Directory duplicate detection**: Finds directories with identical contents
- **Flexible search options**: Search for files only, directories only, or both
- **Detailed reporting**: Shows file/directory paths, sizes, and wasted space
- **Error handling**: Gracefully handles permission errors and inaccessible files
- **Progress feedback**: Shows progress through each step of the process
- **Summary statistics**: Reports total duplicates and space savings potential

## Requirements

- Python 3.13+
- Standard library only (no external dependencies required)

## Example Output

```
Searching for duplicate files in: /home/user/Documents
============================================================
Step 1: Walking directory tree...
Found 1,234 files.

Step 2: Grouping files by size...
Found 89 files in 12 size groups that could be duplicates.

Step 3: Calculating hashes for potential duplicates...
Hashing 4 files of size 2048 bytes...
Hashing 3 files of size 1024000 bytes...

Step 4: Reporting duplicates...

Found 2 sets of duplicate files:

Duplicate Set #1 (Hash: a1b2c3d4e5f6...):
  Size: 2,048 bytes
  Files: 2
  Wasted space: 2,048 bytes
    /home/user/Documents/file1.txt
    /home/user/Documents/backup/file1.txt

Summary:
  Total duplicate sets: 2
  Total duplicate files: 3
  Total wasted space: 1,050,048 bytes (1.00 MB)

Step 5: Finding duplicate directories...

Step 6: Reporting directory duplicates...

Found 1 sets of duplicate directories:

Duplicate Directory Set #1 (Content Hash: abc123def456...):
  Directory size: 512,000 bytes
  Directories: 3
  Wasted space: 1,024,000 bytes
  Sample contents (4 files): image1.jpg, image2.jpg, config.txt, data.csv
  Duplicate directories:
    /home/user/Documents/photos/vacation
    /home/user/Documents/backup/vacation
    /home/user/Documents/archive/vacation-copy

Directory Duplicates Summary:
  Total duplicate directory sets: 1
  Total duplicate directories: 2
  Total wasted space: 1,024,000 bytes (0.98 MB)
```