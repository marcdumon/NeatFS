# neat-fs

A Python tool for finding duplicate files and managing your filesystem.

## Description

neat-fs helps you clean up redundant files by detecting duplicates. It groups files by size first, then hashes only potential duplicates for efficiency.

## Installation

```bash
uv sync --group gui
```

## How to Run

Start the GUI:
```bash
streamlit run src/neat_fs/gui/run_gui.py
```

### Manual Operation

1. **Index your filesystem:**
   - Set root directory
   - Add excluded paths (one per line)
   - Set output CSV
   - Click "Run FS Indexer"

2. **Find duplicates:**
   - Set input CSV
   - Set output CSV
   - Click "Run Hasher"

3. **Browse results:**
   - Filter by name, size, date, etc.
   - Select files
   - Delete, move, or rename via actions panel

## CLI Usage

```bash
# Find duplicates in current directory
python main.py

# Find duplicates in specific path
python main.py /path/to/search

# Files only / directories only
python main.py --files-only /path/to/search
python main.py --dirs-only /path/to/search
```

