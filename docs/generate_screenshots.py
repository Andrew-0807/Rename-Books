"""
Generate SVG terminal screenshots for the README.
Uses Rich's built-in SVG export via Console(record=True).
"""
import sys
sys.path.insert(0, "e:/Programming/Rename-Books")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

OUT = Path("e:/Programming/Rename-Books/docs")
OUT.mkdir(exist_ok=True)


def save_svg(console: Console, filename: str) -> None:
    svg = console.export_svg(title=filename.replace(".svg", ""))
    (OUT / filename).write_text(svg, encoding="utf-8")
    print(f"  Saved {filename}")


# ─── Screenshot 1: dry-run preview ───────────────────────────────────────────
c = Console(record=True, width=90, legacy_windows=False)

c.print(
    "\n[bold white on blue] norma [/bold white on blue]  "
    "[dim]~/ebooks[/dim] [dim]->[/dim] [dim]~/norma-output[/dim]  "
    "[yellow]DRY RUN — no files will be moved[/yellow]\n"
)
meta = Table.grid(padding=(0, 2))
meta.add_column(); meta.add_column(style="dim")
meta.add_column(); meta.add_column(style="dim")
meta.add_row("Backend", "ollama",            "Format", "{Author} - {Title}")
meta.add_row("Model",   "qwen2.5:3b",        "Batch",  "100 files/call")
meta.add_row("Workers", "16",                "API",    "http://localhost:11434/v1")
c.print(meta)
c.print()

table = Table(title="Dry run preview — 12 files", show_lines=False, width=86)
table.add_column("Original", style="dim", no_wrap=False)
table.add_column("-> New name", style="green", no_wrap=False)

rows = [
    ("harry_potter_jk_rowling.epub",                "J.K. Rowling - Harry Potter.epub"),
    ("4.LISA_KLEYPAS_Scandal_in_primavara.pdf",     "Lisa Kleypas - Scandal in primavara.pdf"),
    ("Haralamb_Zinca_Interpolul_transmite.epub",    "Haralamb Zinca - Interpolul transmite arestati.epub"),
    ("1984_george_orwell.mobi",                     "George Orwell - 1984.mobi"),
    ("tolkien_lord_of_the_rings_vol1.epub",         "J.R.R. Tolkien - The Lord of the Rings Vol 1.epub"),
    ("gabriel-garcia-marquez-solitudine.epub",      "Gabriel Garcia Marquez - One Hundred Years of Solitude.epub"),
    ("INV-2024-ACME-CORP-000432.pdf",               "ACME Corp - Invoice 2024-000432.pdf"),
    ("smith2019_ml_paper_final_v2.pdf",             "Smith (2019) - ML Paper Final.pdf"),
    ("Jean_de_la_Hire_Cei_Trei_Cercetasi_V23.epub", "Jean de la Hire - Cei Trei Cercetasi V23.epub"),
    ("foundation_isaac_asimov.pdf",                 "Isaac Asimov - Foundation.pdf"),
    ("brave_new_world_huxley.epub",                 "Aldous Huxley - Brave New World.epub"),
    ("1365135809.epub",                             "Unknown - 1365135809.epub"),
]
for orig, new in rows:
    table.add_row(orig, new)

c.print(table)
c.print("\n[dim]Run without [bold]--dry-run[/bold] to apply these renames.[/dim]\n")
save_svg(c, "screenshot-dryrun.svg")


# ─── Screenshot 2: run summary ───────────────────────────────────────────────
c = Console(record=True, width=90, legacy_windows=False)

c.print(
    "\n[bold white on blue] norma [/bold white on blue]  "
    "[dim]~/ebooks (1 000 files)[/dim] [dim]->[/dim] [dim]~/norma-output[/dim]\n"
)
meta = Table.grid(padding=(0, 2))
meta.add_column(); meta.add_column(style="dim")
meta.add_column(); meta.add_column(style="dim")
meta.add_row("Backend", "ollama",     "Format", "{Author} - {Title}")
meta.add_row("Model",   "qwen2.5:3b", "Batch",  "100 files/call")
meta.add_row("Workers", "16",         "API",    "http://localhost:11434/v1")
c.print(meta)
c.print()

from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
c.print("  Processing files... [green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/green] [bold]1000/1000[/bold]")
c.print()

summary = Table(show_header=False, box=None, padding=(0, 2))
summary.add_column(style="dim"); summary.add_column()
summary.add_row("+ renamed",  "[green]998[/green]")
summary.add_row("x errors",   "[red]2[/red]")
summary.add_row("o empty",    "0")
summary.add_row("deduped",    "0")
summary.add_row("elapsed",    "68.4s  (877 files/min)")
c.print(Panel(summary, title="[bold]Done[/bold]", expand=False))
c.print("  [dim]Error files:[/dim] ~/norma-output/_errors")
c.print("  [dim]Log:[/dim] ~/norma-output/processed.log\n")
save_svg(c, "screenshot-run.svg")


# ─── Screenshot 3: norma status ──────────────────────────────────────────────
c = Console(record=True, width=70, legacy_windows=False)

c.print("\n[bold]norma[/bold] — status check\n")
c.print("  Backend:  [dim]ollama[/dim]")
c.print("  API URL:  [dim]http://localhost:11434/v1[/dim]")
c.print("  Status:   [green]Connected[/green]")
c.print("\n  Available models (3):")
c.print("    • qwen2.5:3b [green]<- recommended[/green]")
c.print("    • qwen2.5:7b [blue]<- high quality[/blue]")
c.print("    • llama3.2:3b")
c.print()
save_svg(c, "screenshot-status.svg")


print("\nAll screenshots saved to docs/")
