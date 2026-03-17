"""
Single-experiment benchmark runner.
Adapted from autoresearch's train.py philosophy:
  - fixed input corpus
  - measure one primary metric (files/min)
  - secondary metric (error_rate %)
  - returns dict of results
"""
import shutil
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from norma.config import Config
from norma.pipeline import run_pipeline

FILES_DIR  = Path(__file__).parent / "files"
OUTPUT_DIR = Path(__file__).parent / "output"


def run_experiment(
    batch_size: int    = 15,
    workers: int       = 8,
    temperature: float = 0.1,
    max_tokens: int    = 512,
    prompt_variant: str = "default",   # "default" | "short"
    label: str         = "",
) -> dict:
    """Run one experiment, return metrics dict."""

    # Apply prompt variant before building config
    if prompt_variant == "short":
        _patch_short_prompt()
    else:
        _restore_default_prompt()

    # Clean output dir
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    config = Config(
        input_folder  = FILES_DIR,
        output_folder = OUTPUT_DIR,
        format_string = "{Author} - {Title}",
        model         = "local-model",
        workers       = workers,
        batch_size    = batch_size,
        dry_run       = False,
        api_url       = "http://localhost:1234/v1",
        temperature   = temperature,
        max_tokens    = max_tokens,
    )

    t0    = time.monotonic()
    stats = run_pipeline(config)
    elapsed = time.monotonic() - t0

    total   = stats.get("total",   0)
    renamed = stats.get("renamed", 0)
    errors  = stats.get("errors",  0)
    empty   = stats.get("empty",   0)

    files_per_min = round(total / elapsed * 60, 1) if elapsed > 0 else 0
    error_rate    = round(errors / total * 100, 1)  if total  > 0 else 0
    valid_rate    = round(renamed / total * 100, 1) if total  > 0 else 0

    # Count output files that contain " - " (format validity)
    out_files = list(OUTPUT_DIR.rglob("*"))
    valid_format = sum(1 for f in out_files if f.is_file() and " - " in f.stem)
    format_rate  = round(valid_format / renamed * 100, 1) if renamed > 0 else 0

    return {
        "label":         label or f"b{batch_size}_w{workers}_t{temperature}",
        "batch_size":    batch_size,
        "workers":       workers,
        "temperature":   temperature,
        "max_tokens":    max_tokens,
        "prompt":        prompt_variant,
        "elapsed_s":     round(elapsed, 2),
        "total":         total,
        "renamed":       renamed,
        "errors":        errors,
        "files_per_min": files_per_min,
        "error_rate":    error_rate,
        "valid_rate":    valid_rate,
        "format_rate":   format_rate,
    }


# ---------------------------------------------------------------------------
# Prompt patching — swap in a shorter system prompt for iteration testing
# ---------------------------------------------------------------------------

_SHORT_PROMPT = None
_DEFAULT_PROMPT_FN = None

def _patch_short_prompt():
    import norma.prompt as _pm
    global _DEFAULT_PROMPT_FN
    if _DEFAULT_PROMPT_FN is None:
        _DEFAULT_PROMPT_FN = _pm.build_system_prompt

    def _short(format_string: str) -> str:
        from norma.prompt import parse_fields
        fields = parse_fields(format_string)
        field_block = ", ".join(f"{{{f}}}" for f in fields)
        return (
            f"Format each filename as: {format_string}\n"
            f"Fields: {field_block}\n"
            "Rules: output only the formatted name, preserve language, "
            "use Unknown for missing fields, numbered list in/out.\n"
            "Example: harry_potter_jk_rowling → J.K. Rowling - Harry Potter"
        )
    _pm.build_system_prompt = _short

def _restore_default_prompt():
    import norma.prompt as _pm
    global _DEFAULT_PROMPT_FN
    if _DEFAULT_PROMPT_FN is not None:
        _pm.build_system_prompt = _DEFAULT_PROMPT_FN


if __name__ == "__main__":
    # Quick smoke-test of a single experiment
    result = run_experiment(batch_size=15, workers=8, label="smoke_test")
    for k, v in result.items():
        print(f"  {k:20s} {v}")
