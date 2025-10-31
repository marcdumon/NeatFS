from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


@dataclass
class OperationResult:
    path: Path
    success: bool
    message: str = ""


def _as_paths(paths: Iterable[Path | str]) -> List[Path]:
    return [p if isinstance(p, Path) else Path(p) for p in paths]


def validate_existing_files(paths: Iterable[Path | str]) -> Tuple[List[Path], List[OperationResult]]:
    valid: List[Path] = []
    errors: List[OperationResult] = []
    for p in _as_paths(paths):
        if not p.exists():
            errors.append(OperationResult(p, False, "Path does not exist"))
            continue
        if p.is_dir():
            errors.append(OperationResult(p, False, "Path is a directory, expected file"))
            continue
        valid.append(p)
    return valid, errors


def delete_files(paths: Iterable[Path | str], *, dry_run: bool = True, follow_symlinks: bool = False) -> List[OperationResult]:
    import os

    results: List[OperationResult] = []
    files, errs = validate_existing_files(paths)
    results.extend(errs)
    for p in files:
        try:
            # Avoid following symlinks unless explicitly requested
            if p.is_symlink() and not follow_symlinks:
                if not dry_run:
                    p.unlink()
                results.append(OperationResult(p, True, "Symlink removed"))
                continue
            if not dry_run:
                os.remove(p)
            results.append(OperationResult(p, True, "Deleted" if not p.is_symlink() else "Symlink deleted"))
        except Exception as e:  # noqa: BLE001
            results.append(OperationResult(p, False, f"Error: {e}"))
    return results


def move_files(paths: Iterable[Path | str], destination_dir: Path | str, *, dry_run: bool = True, overwrite: bool = False) -> List[OperationResult]:
    import shutil

    dest_dir = destination_dir if isinstance(destination_dir, Path) else Path(destination_dir)
    results: List[OperationResult] = []
    files, errs = validate_existing_files(paths)
    results.extend(errs)
    if not dest_dir.exists():
        if dry_run:
            # Pretend it will be created
            pass
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
    for p in files:
        target = dest_dir / p.name
        if target.exists() and not overwrite:
            results.append(OperationResult(p, False, f"Target exists: {target}"))
            continue
        try:
            if not dry_run:
                # If overwriting, remove target first to avoid cross-device errors
                if target.exists() and overwrite:
                    if target.is_file() or target.is_symlink():
                        target.unlink()
                shutil.move(str(p), str(target))
            results.append(OperationResult(p, True, f"Move -> {target}"))
        except Exception as e:  # noqa: BLE001
            results.append(OperationResult(p, False, f"Error: {e}"))
    return results


def rename_file(path: Path | str, new_name: str, *, dry_run: bool = True, overwrite: bool = False) -> OperationResult:
    p = path if isinstance(path, Path) else Path(path)
    if not p.exists() or p.is_dir():
        return OperationResult(p, False, "Path does not exist or is a directory")
    target = p.with_name(new_name)
    if target.exists() and not overwrite:
        return OperationResult(p, False, f"Target exists: {target}")
    try:
        if not dry_run:
            if target.exists() and overwrite:
                if target.is_file() or target.is_symlink():
                    target.unlink()
            p.rename(target)
        return OperationResult(p, True, f"Rename -> {target}")
    except Exception as e:  # noqa: BLE001
        return OperationResult(p, False, f"Error: {e}")


