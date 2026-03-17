import re
import shutil
import logging
import threading
from pathlib import Path

from openai import OpenAI

from .config import Config
from .prompt import build_system_prompt, get_format_literals

logger = logging.getLogger("norma")


class FileProcessor:
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(
            base_url=config.api_url,
            api_key="lm-studio",  # ignored by both Ollama and LM Studio
        )
        self.system_prompt = build_system_prompt(config.format_string)
        self._format_literals = get_format_literals(config.format_string)

        # Thread-safe counters via lock
        self._lock = threading.Lock()
        self.count_total = 0
        self.count_renamed = 0
        self.count_errors = 0
        self.count_empty = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_and_apply_batch(self, files: list[Path]) -> list[tuple[Path, str | None, bool]]:
        """
        Process a batch of files end-to-end:
          1. Ask LLM for new names
          2. Apply renames (copy to output folder) unless dry_run

        Returns a list of (original_path, new_name, success) tuples.
        """
        if not files:
            return []

        name_map = self._get_names_for_batch(files)
        results = []

        for original in files:
            new_stem = name_map.get(original)
            if new_stem is None:
                self._increment("errors")
                self._increment("total")
                results.append((original, None, False))
                continue

            success, final_name = self._apply_rename(original, new_stem)
            results.append((original, final_name, success))

        return results

    # ------------------------------------------------------------------
    # LLM interaction
    # ------------------------------------------------------------------

    def _get_names_for_batch(self, files: list[Path]) -> dict[Path, str | None]:
        """Send batch to LLM, return {path: new_stem}. Falls back to per-file on failure."""
        stems = [f.stem for f in files]
        numbered_input = "\n".join(f"{i + 1}. {stem}" for i, stem in enumerate(stems))

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": numbered_input},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            raw = response.choices[0].message.content.strip()
            parsed = _parse_numbered_response(raw, len(files))

            if parsed is not None:
                return {files[i]: parsed[i] for i in range(len(files))}

            logger.warning(f"Batch count mismatch — falling back to individual calls for {len(files)} files")
        except Exception as e:
            logger.error(f"Batch LLM call failed: {e} — falling back to individual calls")

        return self._get_names_individually(files)

    def _get_names_individually(self, files: list[Path]) -> dict[Path, str | None]:
        results: dict[Path, str | None] = {}
        for f in files:
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f.stem},
                    ],
                    temperature=self.config.temperature,
                    max_tokens=64,  # single file → short output
                )
                name = response.choices[0].message.content.strip()
                name = re.sub(r'^\d+\.\s*', '', name).strip()
                results[f] = name
            except Exception as e:
                logger.error(f"Individual LLM call failed for {f.name}: {e}")
                results[f] = None
        return results

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _apply_rename(self, original: Path, new_stem: str) -> tuple[bool, str | None]:
        """
        Copy original to output folder with new_stem + original extension.
        Returns (success, final_filename).
        """
        self._increment("total")

        try:
            if original.stat().st_size == 0:
                self._increment("empty")
                logger.info(f"Skipped empty file: {original.name}")
                return False, None
        except OSError:
            self._increment("errors")
            return False, None

        new_stem = _clean_stem(new_stem)
        if not new_stem or not _matches_format(new_stem, self._format_literals):
            self._move_to_errors(original)
            self._increment("errors")
            return False, None

        extension = original.suffix.lower() if original.suffix else ""
        dest_path = self._resolve_dest_path(new_stem + extension)
        final_name = dest_path.name

        if self.config.dry_run:
            self._increment("renamed")
            return True, final_name

        try:
            self.config.output_folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, dest_path)
            self._increment("renamed")
            logger.info(f"{original.name} → {final_name}")
            return True, final_name
        except Exception as e:
            logger.error(f"Copy failed for {original.name}: {e}")
            self._move_to_errors(original)
            self._increment("errors")
            return False, None

    def _resolve_dest_path(self, filename: str) -> Path:
        dest = self.config.output_folder / filename
        if not dest.exists():
            return dest
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 2
        while True:
            candidate = self.config.output_folder / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _move_to_errors(self, original: Path) -> None:
        self.config.errors_folder.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(original, self.config.errors_folder / original.name)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Thread-safe counter helpers
    # ------------------------------------------------------------------

    def _increment(self, counter: str) -> None:
        with self._lock:
            match counter:
                case "total":   self.count_total += 1
                case "renamed": self.count_renamed += 1
                case "errors":  self.count_errors += 1
                case "empty":   self.count_empty += 1

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "total":   self.count_total,
                "renamed": self.count_renamed,
                "errors":  self.count_errors,
                "empty":   self.count_empty,
            }


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _parse_numbered_response(raw: str, expected: int) -> list[str] | None:
    """Parse '1. Name\n2. Name\n...' — returns None if count doesn't match expected."""
    results = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^\d+\.\s*(.+)$', line)
        if m:
            results.append(m.group(1).strip())

    if len(results) != expected:
        return None
    return results


def _clean_stem(stem: str) -> str:
    return (
        stem
        .replace("\n", " ")
        .replace("\\", "")
        .replace("{", "")
        .replace("}", "")
        .strip()
    )


def _matches_format(stem: str, literals: list[str]) -> bool:
    """Return True if stem contains at least one expected literal separator."""
    if not literals:
        return True  # no literals to check (format is just a single {Field})
    return any(lit in stem for lit in literals)
