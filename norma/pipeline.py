import math
import shutil
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from .config import Config
from .processor import FileProcessor
from .dedup import remove_duplicates

logger = logging.getLogger("norma")

# Auto-split threshold: if a flat input folder has more files than this, split first
_SPLIT_THRESHOLD = 3000


def run_pipeline(
    config: Config,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict:
    """
    Run the full rename pipeline.

    Steps:
      1. Auto-split if the input folder is flat with > SPLIT_THRESHOLD files
      2. Collect all files to process
      3. Process in batches using ThreadPoolExecutor
      4. Deduplicate processed originals
      5. Write processed.log
      6. Return stats dict

    progress_callback(completed, total) is called after each batch completes.
    """
    config.output_folder.mkdir(parents=True, exist_ok=True)

    # Step 1: auto-split large flat folders
    _auto_split_if_needed(config.input_folder)

    # Step 2: collect files
    files = _collect_files(config.input_folder)
    total = len(files)

    if total == 0:
        return {"total": 0, "renamed": 0, "errors": 0, "empty": 0, "deduped": 0}

    # Step 3: process in batches
    processor = FileProcessor(config)
    batches = _chunk(files, config.batch_size)
    completed = 0

    # For dry-run, collect preview rows
    preview_rows: list[tuple[str, str]] = []

    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        futures = {
            executor.submit(processor.process_and_apply_batch, batch): batch
            for batch in batches
        }
        for future in as_completed(futures):
            try:
                batch_results = future.result()
                completed += len(futures[future])
                if config.dry_run:
                    for original, new_name, _ in batch_results:
                        if new_name:
                            preview_rows.append((original.name, new_name))
                if progress_callback:
                    progress_callback(completed, total)
            except Exception as e:
                logger.error(f"Batch processing error: {e}")

    # Step 4: dedup (skip in dry-run — nothing was copied)
    deduped = 0
    if not config.dry_run:
        processed_mirror = config.output_folder.parent / "Processed" / config.input_folder.name
        if processed_mirror.exists():
            deduped = remove_duplicates(config.input_folder, processed_mirror, config.workers)

    # Step 5: write log
    if not config.dry_run:
        _write_log(config, processor.stats)

    stats = processor.stats
    stats["deduped"] = deduped
    if config.dry_run:
        stats["preview"] = preview_rows

    return stats


# ------------------------------------------------------------------
# Auto-split
# ------------------------------------------------------------------

def _auto_split_if_needed(folder: Path) -> None:
    """If folder contains > _SPLIT_THRESHOLD direct files, split into subfolders."""
    flat_files = [p for p in folder.iterdir() if p.is_file()]
    if len(flat_files) <= _SPLIT_THRESHOLD:
        return

    n_folders = math.ceil(len(flat_files) / _SPLIT_THRESHOLD)
    folder_names = [folder / f"Folder_{i + 1:03d}" for i in range(n_folders)]
    for d in folder_names:
        d.mkdir(exist_ok=True)

    for i, file in enumerate(flat_files):
        dest_dir = folder_names[i % n_folders]
        shutil.move(str(file), dest_dir / file.name)

    logger.info(f"Auto-split {len(flat_files)} files into {n_folders} subfolders in {folder.name}")


# ------------------------------------------------------------------
# File collection
# ------------------------------------------------------------------

def _collect_files(folder: Path) -> list[Path]:
    """Collect all files recursively, excluding hidden files and system files."""
    files = []
    for p in folder.rglob("*"):
        if p.is_file() and not p.name.startswith(".") and not p.name.startswith("~"):
            files.append(p)
    return files


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _chunk(lst: list, size: int) -> list[list]:
    return [lst[i: i + size] for i in range(0, len(lst), size)]


def _write_log(config: Config, stats: dict) -> None:
    try:
        config.processed_log.write_text(
            f"renamed: {stats['renamed']}\n"
            f"errors:  {stats['errors']}\n"
            f"empty:   {stats['empty']}\n"
            f"total:   {stats['total']}\n",
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning(f"Could not write processed.log: {e}")
