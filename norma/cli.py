from __future__ import annotations

import logging
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from dataclasses import replace

from .config import Config
from .pipeline import run_pipeline
from .tui import run_tui

# Force UTF-8 on Windows so Rich can render its box-drawing and arrow characters
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

app = typer.Typer(
    name="norma",
    help="AI-powered universal file normalizer — any domain, any language, any format.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console(legacy_windows=False)

DEFAULT_FORMAT = "{Author} - {Title}"
DEFAULT_MODEL_OLLAMA = "qwen2.5:3b"
DEFAULT_MODEL_LMSTUDIO = (
    "local-model"  # LM Studio ignores this field; uses whatever is loaded
)

# Full base URLs including /v1
BACKEND_URLS = {
    "ollama": "http://localhost:11434/v1",
    "lmstudio": "http://localhost:1234/v1",
}


class Backend(str, Enum):
    ollama = "ollama"
    lmstudio = "lmstudio"


def _resolve_api_url(backend: Backend, api_url: Optional[str]) -> str:
    """api_url overrides backend default when explicitly provided."""
    if api_url:
        return api_url
    return BACKEND_URLS[backend.value]


def _default_model(backend: Backend) -> str:
    return (
        DEFAULT_MODEL_LMSTUDIO if backend == Backend.lmstudio else DEFAULT_MODEL_OLLAMA
    )


# ------------------------------------------------------------------
# norma tui
# ------------------------------------------------------------------


@app.command()
def tui(
    input_folder: Path = typer.Argument(..., help="Folder containing files to rename"),
    format: str = typer.Option(
        DEFAULT_FORMAT,
        "--format",
        "-f",
        help='Output naming template, e.g. "{Author} - {Title}"',
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Destination folder (default: <input_folder>/../norma-output)",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model name (default depends on --backend)"
    ),
    workers: int = typer.Option(
        16, "--workers", "-w", help="Concurrent worker threads"
    ),
    batch_size: int = typer.Option(
        100, "--batch-size", "-b", help="Files per LLM call"
    ),
    backend: Backend = typer.Option(
        Backend.ollama, "--backend", help="Local LLM backend: ollama or lmstudio"
    ),
    api_url: Optional[str] = typer.Option(
        None, "--api-url", help="Override API base URL (e.g. http://localhost:1234/v1)"
    ),
) -> None:
    """Open a real-time TUI to rename files in INPUT_FOLDER."""
    if not input_folder.exists():
        console.print(f"[red]Error:[/red] Folder not found: {input_folder}")
        raise typer.Exit(1)

    if not input_folder.is_dir():
        console.print(f"[red]Error:[/red] Path is not a directory: {input_folder}")
        raise typer.Exit(1)

    resolved_url = _resolve_api_url(backend, api_url)
    resolved_model = model or _default_model(backend)
    resolved_output = output or (input_folder.parent / "norma-output")

    config = Config(
        input_folder=input_folder.resolve(),
        output_folder=resolved_output.resolve(),
        format_string=format,
        model=resolved_model,
        workers=workers,
        batch_size=batch_size,
        dry_run=False,
        api_url=resolved_url,
    )

    _configure_logging(config.output_folder)

    reachable, _ = _check_api(resolved_url)
    if not reachable:
        _print_connection_error(backend, resolved_url, resolved_model)
        raise typer.Exit(1)

    run_tui(config)


# ------------------------------------------------------------------
# norma run
# ------------------------------------------------------------------


@app.command()
def run(
    input_folder: Path = typer.Argument(..., help="Folder containing files to rename"),
    format: str = typer.Option(
        DEFAULT_FORMAT,
        "--format",
        "-f",
        help='Output naming template, e.g. "{Author} - {Title}"',
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Destination folder (default: <input_folder>/../norma-output)",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model name (default depends on --backend)"
    ),
    workers: int = typer.Option(
        16, "--workers", "-w", help="Concurrent worker threads"
    ),
    batch_size: int = typer.Option(
        100, "--batch-size", "-b", help="Files per LLM call"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Preview renames without copying files"
    ),
    backend: Backend = typer.Option(
        Backend.ollama, "--backend", help="Local LLM backend: ollama or lmstudio"
    ),
    api_url: Optional[str] = typer.Option(
        None, "--api-url", help="Override API base URL (e.g. http://localhost:1234/v1)"
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        "-r",
        help="Retry failed files this many times (0 = no retry)",
    ),
) -> None:
    """Rename all files in INPUT_FOLDER using an AI-powered format transform."""
    if not input_folder.exists():
        console.print(f"[red]Error:[/red] Folder not found: {input_folder}")
        raise typer.Exit(1)

    if not input_folder.is_dir():
        console.print(f"[red]Error:[/red] Path is not a directory: {input_folder}")
        raise typer.Exit(1)

    resolved_url = _resolve_api_url(backend, api_url)
    resolved_model = model or _default_model(backend)
    resolved_output = output or (input_folder.parent / "norma-output")

    config = Config(
        input_folder=input_folder.resolve(),
        output_folder=resolved_output.resolve(),
        format_string=format,
        model=resolved_model,
        workers=workers,
        batch_size=batch_size,
        dry_run=dry_run,
        api_url=resolved_url,
    )

    _configure_logging(config.output_folder)

    reachable, model_available = _check_api(resolved_url)
    if not reachable:
        _print_connection_error(backend, resolved_url, resolved_model)
        raise typer.Exit(1)
    if not model_available and backend == Backend.lmstudio:
        console.print(
            "[yellow]Warning:[/yellow] LM Studio is running but no model is loaded.\n"
            "  Open LM Studio → Developer tab → load a model → Start Server.\n"
            "  Proceeding anyway — completions will fail until a model is loaded.\n"
        )

    _print_run_header(config, backend, dry_run)

    start = time.monotonic()
    stats = _run_with_progress(config)

    if dry_run:
        _print_dry_run_preview(stats.get("preview", []), stats.get("errors", 0))
        return

    # Auto-retry loop — move _errors/ files through fresh pipeline passes
    attempt = 0
    total_renamed = stats.get("renamed", 0)
    total_errors = stats.get("errors", 0)

    while stats.get("errors", 0) > 0 and attempt < max_retries:
        attempt += 1
        errors_folder = config.errors_folder
        retry_queue = config.output_folder / f"_retry_{attempt}"

        # Stage errors into a fresh folder so _errors/ resets cleanly each pass
        errors_folder.rename(retry_queue)

        console.print(
            f"\n  [yellow]Retry {attempt}/{max_retries}[/yellow] — "
            f"{stats['errors']} files failed, trying again...\n"
        )

        retry_config = replace(config, input_folder=retry_queue)
        stats = _run_with_progress(retry_config)

        total_renamed += stats.get("renamed", 0)
        total_errors = stats.get("errors", 0)

        # Clean up staging dir (originals were copies)
        import shutil as _shutil

        _shutil.rmtree(retry_queue, ignore_errors=True)

    elapsed = time.monotonic() - start
    _print_summary(
        {**stats, "renamed": total_renamed, "errors": total_errors},
        elapsed,
        config,
    )


# ------------------------------------------------------------------
# norma status
# ------------------------------------------------------------------


@app.command()
def status(
    backend: Backend = typer.Option(
        Backend.ollama, "--backend", help="Backend to check: ollama or lmstudio"
    ),
    api_url: Optional[str] = typer.Option(
        None, "--api-url", help="Override API base URL"
    ),
) -> None:
    """Check backend connectivity and list available models."""
    import httpx

    resolved_url = _resolve_api_url(backend, api_url)
    console.print(f"\n[bold]norma[/bold] — status check\n")
    console.print(f"  Backend:  [dim]{backend.value}[/dim]")
    console.print(f"  API URL:  [dim]{resolved_url}[/dim]")

    try:
        r = httpx.get(f"{resolved_url}/models", timeout=5)
        r.raise_for_status()
        data = r.json()
        models = [m["id"] for m in data.get("data", [])]

        console.print("  Status:   [green]Connected[/green]")

        if models:
            console.print(f"\n  Available models ({len(models)}):")
            for m in models:
                marker = ""
                if backend == Backend.ollama:
                    if m.startswith("qwen2.5:3b"):
                        marker = " [green]← recommended[/green]"
                    elif m.startswith("qwen2.5:7b"):
                        marker = " [blue]← high quality[/blue]"
                else:
                    marker = " [green]← currently loaded[/green]"
                console.print(f"    • {m}{marker}")
        else:
            console.print("\n  [yellow]No models found.[/yellow]")
            if backend == Backend.ollama:
                console.print(f"  Run: [bold]ollama pull {DEFAULT_MODEL_OLLAMA}[/bold]")
            else:
                console.print("  Load a model in LM Studio and start the local server.")

        if backend == Backend.ollama and not any(
            m.startswith("qwen2.5") for m in models
        ):
            console.print(f"\n  [yellow]Tip:[/yellow] Install the recommended model:")
            console.print(f"    [bold]ollama pull {DEFAULT_MODEL_OLLAMA}[/bold]")

        if backend == Backend.lmstudio:
            console.print(
                f"\n  [dim]Note:[/dim] LM Studio uses whatever model is currently loaded."
            )
            console.print(f"  [dim]The --model flag is ignored by LM Studio.[/dim]")

    except Exception as e:
        console.print(f"  Status:   [red]Failed[/red] — {e}")
        _print_connection_error(backend, resolved_url, _default_model(backend))


# ------------------------------------------------------------------
# norma retry
# ------------------------------------------------------------------


@app.command()
def retry(
    errors_folder: Path = typer.Argument(
        ..., help="Folder containing files that failed previously"
    ),
    format: str = typer.Option(
        DEFAULT_FORMAT, "--format", "-f", help="Output naming template"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Destination folder"
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
    workers: int = typer.Option(8, "--workers", "-w"),
    batch_size: int = typer.Option(15, "--batch-size", "-b"),
    backend: Backend = typer.Option(
        Backend.ollama, "--backend", help="Backend: ollama or lmstudio"
    ),
    api_url: Optional[str] = typer.Option(
        None, "--api-url", help="Override API base URL"
    ),
) -> None:
    """Re-process files from a previous run's _errors folder."""
    if not errors_folder.exists():
        console.print(f"[red]Error:[/red] Folder not found: {errors_folder}")
        raise typer.Exit(1)

    resolved_url = _resolve_api_url(backend, api_url)
    resolved_model = model or _default_model(backend)
    resolved_output = output or (errors_folder.parent / "norma-output")

    config = Config(
        input_folder=errors_folder.resolve(),
        output_folder=resolved_output.resolve(),
        format_string=format,
        model=resolved_model,
        workers=workers,
        batch_size=batch_size,
        dry_run=False,
        api_url=resolved_url,
    )

    _configure_logging(config.output_folder)
    console.print(f"\n[bold]Retrying[/bold] {errors_folder} → {resolved_output}\n")

    stats = run_pipeline(config)
    _print_summary(stats, 0, config)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _run_with_progress(config: Config) -> dict:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )
    task_id = progress.add_task("Processing files...", total=None)

    def on_progress(completed: int, total: int) -> None:
        progress.update(task_id, completed=completed, total=total)

    with progress:
        return run_pipeline(config, progress_callback=on_progress)


# ------------------------------------------------------------------
# Display helpers
# ------------------------------------------------------------------


def _print_run_header(config: Config, backend: Backend, dry_run: bool) -> None:
    mode = "[yellow]DRY RUN — no files will be moved[/yellow]" if dry_run else ""
    console.print(
        f"\n[bold white on blue] norma [/bold white on blue]  "
        f"{config.input_folder} [dim]→[/dim] {config.output_folder}  {mode}\n"
    )
    meta = Table.grid(padding=(0, 2))
    meta.add_column()
    meta.add_column(style="dim")
    meta.add_column()
    meta.add_column(style="dim")
    meta.add_row("Backend", backend.value, "Format", config.format_string)
    meta.add_row("Model", config.model, "Batch", f"{config.batch_size} files/call")
    meta.add_row("Workers", str(config.workers), "API", config.api_url)
    console.print(meta)
    console.print()


def _print_summary(stats: dict, elapsed: float, config: Config) -> None:
    renamed = stats.get("renamed", 0)
    errors = stats.get("errors", 0)
    empty = stats.get("empty", 0)
    deduped = stats.get("deduped", 0)
    rate = f"{int(renamed / elapsed * 60)} files/min" if elapsed > 0 else "—"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()
    table.add_row("✓ renamed", f"[green]{renamed}[/green]")
    table.add_row("✗ errors", f"[red]{errors}[/red]")
    table.add_row("○ empty", str(empty))
    table.add_row("⊘ deduped", str(deduped))
    table.add_row("⏱ elapsed", f"{elapsed:.1f}s  ({rate})")

    console.print(Panel(table, title="[bold]Done[/bold]", expand=False))
    if errors:
        console.print(f"  [dim]Error files:[/dim] {config.errors_folder}")
    console.print(f"  [dim]Log:[/dim] {config.processed_log}\n")


def _print_dry_run_preview(preview: list[tuple[str, str]], errors: int = 0) -> None:
    if not preview:
        msg = "[yellow]No files would be renamed.[/yellow]"
        if errors:
            msg += (
                f" [red]{errors} LLM errors[/red] — is a model loaded in your backend?"
            )
        console.print(msg)
        return

    table = Table(title=f"Dry run preview — {len(preview)} files", show_lines=False)
    table.add_column("Original", style="dim", no_wrap=False)
    table.add_column("→ New name", style="green", no_wrap=False)

    for original, new_name in preview[:100]:
        table.add_row(original, new_name)

    if len(preview) > 100:
        table.add_row(f"[dim]... and {len(preview) - 100} more[/dim]", "")

    console.print(table)
    console.print(
        "\n[dim]Run without [bold]--dry-run[/bold] to apply these renames.[/dim]\n"
    )


def _print_connection_error(backend: Backend, url: str, model: str) -> None:
    if backend == Backend.lmstudio:
        console.print(
            f"[red]Error:[/red] Cannot reach LM Studio at [bold]{url}[/bold]\n"
            "  • Open LM Studio and start the local server (Developer tab → Start Server)\n"
            "  • Load a model before starting the server\n"
            "  • Run [bold]norma status --backend lmstudio[/bold] to diagnose"
        )
    else:
        console.print(
            f"[red]Error:[/red] Cannot reach Ollama at [bold]{url}[/bold]\n"
            "  • Make sure Ollama is running: [dim]ollama serve[/dim]\n"
            f"  • Pull the model if needed:    [dim]ollama pull {model}[/dim]\n"
            "  • Run [bold]norma status[/bold] to diagnose"
        )


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------


def _check_api(api_url: str) -> tuple[bool, bool]:
    """Returns (reachable, has_models)."""
    try:
        import httpx

        r = httpx.get(f"{api_url}/models", timeout=5)
        r.raise_for_status()
        models = r.json().get("data", [])
        return True, len(models) > 0
    except Exception:
        return False, False


def _configure_logging(output_folder: Path) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=output_folder / "norma.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
