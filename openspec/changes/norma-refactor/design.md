# Design: norma refactor

## Package name and structure

The project is renamed to **norma**. Entry point is `norma` (via `pyproject.toml` scripts).

```
norma/
├── norma/
│   ├── __init__.py
│   ├── cli.py          # typer CLI — all commands and flags
│   ├── pipeline.py     # orchestrates: split → process → dedup → report
│   ├── processor.py    # FileProcessor class (LLM calls, file ops)
│   ├── prompt.py       # dynamic prompt builder from user's format string
│   ├── dedup.py        # duplicate detection and removal
│   └── config.py       # Config dataclass — centralizes all runtime settings
├── pyproject.toml
├── README.md
└── openspec/
```

---

## CLI design (typer)

### Primary command

```
norma run <input_folder> [options]
```

| Flag | Default | Description |
|---|---|---|
| `--format` | `"{Author} - {Title}"` | Output naming template with `{Field}` placeholders |
| `--output` | `./norma-output` | Destination folder for renamed files |
| `--model` | `qwen2.5:3b` | Ollama model to use |
| `--workers` | `8` | Concurrent threads |
| `--batch-size` | `15` | Files per LLM call (batching) |
| `--dry-run` | `false` | Preview renames without moving files |
| `--ollama-url` | `http://localhost:11434` | Ollama base URL |

### Secondary commands

```
norma status          # check Ollama connectivity and available models
norma retry <folder>  # re-process files that failed on a previous run
```

### Example invocations

```bash
# Books (original use case)
norma run ./my-ebooks --format "{Author} - {Title}"

# Invoices
norma run ./invoices --format "{Client} / Invoice / {Date}"

# Research papers
norma run ./papers --format "{Author} ({Year}) - {Title}"

# Preview before committing
norma run ./messy-files --format "{Author} - {Title}" --dry-run

# Use a bigger model for better quality
norma run ./books --model qwen2.5:7b
```

---

## The critical performance design: batching

**This is the most important architectural decision.**

The original code: 1 LLM API call per file, 8 concurrent threads.
The bottleneck: request overhead per call (model setup, HTTP round-trip) dominates for short prompts.

**norma's approach: batch multiple filenames per LLM call.**

```
Old:  [file1] → API  (1s)
      [file2] → API  (1s)
      ...
      8 concurrent × 1 file each = 8 files/second (theoretical)

New:  [file1, file2, ..., file15] → API  (1.5s)
      [file16, ..., file30]       → API  (1.5s)
      ...
      8 concurrent × 15 files each = 80 files/second (theoretical)
```

Batching 15 files per call with 8 workers yields ~10x throughput with the same or better model quality.

### Batch prompt structure

The LLM receives a numbered list of filenames and returns a numbered list of formatted names:

```
Input to LLM:
  Format each filename as: {Author} - {Title}

  1. harry_potter_jk_rowling.epub
  2. 4.LISA_KLEYPAS_Scandal_in_primavara.pdf
  3. INV-2024-ACME-000432.pdf
  ...

Expected output (strict):
  1. J.K. Rowling - Harry Potter
  2. Lisa Kleypas - Scandal in primavara
  3. Anonymous - INV-2024-ACME-000432
  ...
```

Response parsing: extract numbered lines, validate count matches input batch size.
If count mismatch: fall back to processing each file individually.

---

## Prompt design (prompt.py)

`prompt.py` builds the system prompt dynamically from the user's `--format` string.

### Template parsing

```
"{Author} - {Title}"
→ fields: ["Author", "Title"]
→ tells LLM: "extract Author and Title from each filename"
```

The system prompt is assembled as:
1. Instruction: output format, numbered list rules
2. Field definitions: what each `{Field}` means (derived from field name)
3. Language rule: preserve the input language, do not translate
4. Fallback rule: if a field is unknown, use `Unknown`
5. Few-shot examples: 3–5 examples generated to match the requested format

Field semantics are inferred from field names:
- `Author`, `Writer`, `Creator` → "the person who created the work"
- `Title`, `Name` → "the name of the work"
- `Date`, `Year` → "a date or year found in the filename"
- `Client`, `Company` → "an organization name"
- Unknown fields → passed as-is to the LLM with a generic description

---

## Config dataclass (config.py)

All runtime settings flow through a single `Config` object, eliminating scattered constants:

```python
@dataclass
class Config:
    input_folder: Path
    output_folder: Path
    format_string: str          # e.g. "{Author} - {Title}"
    model: str                  # e.g. "qwen2.5:3b"
    workers: int                # thread count
    batch_size: int             # files per LLM call
    dry_run: bool
    ollama_url: str
    errors_folder: Path         # derived: output_folder / "_errors"
    processed_log: Path         # derived: output_folder / "processed.log"
```

---

## File flow

```
input_folder/
  ├── Folder_001/   (auto-split if >3000 files)
  │   ├── file1.epub
  │   └── file2.pdf
  └── Folder_002/
      └── file3.epub

                    ┌─────────────────────┐
                    │  pipeline.py        │
                    │                     │
                    │  1. auto-split      │  (if flat folder > 3000 files)
                    │  2. process batches │  (8 workers × 15 files/batch)
                    │  3. dedup           │  (remove already-processed originals)
                    │  4. report          │  (rich summary table)
                    └─────────────────────┘

output_folder/
  ├── J.K. Rowling - Harry Potter.epub
  ├── Lisa Kleypas - Scandal in primavara.pdf
  ├── _errors/      (files that could not be formatted)
  └── processed.log
```

---

## Error handling

| Situation | Behaviour |
|---|---|
| LLM returns wrong batch count | Retry files individually |
| Renamed file already exists in output | Append `(2)`, `(3)` etc. |
| Empty file (0 bytes) | Skip and log, do not copy |
| Ollama not running | Fail fast with clear message + `norma status` hint |
| File has no extension | Treat basename as full name |

---

## Model recommendation

Default: **`qwen2.5:3b`**

Rationale: same size class as `gemma2:2b` (~2GB), dramatically better at following structured output instructions, excellent multilingual performance. Users on powerful machines can pass `--model qwen2.5:7b` for better quality.

`qwen2.5:3b` → `ollama pull qwen2.5:3b` (required setup, documented in README)

---

## Output UX (rich)

During processing, norma shows a live display:

```
 norma  Processing ./my-ebooks → ./norma-output

  Model   qwen2.5:3b         Format   {Author} - {Title}
  Workers 8                  Batch    15 files/call

 ████████████████████░░░░░  68%  6,821 / 10,000

  ✓ renamed    6,634     (97.2%)
  ✗ errors       187      (2.8%)
  ○ skipped        0

  Speed   ~420 files/min    ETA   ~15s
```

Final summary after completion prints a compact table of counts and any error files.

---

## What is removed

| Old file | Fate |
|---|---|
| `RenameBooks.py` | → `norma/cli.py` + `norma/pipeline.py` |
| `Processor.py` | → `norma/processor.py` (cleaned up, no hardcoded paths) |
| `DelDupFiles.py` | → `norma/dedup.py` |
| `Split Batches.py` | → inlined into `pipeline.py`, runs automatically |
| `RemoveErrors.py` | → inlined into `pipeline.py` as post-pass validation |
| `RemoveAlready done.py` | → removed (one-off utility, not needed) |
| `rmStartSpace.py` | → removed (one-off utility, not needed) |
| `RenameByParentFolder .py` | → removed (one-off utility, not needed) |
| `processed_files.log` | → `norma-output/processed.log` (per-run, not repo-tracked) |
