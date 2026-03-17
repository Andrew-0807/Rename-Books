from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    input_folder: Path
    output_folder: Path
    format_string: str
    model: str
    workers: int
    batch_size: int
    dry_run: bool
    api_url: str             # full base URL including /v1
    temperature: float = 0.1      # low = deterministic, fewer malformed responses
    max_tokens: Optional[int] = None  # None = auto (batch_size * 20)

    def __post_init__(self):
        if self.max_tokens is None:
            object.__setattr__(self, "max_tokens", self.batch_size * 20)

    @property
    def errors_folder(self) -> Path:
        return self.output_folder / "_errors"

    @property
    def processed_log(self) -> Path:
        return self.output_folder / "processed.log"
