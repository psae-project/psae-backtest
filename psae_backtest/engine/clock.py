from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd

try:
    import exchange_calendars as xcals
    NYSE = xcals.get_calendar("XNYS")
    HAS_XCALS = True
except Exception:
    HAS_XCALS = False


@dataclass
class BarEvent:
    timestamp: datetime
    bar_type: str  # "open", "bar", "close"


class SimulatedClock:
    def __init__(self, start: str, end: str, frequency: str = "1h"):
        self.start = start
        self.end = end
        self.frequency = frequency

    def __iter__(self):
        if HAS_XCALS:
            sessions = NYSE.sessions_in_range(self.start, self.end)
            for session in sessions:
                open_time = NYSE.session_open(session)
                close_time = NYSE.session_close(session)
                yield BarEvent(open_time.to_pydatetime(), "open")
                t = open_time + pd.Timedelta(hours=1)
                while t < close_time:
                    yield BarEvent(t.to_pydatetime(), "bar")
                    t += pd.Timedelta(hours=1)
                yield BarEvent(close_time.to_pydatetime(), "close")
        else:
            # Fallback: plain hourly iteration
            t = pd.Timestamp(self.start)
            end = pd.Timestamp(self.end)
            while t <= end:
                yield BarEvent(t.to_pydatetime(), "bar")
                t += pd.Timedelta(hours=1)
