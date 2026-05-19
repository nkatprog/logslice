# logslice

> Command-line utility to extract and filter log segments by time range and severity

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
logslice [OPTIONS] <logfile>
```

**Basic example — extract errors between two timestamps:**

```bash
logslice --start "2024-03-01 08:00:00" --end "2024-03-01 09:00:00" --level ERROR app.log
```

**Options:**

| Flag | Description |
|------|-------------|
| `--start` | Start of time range (inclusive) |
| `--end` | End of time range (inclusive) |
| `--level` | Minimum severity level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `--output` | Write results to a file instead of stdout |
| `--format` | Log timestamp format (default: `%Y-%m-%d %H:%M:%S`) |

**Example — save warnings and above to a file:**

```bash
logslice --start "2024-03-01 00:00:00" --level WARNING --output filtered.log app.log
```

---

## Requirements

- Python 3.8+

---

## License

This project is licensed under the [MIT License](LICENSE).