# Proposal: norma — AI-powered universal file normalizer

## What

Refactor the `Rename-Books` project into **norma**, a standalone, privacy-first CLI tool that uses a local LLM to rename and normalize any files into any format the user defines — regardless of input language, domain, or naming convention.

The name **norma** comes from *normalize*. It's short, memorable, and domain-agnostic — signaling that this tool is not about books, but about bringing order to any collection of files.

## Why

The current codebase works — it proved its concept by renaming 100,000 files in ~10 minutes on capable hardware. But it is not shareable, not flexible, and not portfolio-ready:

- All paths are hardcoded to `D:/11/`
- The naming format (`Author - Title`) is hardcoded in the LLM prompt
- There is no entry point — it's a collection of scripts run in a specific manual order
- The model (`gemma2:2b`) is outdated and gives inconsistent results
- It cannot be installed or reused without editing source code

The core idea — "use a local LLM to intelligently transform filenames into any user-defined format" — has broader applications: logistics (invoice normalization), legal (document filing), research (paper archiving), media libraries, and anywhere humans accumulate poorly-named files.

This refactor elevates that idea into a proper tool.

## Goals

1. **Remove all hardcoded paths** — input/output/model configurable entirely from CLI
2. **Make the format user-defined** — via template string `"{Author} - {Title}"` or a natural language description
3. **Single entry point** — `norma run ./folder` replaces the multi-script manual workflow
4. **Keep the performance** — batched LLM calls + concurrent processing maintain throughput
5. **Upgrade the model default** — `qwen2.5:3b` as default (same size class as gemma2:2b, dramatically better instruction-following)
6. **Installable** — works via `pipx install norma` and eventually as a standalone executable
7. **Portfolio-ready** — clean README, good CLI UX, proper package structure

## Out of Scope (this change)

- Web UI or GUI
- Cloud LLM support (stays local-only for now)
- Standalone `.exe` distribution (separate phase after this)
- Plugin system or domain presets

## Success Criteria

- `norma run ./some-folder --format "{Author} - {Title}"` processes files end-to-end without any manual steps
- No hardcoded paths anywhere in the codebase
- The tool works on a folder of books, invoices, or any other files with the same command
- Installable as a package; `norma --help` works after install
- Throughput is maintained or improved vs the original scripts
