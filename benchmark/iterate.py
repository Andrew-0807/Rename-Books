"""
Autoresearch-style iteration loop for norma.

Principle (from program.md):
  modify → run → measure → keep if better, discard if worse → repeat
  NEVER STOP until all iterations are complete.

Primary metric:   files_per_min  (higher = better)
Secondary metric: error_rate     (lower = better)

Results logged to benchmark/results.tsv
"""
import sys
import time
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from bench import run_experiment

RESULTS_FILE = Path(__file__).parent / "results.tsv"
ITERATIONS_FILE = Path(__file__).parent / "ITERATIONS.md"


def log(result: dict, status: str, note: str = "") -> None:
    header = not RESULTS_FILE.exists()
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        if header:
            f.write("\t".join([
                "iter", "label", "batch", "workers", "temp", "max_tok", "prompt",
                "files_min", "error_pct", "format_pct", "elapsed_s", "status", "note"
            ]) + "\n")
        f.write("\t".join(str(x) for x in [
            result.get("_iter", "?"),
            result["label"],
            result["batch_size"],
            result["workers"],
            result["temperature"],
            result["max_tokens"],
            result["prompt"],
            result["files_per_min"],
            result["error_rate"],
            result["format_rate"],
            result["elapsed_s"],
            status,
            note,
        ]) + "\n")


def score(result: dict) -> float:
    """Combined score: files/min heavily weighted, penalise error rate."""
    return result["files_per_min"] * (1 - result["error_rate"] / 100)


def print_result(n: int, result: dict, status: str) -> None:
    print(f"\n  Iter {n:2d} [{status:8s}]  {result['label']}")
    print(f"    {result['files_per_min']:6.1f} files/min  |  "
          f"{result['error_rate']:5.1f}% errors  |  "
          f"{result['format_rate']:5.1f}% valid format  |  "
          f"{result['elapsed_s']:.1f}s")


# ---------------------------------------------------------------------------
# Iteration plan
# ---------------------------------------------------------------------------
# Each entry: (label, kwargs_override, description)
ITERATIONS = [
    # 0 — Baseline
    (
        "iter00_baseline",
        dict(batch_size=15, workers=8, temperature=0.1, max_tokens=512, prompt_variant="default"),
        "Baseline: default settings (batch=15, workers=8, temp=0.1, max_tok=512)",
    ),
    # 1 — Double the batch
    (
        "iter01_batch30",
        dict(batch_size=30, workers=8, temperature=0.1, max_tokens=1024, prompt_variant="default"),
        "Hypothesis: larger batch → fewer LLM round-trips → better throughput",
    ),
    # 2 — Batch 50
    (
        "iter02_batch50",
        dict(batch_size=50, workers=8, temperature=0.1, max_tokens=1600, prompt_variant="default"),
        "Push batch to 50; max_tokens scaled to match expected output size",
    ),
    # 3 — Batch 100
    (
        "iter03_batch100",
        dict(batch_size=100, workers=8, temperature=0.1, max_tokens=3000, prompt_variant="default"),
        "Maximum batch — amortise system prompt cost over 100 filenames",
    ),
    # 4 — Short prompt
    (
        "iter04_short_prompt",
        dict(batch_size=None, workers=8, temperature=0.1, max_tokens=None, prompt_variant="short"),
        "Shorter system prompt: fewer input tokens per call",
    ),
    # 5 — Short prompt + best batch
    (
        "iter05_short_best_batch",
        dict(batch_size=None, workers=8, temperature=0.1, max_tokens=None, prompt_variant="short"),
        "Short prompt combined with best batch size from iters 1-3",
    ),
    # 6 — Workers = 4 (single GPU serialises anyway)
    (
        "iter06_workers4",
        dict(batch_size=None, workers=4, temperature=0.1, max_tokens=None, prompt_variant="short"),
        "Reduce workers: GPU handles one request at a time, less thread overhead",
    ),
    # 7 — Workers = 16
    (
        "iter07_workers16",
        dict(batch_size=None, workers=16, temperature=0.1, max_tokens=None, prompt_variant="short"),
        "Increase workers: test whether more parallelism saturates the GPU queue",
    ),
    # 8 — Lower max_tokens aggressively (each filename → ~10 tokens output)
    (
        "iter08_tight_tokens",
        dict(batch_size=None, workers=None, temperature=0.1, max_tokens=None, prompt_variant="short"),
        "Tight max_tokens = batch_size * 20 — prevent runaway responses",
    ),
    # 9 — Combined champion
    (
        "iter09_champion",
        dict(batch_size=None, workers=None, temperature=0.05, max_tokens=None, prompt_variant="short"),
        "All best settings + temperature=0.05 (most deterministic)",
    ),
]


