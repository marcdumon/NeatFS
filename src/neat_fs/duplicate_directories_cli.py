"""CLI interface for browsing and managing duplicate directories."""

import pandas as pd
import subprocess
from pathlib import Path


def open_in_dolphin_split(dir1: str, dir2: str) -> None:
    """Open two directories in Dolphin split view."""
    # Suppress Qt/KDE debug messages by redirecting stderr
    subprocess.Popen(
        ['dolphin', '--split', dir1, dir2],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def display_duplicate_groups(duplicates_df: pd.DataFrame) -> dict:
    """Display duplicate directory groups and return grouped data."""
    groups = {}
    
    for group_id in sorted(duplicates_df['group_id'].unique()):
        group_data = duplicates_df[duplicates_df['group_id'] == group_id].sort_values('directory')
        groups[group_id] = group_data
        
        file_count = group_data.iloc[0]['file_count']
        total_size_mb = group_data.iloc[0]['total_size'] / 1024 / 1024
        
        print(f"\n{'='*80}")
        print(f"Group {group_id} ({file_count} files, {total_size_mb:.2f} MB) - {len(group_data)} duplicate directories:")
        print(f"{'='*80}")
        
        for idx, (_, row) in enumerate(group_data.iterrows(), 1):
            print(f"  {idx}. {row['directory']}")
    
    return groups


def run_cli(csv_file: str = './data/duplicate_directories.csv') -> None:
    """Run the interactive CLI for browsing duplicate directories."""
    
    # Load duplicate directories
    if not Path(csv_file).exists():
        print(f"Error: {csv_file} not found. Please run duplicate_directories_finder.py first.")
        return
    
    duplicates_df = pd.read_csv(csv_file)
    
    if len(duplicates_df) == 0:
        print("No duplicate directories found.")
        return
    
    print(f"\n{'#'*80}")
    print(f"# DUPLICATE DIRECTORY BROWSER")
    print(f"# Found {duplicates_df['group_id'].nunique()} groups with {len(duplicates_df)} duplicate directories")
    print(f"{'#'*80}")
    
    groups = display_duplicate_groups(duplicates_df)
    
    # Main interaction loop
    while True:
        print(f"\n{'='*80}")
        print("Commands:")
        print("  s <group_id>        - Open directories in split view (e.g., 's 1')")
        print("  s <group_id> <n> <m> - Open specific directories in split view (e.g., 's 1 1 2')")
        print("  l                   - List all groups again")
        print("  q                   - Quit")
        print(f"{'='*80}")
        
        try:
            command = input("\nEnter command: ").strip().lower()
            
            if not command:
                continue
            
            if command == 'q':
                print("Goodbye!")
                break
            
            if command == 'l':
                groups = display_duplicate_groups(duplicates_df)
                continue
            
            if command.startswith('s '):
                parts = command.split()
                
                if len(parts) < 2:
                    print("Error: Please specify a group_id (e.g., 's 1')")
                    continue
                
                try:
                    group_id = int(parts[1])
                except ValueError:
                    print("Error: Invalid group_id. Must be a number.")
                    continue
                
                if group_id not in groups:
                    print(f"Error: Group {group_id} not found.")
                    continue
                
                group_data = groups[group_id]
                group_list = group_data['directory'].tolist()
                
                # If specific directories specified
                if len(parts) == 4:
                    try:
                        idx1 = int(parts[2]) - 1
                        idx2 = int(parts[3]) - 1
                        
                        if idx1 < 0 or idx1 >= len(group_list) or idx2 < 0 or idx2 >= len(group_list):
                            print(f"Error: Directory indices must be between 1 and {len(group_list)}")
                            continue
                        
                        dir1 = group_list[idx1]
                        dir2 = group_list[idx2]
                        
                    except ValueError:
                        print("Error: Invalid directory indices. Must be numbers.")
                        continue
                
                # Otherwise, open first two directories
                elif len(parts) == 2:
                    if len(group_list) < 2:
                        print("Error: Group must have at least 2 directories.")
                        continue
                    
                    dir1 = group_list[0]
                    dir2 = group_list[1]
                
                else:
                    print("Error: Invalid command format. Use 's <group_id>' or 's <group_id> <n> <m>'")
                    continue
                
                print(f"\nOpening in split view:")
                print(f"  Left:  {dir1}")
                print(f"  Right: {dir2}")
                
                open_in_dolphin_split(dir1, dir2)
                
                continue
            
            print("Error: Unknown command. Use 's', 'l', or 'q'.")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break


if __name__ == '__main__':
    run_cli()

