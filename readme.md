# neat-fs

A Python tool for finding duplicate files and directories with optimized performance.

## Features

- **Efficient duplicate detection**: Groups files by size first, then hashes only potential duplicates
- **Directory comparison**: Finds directories with identical contents
- **Performance optimized**: Uses optimal chunk sizes for maximum throughput
- **Flexible search**: Find files, directories, or both

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Find duplicates in current directory
python main.py

# Find duplicates in specific directory
python main.py /path/to/search

# Files only
python main.py --files-only /path/to/search

# Directories only  
python main.py --dirs-only /path/to/search
```

## Performance Results

Based on hash speed testing with files from 1KB to 20GB:

### File Size vs Performance
- **Small files** (1KB-100KB): 1.7-9.7 MB/s
- **Medium files** (1MB-10MB): 198-315 MB/s  
- **Large files** (100MB-500MB): 187-342 MB/s
- **Very large files** (1GB-20GB): 137-555 MB/s

### Optimal Chunk Size
Testing shows **1MB chunks** provide best performance for most file sizes, achieving up to 555 MB/s throughput.

### Performance Charts

![Hash Speed Test Results](data/tests/01_hash_speed_test/01_hash_speed_plot.png)
*File size vs hash time and throughput analysis*

![Chunk Size Analysis](data/tests/01_hash_speed_test/01_chunk_size_plot.png)
*Optimal chunk size performance comparison*

### Key Insights
1. **Size grouping is crucial**: Only hash files with matching sizes
2. **Chunk size matters**: 1MB chunks optimize I/O performance
3. **Large files scale well**: Performance remains consistent up to 20GB files
4. **Memory efficient**: Chunked reading prevents memory issues

### Detailed Analysis
See the complete performance analysis in [`notebooks/hash_speed_test.ipynb`](notebooks/hash_speed_test.ipynb) including:
- File size vs hash time relationships
- Chunk size optimization testing
- Throughput analysis with error bars
- Performance recommendations

## Project Structure

```
src/neat_fs/
├── file_scanner.py      # Directory scanning
├── duplicate_finder.py  # Duplicate detection
└── utils.py            # Shared utilities
```

## Requirements

- Python 3.8+
- pandas (for data processing)
- matplotlib (optional, for notebooks)