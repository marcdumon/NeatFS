import os
from pathlib import Path
import sys
import pandas as pd


# sys.path.append("..")
print(sys.path)
from neat_fs import scan_files



df = scan_files.walk_directory_tree(Path('/mnt/Data/obsidian/work_vault'))
print(df)
print('********************')
