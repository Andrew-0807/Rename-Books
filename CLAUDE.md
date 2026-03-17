# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**norma** is a local, privacy-first CLI tool that uses a local LLM (via Ollama) to rename files into any format the user defines — regardless of input language, domain, or naming convention. All processing is local; no filenames are sent externally.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) running locally with the default model pulled:

  ```bash
  ollama pull qwen2.5:3b
  ```

## Install & Run

```bash
pip install -e .        # dev install
norma --help
norma run ./some-folder --format "{Author} - {Title}"
norma run ./invoices    --format "{Client} / Invoice / {Date}" --dry-run
norma status            # check Ollama connectivity
norma retry ./norma-output/_errors --format "{Author} - {Title}"
```

## Package Structure

```text
norma/
├── cli.py        # typer entry point — all commands (run, status, retry)
├── pipeline.py   # orchestrates: auto-split → batch process → dedup → log
├── processor.py  # FileProcessor: LLM batching, file copy, collision handling
├── prompt.py     # builds system prompt dynamically from --format string
├── dedup.py      # removes source files already present in Processed/ mirror
└── config.py     # Config dataclass — all runtime settings, no global state
```

## Architecture

**Key design: batching.** Instead of one LLM call per file, `processor.py` sends a numbered list of 15 filenames per call and parses the numbered response. This gives ~10× throughput over the original approach. Falls back to per-file calls if the response count doesn't match.

**Data flow:**

1. `cli.py` builds a `Config` dataclass from CLI flags and calls `run_pipeline()`
2. `pipeline.py` auto-splits flat folders >3000 files, collects all files, chunks into batches, submits to `ThreadPoolExecutor(workers=8)`
3. Each worker calls `processor.process_and_apply_batch()` → LLM call → file copies to `norma-output/`
4. After all batches: `dedup.py` removes originals that now exist in `Processed/`
5. Stats logged to `norma-output/processed.log`

**Prompt design:** `prompt.py` parses `{Field}` tokens from the format string, maps known field names to semantic descriptions, and assembles a system prompt with numbered-list rules and few-shot examples. The default `{Author} - {Title}` format uses curated multilingual examples from the original codebase.

**Config flows through everything** — no `os.chdir()`, no hardcoded paths, no module-level constants.

## Default model: `qwen2.5:3b`

Same size class as the original `gemma2:2b` but dramatically better at structured output and multilingual filenames. Users can override with `--model qwen2.5:7b` for higher quality at lower speed.

## OpenSpec artifacts

Change proposal, design, and tasks live in [openspec/changes/norma-refactor/](openspec/changes/norma-refactor/).
