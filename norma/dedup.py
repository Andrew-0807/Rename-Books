from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger("norma")


def remove_duplicates(source_folder: Path, processed_folder: Path, workers: int = 8) -> int:
    """
    Delete files from source_folder that already exist (by filename) in processed_folder.
    Operates recursively on matching subfolders. Returns the count of deleted files.
    """
    if not source_folder.exists() or not processed_folder.exists():
        return 0

    source_subs = {p.name: p for p in source_folder.iterdir() if p.is_dir()}
    processed_subs = {p.name: p for p in processed_folder.iterdir() if p.is_dir()}
    common = set(source_subs) & set(processed_subs)

    total_deleted = 0
    for subfolder_name in common:
        deleted = _dedup_subfolder(
            source_subs[subfolder_name],
            processed_subs[subfolder_name],
            workers,
        )
        total_deleted += deleted
        if deleted:
            logger.info(f"Removed {deleted} duplicates from {subfolder_name}")

    return total_deleted


def _dedup_subfolder(src: Path, processed: Path, workers: int) -> int:
    src_files = {f.name for f in src.iterdir() if f.is_file()}
    proc_files = {f.name for f in processed.iterdir() if f.is_file()}
    duplicates = [src / name for name in src_files & proc_files]

    if not duplicates:
        return 0

    deleted = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_delete, f): f for f in duplicates}
        for future in as_completed(futures):
            if future.result():
                deleted += 1

    return deleted


def _delete(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except Exception as e:
        logger.error(f"Could not delete {path.name}: {e}")
        return False
