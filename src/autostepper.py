from __future__ import annotations

import threading
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from state import PerformanceState

Mode = Literal["tuning", "voice", "both"]


class AutoStepper:
    """Advances one or both cue pointers at a fixed interval on a background thread."""

    def __init__(self, state: PerformanceState, interval_s: float = 10.0,
                 mode: Mode = "both"):
        self._state = state
        self._mode = mode
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def toggle(self) -> None:
        self.stop() if self.running else self.start()

    def _run(self) -> None:
        while not self._stop.wait(self.interval_s):
            if self._mode == "tuning":
                self._state.advance_tuning()
            elif self._mode == "voice":
                self._state.advance_voice()
            else:
                self._state.advance_both()
