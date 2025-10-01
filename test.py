from main import walk_directory_tree_and_group_by_size
from pathlib import Path


x = walk_directory_tree_and_group_by_size(Path('/mnt/Data/obsidian/work_vault'))
print(x)

