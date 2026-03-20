from __future__ import annotations

import queue
import shutil
import threading
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Footer, Input, Log, Static

from .config import Config
from .pipeline import run_pipeline
from .processor import FileResult

INITIAL_ROWS = 50


class EditModal(Widget):
    class Saved(Message):
        def __init__(self, original: Path, corrected: str) -> None:
            self.original = original
            self.corrected = corrected
            super().__init__()

    class Cancelled(Message):
        def __init__(self) -> None:
            super().__init__()

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save", show=False),
    ]

    def __init__(
        self,
        original: Path,
        llm_suggestion: str,
        success: bool,
        final_name: str | None,
    ) -> None:
        super().__init__()
        self.original = original
        self.llm_suggestion = llm_suggestion or ""
        self.success = success
        self.final_name = final_name or ""

    def compose(self) -> ComposeResult:
        yield Static(f"Original: {self.original.name}", id="original-label")
        yield Input(value=self.llm_suggestion, id="correction-input")
        status = "[green]OK[/green]" if self.success else "[red]FAILED[/red]"
        if self.final_name and self.success:
            status += f" -> {self.final_name}"
        yield Static(status, id="status-label")
        yield Static("[b]Ctrl+S[/b] save   [b]Esc[/b] cancel", id="hints-label")

    def on_mount(self) -> None:
        input_widget = self.query_one("#correction-input", Input)
        input_widget.focus()
        input_widget.cursor_position = len(input_widget.value)

    def action_save(self) -> None:
        input_widget = self.query_one("#correction-input", Input)
        corrected = input_widget.value.strip()
        self.post_message(self.Saved(self.original, corrected))

    def action_cancel(self) -> None:
        self.post_message(self.Cancelled())


class NormaeApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    #log-feed {
        height: 8;
        border: solid $border;
        margin: 0 1;
    }

    #file-table {
        height: 1fr;
        border: solid $border;
        margin: 0 1;
    }

    DataTable {
        height: 100%;
    }

    DataTable > .datatable--cursor {
        background: $accent 20%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("r", "retry_selected", "Retry"),
        Binding("a", "retry_all", "Retry All"),
        Binding("e", "edit_selected", "Edit"),
        Binding("g", "scroll_top", "Top", show=False),
        Binding("G", "scroll_bottom", "Bottom", show=False),
    ]

    class PipelineDone(Message):
        pass

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self._result_queue: queue.Queue[Any] = queue.Queue()
        self._pipeline_thread: threading.Thread | None = None

        self._all_results: list[FileResult] = []
        self._loaded_count = 0
        self._total_rows = 0
        self._user_scrolled_log = False

    def compose(self) -> ComposeResult:
        yield Log(id="log-feed", min_height=8, max_height=8)
        yield DataTable(id="file-table")
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"norma -- {self.config.input_folder.name}"
        self.sub_title = self.config.format_string

        table = self.query_one("#file-table", DataTable)
        table.add_columns("", "Original", "LLM Suggestion", "Final Name")
        table.cursor_type = "row"

        table.watch_scroll_y = self._on_table_scroll  # type: ignore[method-assign]

        self.set_interval(0.1, self._drain_queue)
        self._pipeline_thread = threading.Thread(target=self._run_pipeline, daemon=True)
        self._pipeline_thread.start()

    def _run_pipeline(self) -> None:
        try:

            def callback(results: list[FileResult]) -> None:
                self._result_queue.put(results)

            run_pipeline(self.config, result_callback=callback)
        except Exception as e:
            self._result_queue.put(str(e))
        finally:
            self._result_queue.put(None)

    def _drain_queue(self) -> None:
        try:
            while True:
                item = self._result_queue.get_nowait()
                if item is None:
                    self.post_message(self.PipelineDone())
                    return
                if isinstance(item, str):
                    self._append_log(item)
                    continue
                self._on_batch_results(item)
        except queue.Empty:
            pass

    def _on_batch_results(self, batch_results: list[FileResult]) -> None:
        self._all_results.extend(batch_results)
        self._total_rows = len(self._all_results)

        table = self.query_one("#file-table", DataTable)
        log_widget = self.query_one("#log-feed", Log)

        for i, (original, llm_suggestion, success, final_name) in enumerate(
            batch_results
        ):
            idx = len(self._all_results) - len(batch_results) + i
            icon = "[green]![/green]" if success else "[red]![/red]"
            orig_name = original.name
            llm_str = llm_suggestion or "--"
            final_str = final_name or ("(error)" if not success else "(copied)")
            table.add_row(icon, orig_name, llm_str, final_str, key=str(idx))
            self._append_log(f"{icon} {orig_name} -> {final_str}  [dim]{llm_str}[/dim]")

        self._update_status()

        if self._loaded_count == 0:
            self._load_more_rows()

    def _append_log(self, text: str) -> None:
        log_widget = self.query_one("#log-feed", Log)
        log_widget.write_line(text)
        if not self._user_scrolled_log:
            log_widget.scroll_home(animate=False)

    def _load_more_rows(self) -> None:
        table = self.query_one("#file-table", DataTable)
        rows = list(table.rows.values())
        if self._loaded_count >= len(rows):
            return
        end = min(self._loaded_count + INITIAL_ROWS, len(rows))
        for i in range(self._loaded_count, end):
            table.refresh_row(rows[i])
        self._loaded_count = end

    def _on_table_scroll(self, scroll_y: float) -> None:
        table = self.query_one("#file-table", DataTable)
        if table.max_scroll_y == 0:
            return
        distance_from_bottom = table.max_scroll_y - scroll_y
        if distance_from_bottom < 10:
            self._load_more_rows()

    def _update_status(self) -> None:
        renamed = sum(1 for r in self._all_results if r[2])
        errors = sum(1 for r in self._all_results if not r[2])
        total = len(self._all_results)
        self.sub_title = (
            f"[green]V {renamed}[/green]  [red]X {errors}[/red]  "
            f"{total} total   {self.config.format_string}"
        )

    def _get_selected_result(self) -> FileResult | None:
        table = self.query_one("#file-table", DataTable)
        cursor = table.cursor_row
        if cursor < 0 or cursor >= len(self._all_results):
            return None
        return self._all_results[cursor]

    def action_retry_selected(self) -> None:
        result = self._get_selected_result()
        if result:
            self._append_log(f"[yellow]Queued for retry:[/yellow] {result[0].name}")

    def action_retry_all(self) -> None:
        errors = [r for r in self._all_results if not r[2]]
        if not errors:
            self._append_log("[yellow]No errors to retry.[/yellow]")
            return
        self._append_log(f"[yellow]Queued {len(errors)} errors for retry.[/yellow]")

    def action_edit_selected(self) -> None:
        result = self._get_selected_result()
        if result is None:
            return
        llm: str = result[1] if result[1] is not None else ""
        modal = EditModal(result[0], llm, result[2], result[3])
        self.mount(modal)

    def on_edit_modal_saved(self, event: EditModal.Saved) -> None:
        if not event.corrected:
            return
        orig = event.original
        dest = self.config.output_folder / event.corrected
        if dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            counter = 2
            while True:
                candidate = self.config.output_folder / f"{stem} ({counter}){suffix}"
                if not candidate.exists():
                    dest = candidate
                    break
                counter += 1
        try:
            shutil.copy2(orig, dest)
            self._append_log(f"[green]Saved:[/green] {orig.name} -> {dest.name}")
            table = self.query_one("#file-table", DataTable)
            for idx, r in enumerate(self._all_results):
                if r[0] == orig:
                    row_key = str(idx)
                    if row_key in table.rows:
                        table.update_cell(row_key, "Final Name", dest.name)
                        table.update_cell(row_key, "", "[green]![/green]")
                    break
        except Exception as e:
            self._append_log(f"[red]Save failed:[/red] {e}")

    def on_edit_modal_cancelled(self, event: EditModal.Cancelled) -> None:
        pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        pass

    def action_scroll_top(self) -> None:
        table = self.query_one("#file-table", DataTable)
        table.scroll_home(animate=True)

    def action_scroll_bottom(self) -> None:
        table = self.query_one("#file-table", DataTable)
        table.scroll_end(animate=True)

    def action_quit(self) -> None:
        self.exit()

    def on_PipelineDone(self) -> None:
        renamed = sum(1 for r in self._all_results if r[2])
        errors = sum(1 for r in self._all_results if not r[2])
        self._append_log("")
        self._append_log(
            f"[bold]Pipeline done --[/bold] "
            f"[green]V {renamed}[/green]  [red]X {errors}[/red]"
        )
        if errors > 0:
            self._append_log("[dim]Press [b]a[/b] to retry all errors.[/dim]")
        self._update_status()


def run_tui(config: Config) -> None:
    app = NormaeApp(config)
    app.run()
