"""Log line parser: extracts timestamp and severity from log entries."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Common log format: 2024-01-15 12:34:56,789 [ERROR] Some message
# Also supports ISO 8601: 2024-01-15T12:34:56.789Z [WARN] Some message
LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.,]?\d*Z?)"
    r"\s*\[?(?P<severity>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\]?"
    r"\s*(?P<message>.*)$",
    re.IGNORECASE,
)

TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]

SEVERITY_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "FATAL": 50,
}


@dataclass
class LogEntry:
    raw: str
    timestamp: Optional[datetime]
    severity: Optional[str]
    message: str

    @property
    def severity_level(self) -> int:
        if self.severity is None:
            return 0
        return SEVERITY_LEVELS.get(self.severity.upper(), 0)


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Try multiple timestamp formats and return a datetime or None."""
    ts_str = ts_str.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def parse_line(line: str) -> LogEntry:
    """Parse a single log line into a LogEntry."""
    line = line.rstrip("\n")
    match = LOG_PATTERN.match(line)
    if not match:
        return LogEntry(raw=line, timestamp=None, severity=None, message=line)

    ts = parse_timestamp(match.group("timestamp"))
    severity = match.group("severity").upper() if match.group("severity") else None
    # Normalise WARNING -> WARN for consistency
    if severity == "WARNING":
        severity = "WARN"
    message = match.group("message").strip()
    return LogEntry(raw=line, timestamp=ts, severity=severity, message=message)
