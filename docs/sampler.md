# Log Sampler

The **sampler** module reduces high-volume log streams by keeping only every
*N*-th entry, making it easier to spot trends without being overwhelmed by
repetitive lines.

## Python API

```python
from logslice.sampler import sample
from logslice.filter import filter_file

with open("app.log") as fh:
    entries = list(filter_file(fh))

# Keep every 5th entry globally
for entry in sample(entries, rate=5):
    print(entry)

# Keep every 5th entry *per severity level*
for entry in sample(entries, rate=5, per_severity=True):
    print(entry)
```

### `sample(entries, rate, per_severity=False)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `entries` | `Iterable[LogEntry]` | Source log entries. |
| `rate` | `int` | Keep 1 in every *rate* entries. Must be ≥ 1. |
| `per_severity` | `bool` | Maintain independent counters per severity level. |

Raises `ValueError` if `rate < 1`.

## CLI

```
logslice-sample [OPTIONS] [FILE]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-n N` / `--rate N` | `10` | Keep every N-th entry. |
| `--per-severity` | off | Count independently per severity. |
| `--colour` | off | Colourise output. |

### Examples

```bash
# Sample a busy log, keeping 1 in 100 lines
logslice-sample -n 100 app.log

# Pipe from tail, preserving rare ERROR lines
tail -f app.log | logslice-sample -n 50 --per-severity
```
