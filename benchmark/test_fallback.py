"""
Task 6.4: Test batch fallback when LLM returns wrong response count.
Patches _parse_numbered_response to return None for the first batch call,
forcing fallback to individual calls. Verifies all 3 files still get renamed.
"""
import sys
sys.path.insert(0, "e:/Programming/Rename-Books")

from pathlib import Path
from unittest.mock import patch
import norma.processor as proc_module
from norma.config import Config
from norma.processor import FileProcessor

config = Config(
    input_folder=Path("e:/Programming/Rename-Books/benchmark/files"),
    output_folder=Path("e:/Programming/Rename-Books/benchmark/test-fallback-output"),
    format_string="{Author} - {Title}",
    model="local-model",
    workers=1,
    batch_size=3,
    dry_run=False,
    api_url="http://localhost:1234/v1",
)

files = [
    Path("e:/Programming/Rename-Books/benchmark/files/john_anderson_the_last_hope.epub"),
    Path("e:/Programming/Rename-Books/benchmark/files/william_taylor_lost_in_time.pdf"),
    Path("e:/Programming/Rename-Books/benchmark/files/james_taylor_forgotten_world.epub"),
]

original_parse = proc_module._parse_numbered_response
parse_calls = [0]
individual_calls = [0]

def patched_parse(raw, expected):
    parse_calls[0] += 1
    if parse_calls[0] == 1:
        print(f"  [patch] First batch parse -> returning None to trigger fallback")
        return None  # simulates mismatch
    return original_parse(raw, expected)

original_individually = FileProcessor._get_names_individually
def patched_individually(self, files):
    individual_calls[0] = len(files)
    print(f"  [patch] Fallback: calling _get_names_individually for {len(files)} files")
    return original_individually(self, files)

proc = FileProcessor(config)

with patch.object(proc_module, "_parse_numbered_response", side_effect=patched_parse), \
     patch.object(FileProcessor, "_get_names_individually", patched_individually):
    results = proc.process_and_apply_batch(files)

successes = [(f, name) for f, name, ok in results if ok]
failures  = [(f, name) for f, name, ok in results if not ok]

print(f"Batch parse calls:    {parse_calls[0]}  (expected: 1)")
print(f"Individual fallback:  {individual_calls[0]} files  (expected: 3)")
print(f"Successes:            {len(successes)}")
print(f"Failures:             {len(failures)}")
for f, name in successes:
    print(f"  OK  {f.name} -> {name}")
for f, name in failures:
    print(f"  ERR {f.name}")

assert len(successes) == 3, f"Expected 3 successes, got {len(successes)}"
assert parse_calls[0] == 1, f"Expected 1 batch parse call, got {parse_calls[0]}"
assert individual_calls[0] == 3, f"Expected fallback for 3 files, got {individual_calls[0]}"
print("\nPASS: fallback triggered and all 3 files renamed correctly")
