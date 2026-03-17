# norma — Iteration Results
Autoresearch-style optimization. Primary metric: files/min.
**Best config:** batch=100, workers=16, temp=0.1, max_tokens=2000, prompt=short
**Best throughput:** 871.5 files/min, 0.3% error rate

| Iter | Label | files/min | err% | format% | elapsed | Status | Description |
|------|-------|-----------|------|---------|---------|--------|-------------|
| 0 | iter00_baseline | 594.0 | 4.8 | 100.0 | 101.02s | KEEP ✓ | Baseline: default settings (batch=15, workers=8, temp=0.1, max_tok=512) |
| 1 | iter01_batch30 | 515.4 | 0.4 | 100.0 | 116.42s | DISCARD | Hypothesis: larger batch → fewer LLM round-trips → better throughput |
| 2 | iter02_batch50 | 752.6 | 0.2 | 100.0 | 79.72s | KEEP ✓ | Push batch to 50; max_tokens scaled to match expected output size |
| 3 | iter03_batch100 | 803.5 | 0.5 | 100.0 | 74.67s | KEEP ✓ | Maximum batch — amortise system prompt cost over 100 filenames |
| 4 | iter04_short_prompt | 805.2 | 0.2 | 100.0 | 74.51s | KEEP ✓ | Shorter system prompt: fewer input tokens per call |
| 5 | iter05_short_best_batch | 810.5 | 0.6 | 100.0 | 74.03s | KEEP ✓ | Short prompt combined with best batch size from iters 1-3 |
| 6 | iter06_workers4 | 792.2 | 0.6 | 100.0 | 75.74s | DISCARD | Reduce workers: GPU handles one request at a time, less thread overhead |
| 7 | iter07_workers16 | 862.7 | 0.3 | 100.0 | 69.55s | KEEP ✓ | Increase workers: test whether more parallelism saturates the GPU queue |
| 8 | iter08_tight_tokens | 871.5 | 0.3 | 100.0 | 68.84s | KEEP ✓ | Tight max_tokens = batch_size * 20 — prevent runaway responses |
| 9 | iter09_champion | 871.3 | 0.4 | 100.0 | 68.86s | DISCARD | All best settings + temperature=0.05 (most deterministic) |
