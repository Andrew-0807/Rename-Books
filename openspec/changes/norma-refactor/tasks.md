# Tasks: norma refactor

## Phase 1 — Package scaffold

- [x] **1.1** Create `pyproject.toml` with project metadata, dependencies (`typer`, `rich`, `openai`), and `[project.scripts]` entry point `norma = "norma.cli:app"`
- [x] **1.2** Create `norma/` package directory with `__init__.py`
- [x] **1.3** Create `norma/config.py` — `Config` dataclass with all runtime settings (no defaults from environment, all passed explicitly from CLI)

## Phase 2 — Core logic

- [x] **2.1** Create `norma/prompt.py` — `build_system_prompt(format_string)` that parses `{Field}` tokens, infers field semantics, and assembles the full system prompt with numbered-list batch instructions and few-shot examples matching the requested format
- [x] **2.2** Create `norma/processor.py` — `FileProcessor` class:
  - Accepts a `Config` object (no internal path assumptions)
  - `process_batch(files: list[Path]) -> dict[Path, str]` — sends batch of filenames to LLM, returns mapping of original → new name
  - `copy_and_rename(original, new_name)` — copies to output folder, handles name collisions with `(2)`, `(3)` suffix, skips empty files
  - Parse numbered list response; fall back to per-file calls if count mismatches
- [x] **2.3** Create `norma/dedup.py` — `remove_duplicates(source_folder, processed_folder)` — removes files from source that already appear in processed folder by filename match (concurrent, 8 workers)

## Phase 3 — Pipeline orchestration

- [x] **3.1** Create `norma/pipeline.py` — `run_pipeline(config: Config)`:
  - Auto-split: if input folder contains >3000 flat files, split into `Folder_001` etc. before processing
  - Spin up `ThreadPoolExecutor(max_workers=config.workers)`
  - Submit batches of `config.batch_size` files to `processor.process_batch`
  - Track counts: renamed, errors, skipped, empty
  - After processing: call `dedup.remove_duplicates`
  - Write `processed.log` to output folder
  - Return stats dict for display

## Phase 4 — CLI

- [x] **4.1** Create `norma/cli.py` with `typer` app:
  - `norma run <input_folder> [--format] [--output] [--model] [--workers] [--batch-size] [--dry-run] [--ollama-url]`
  - `norma status` — ping Ollama, list available models, print recommended setup
  - `norma retry <folder>` — re-run pipeline on files that are still in the errors folder
- [x] **4.2** Integrate `rich` live display into `cli.py` — progress bar + live stats panel during `run` command (as designed in design.md)
- [x] **4.3** Dry-run mode: compute new names via LLM but print a preview table instead of copying files

## Phase 5 — Cleanup and packaging

- [x] **5.1** Delete old scripts: `RenameBooks.py`, `Processor.py`, `DelDupFiles.py`, `Split Batches.py`, `RemoveErrors.py`, `RemoveAlready done.py`, `rmStartSpace.py`, `RenameByParentFolder .py`
- [x] **5.2** Remove `processed_files.log` from repo root; add `*.log` and `norma-output/` to `.gitignore`
- [x] **5.3** Update `CLAUDE.md` to reflect new structure and commands
- [x] **5.4** Write `README.md`:
  - What norma is (the pitch: local, private, any domain, any language)
  - Requirements: Python 3.10+, Ollama, `ollama pull qwen2.5:3b`
  - Install: `pipx install .`
  - Usage examples (books, invoices, research papers)
  - `--dry-run` tip
  - Performance note (batching, threading)
  - License

## Phase 6 — Validation

- [x] **6.1** Smoke test: run `norma run` against a small folder (~50 files) with `--dry-run` and verify output preview is correct
- [x] **6.2** Smoke test: run without `--dry-run` and verify files appear in output folder with correct names
- [x] **6.3** Test error handling: point at empty folder, point at folder with 0-byte files, run with Ollama stopped
- [x] **6.4** Test batch fallback: verify that if LLM returns wrong count, individual fallback produces correct results
