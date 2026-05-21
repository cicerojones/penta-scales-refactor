from __future__ import annotations

from typing import Callable

from catalog import Catalog, ScaleEntry, VoiceEntry
from cuelist import Cue
from midi import MidiOut


class PerformanceState:
    def __init__(
        self,
        cues: list[Cue],
        catalog: Catalog,
        midi_out: MidiOut,
        on_change: Callable[[], None] | None = None,
    ):
        if not cues:
            raise ValueError("Cue list must not be empty")
        self._cues = cues
        self._catalog = catalog
        self._midi = midi_out
        self._on_change = on_change or (lambda: None)
        self.armed = False
        self.tuning_ptr = 0
        self.voice_ptr = 0

    # ------------------------------------------------------------------ arm

    def arm(self) -> None:
        self.armed = True
        self._notify()

    def disarm(self) -> None:
        self.armed = False
        self._notify()

    # ------------------------------------------------------------------ advance

    def advance_both(self) -> None:
        self.tuning_ptr = (self.tuning_ptr + 1) % len(self._cues)
        self.voice_ptr  = (self.voice_ptr  + 1) % len(self._cues)
        self._send_tuning()
        self._send_voice()
        self._notify()

    def advance_tuning(self) -> None:
        self.tuning_ptr = (self.tuning_ptr + 1) % len(self._cues)
        self._send_tuning()
        self._notify()

    def advance_voice(self) -> None:
        self.voice_ptr = (self.voice_ptr + 1) % len(self._cues)
        self._send_voice()
        self._notify()

    # ------------------------------------------------------------------ jump

    def jump_tuning(self, n: int) -> None:
        self.tuning_ptr = n % len(self._cues)
        self._send_tuning()
        self._notify()

    def jump_voice(self, n: int) -> None:
        self.voice_ptr = n % len(self._cues)
        self._send_voice()
        self._notify()

    # ------------------------------------------------------------------ reset

    def reset(self) -> None:
        """Set both pointers to 0. Does not send."""
        self.tuning_ptr = 0
        self.voice_ptr  = 0
        self._notify()

    # ------------------------------------------------------------------ current / next

    def current_tuning(self) -> ScaleEntry:
        return self._cues[self.tuning_ptr].tuning

    def current_voice(self) -> VoiceEntry:
        return self._cues[self.voice_ptr].voice

    def next_tuning(self) -> ScaleEntry:
        return self._cues[(self.tuning_ptr + 1) % len(self._cues)].tuning

    def next_voice(self) -> VoiceEntry:
        return self._cues[(self.voice_ptr + 1) % len(self._cues)].voice

    @property
    def cue_count(self) -> int:
        return len(self._cues)

    # ------------------------------------------------------------------ internal

    def _send_tuning(self) -> None:
        if not self.armed:
            return
        scale = self.current_tuning()
        msgs = self._catalog.sysex_for_scale(scale.index)
        self._midi.send_sysex(msgs)

    def _send_voice(self) -> None:
        if not self.armed:
            return
        voice = self.current_voice()
        msgs = self._catalog.sysex_for_voice(voice.bank, voice.index)
        self._midi.send_sysex(msgs)

    def _notify(self) -> None:
        self._on_change()