def main():
    print("\n" + "="*60)
    print("  norma autoresearch iteration loop")
    print("  Primary metric: files/min | Secondary: error_rate")
    print("="*60)

    best_result  = None
    best_score   = -1
    best_batch   = 15
    best_workers = 8
    best_maxtok  = 512

    iteration_notes = []

    for n, (label, kwargs, description) in enumerate(ITERATIONS):
        print(f"\n{'─'*60}")
        print(f"  Iteration {n}: {label}")
        print(f"  {description}")

        # Fill in None values with current best
        resolved = {
            "batch_size":    kwargs.get("batch_size")    or best_batch,
            "workers":       kwargs.get("workers")       or best_workers,
            "temperature":   kwargs.get("temperature",   0.1),
            "max_tokens":    kwargs.get("max_tokens")    or best_maxtok,
            "prompt_variant":kwargs.get("prompt_variant","default"),
            "label":         label,
        }

        # Tight max_tokens for iter08: batch * 20
        if label == "iter08_tight_tokens":
            resolved["max_tokens"] = resolved["batch_size"] * 20

        # Champion: apply all best
        if label == "iter09_champion":
            resolved["max_tokens"] = resolved["batch_size"] * 20

        print(f"  Config: batch={resolved['batch_size']} workers={resolved['workers']} "
              f"temp={resolved['temperature']} max_tok={resolved['max_tokens']} "
              f"prompt={resolved['prompt_variant']}")

        result = run_experiment(**resolved)
        result["_iter"] = n
        s = score(result)

        if best_result is None or s > best_score:
            status = "KEEP ✓"
            # Update best params
            best_score   = s
            best_result  = result
            best_batch   = result["batch_size"]
            best_workers = result["workers"]
            best_maxtok  = result["max_tokens"]
        else:
            status = "DISCARD"

        print_result(n, result, status)
        log(result, status, description)

        note = (
            f"Iter {n}: {label} | {result['files_per_min']} f/m | "
            f"{result['error_rate']}% err | {status}"
        )
        iteration_notes.append((n, label, result, status, description))

        # Never stop — autoresearch principle
        time.sleep(0.5)

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print("\n" + "="*60)
    print("  FINAL RESULTS")
    print("="*60)
    print(f"\n  {'Iter':5} {'Label':35} {'f/min':>8} {'err%':>6} {'status'}")
    print(f"  {'─'*5} {'─'*35} {'─'*8} {'─'*6} {'─'*8}")
    for n, label, res, status, _ in iteration_notes:
        marker = " ← best" if res is best_result else ""
        print(f"  {n:5} {label:35} {res['files_per_min']:8.1f} "
              f"{res['error_rate']:6.1f} {status}{marker}")

    print(f"\n  Best config:")
    print(f"    batch_size   = {best_result['batch_size']}")
    print(f"    workers      = {best_result['workers']}")
    print(f"    temperature  = {best_result['temperature']}")
    print(f"    max_tokens   = {best_result['max_tokens']}")
    print(f"    prompt       = {best_result['prompt']}")
    print(f"    → {best_result['files_per_min']} files/min, {best_result['error_rate']}% error rate")

    _write_iterations_md(iteration_notes, best_result)
    print(f"\n  Results saved to: {RESULTS_FILE}")
    print(f"  Full log:         {ITERATIONS_FILE}")


def _write_iterations_md(notes, best):
    lines = [
        "# norma — Iteration Results\n",
        "Autoresearch-style optimization. Primary metric: files/min.\n",
        f"**Best config:** batch={best['batch_size']}, workers={best['workers']}, "
        f"temp={best['temperature']}, max_tokens={best['max_tokens']}, "
        f"prompt={best['prompt']}\n",
        f"**Best throughput:** {best['files_per_min']} files/min, "
        f"{best['error_rate']}% error rate\n\n",
        "| Iter | Label | files/min | err% | format% | elapsed | Status | Description |\n",
        "|------|-------|-----------|------|---------|---------|--------|-------------|\n",
    ]
    for n, label, res, status, desc in notes:
        lines.append(
            f"| {n} | {label} | {res['files_per_min']} | {res['error_rate']} | "
            f"{res['format_rate']} | {res['elapsed_s']}s | {status} | {desc} |\n"
        )
    ITERATIONS_FILE.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
