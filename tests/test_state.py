import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from catalog import Catalog
from cuelist import load_cuelist, Cue
from state import PerformanceState

RESOURCES = os.path.join(os.path.dirname(__file__), "..", "resources")


class MockMidiOut:
    def __init__(self):
        self.sent: list[list[bytes]] = []

    def send_sysex(self, messages):
        self.sent.append(messages)


@pytest.fixture(scope="module")
def catalog():
    return Catalog(RESOURCES)


@pytest.fixture
def three_cues(catalog):
    scale_names = ["SLENDROB3", "HIRAJOSHI", "PELOG17"]
    voice_refs  = [("PRE1", "PowerGrand"), ("PRE1", "Jazz_Grand"), ("PRE1", "Dark_Grand")]
    return [
        Cue(tuning=catalog.scale_by_name(s), voice=catalog.voice_by_name(b, v))
        for s, (b, v) in zip(scale_names, voice_refs)
    ]


@pytest.fixture
def state(catalog, three_cues):
    midi = MockMidiOut()
    return PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)


class TestArm:
    def test_starts_disarmed(self, state):
        assert not state.armed

    def test_arm_disarm(self, state):
        state.arm()
        assert state.armed
        state.disarm()
        assert not state.armed


class TestAdvance:
    def test_advance_both_increments_both(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.advance_both()
        assert s.tuning_ptr == 1
        assert s.voice_ptr  == 1

    def test_advance_tuning_only(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.advance_tuning()
        assert s.tuning_ptr == 1
        assert s.voice_ptr  == 0

    def test_advance_voice_only(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.advance_voice()
        assert s.tuning_ptr == 0
        assert s.voice_ptr  == 1

    def test_wrap_around(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        for _ in range(3):
            s.advance_both()
        assert s.tuning_ptr == 0
        assert s.voice_ptr  == 0

    def test_independent_wrap(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.advance_tuning()
        s.advance_tuning()
        s.advance_tuning()   # wraps back to 0
        s.advance_voice()    # voice at 1
        assert s.tuning_ptr == 0
        assert s.voice_ptr  == 1


class TestSendGating:
    def test_no_send_when_disarmed(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.advance_both()
        s.advance_tuning()
        s.advance_voice()
        assert midi.sent == []

    def test_sends_when_armed(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.arm()
        s.advance_both()
        assert len(midi.sent) == 2   # one tuning send + one voice send


class TestJump:
    def test_jump_tuning(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.jump_tuning(2)
        assert s.tuning_ptr == 2
        assert s.voice_ptr  == 0

    def test_jump_voice(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.jump_voice(2)
        assert s.voice_ptr  == 2
        assert s.tuning_ptr == 0

    def test_jump_wraps(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.jump_tuning(99)
        assert s.tuning_ptr == 99 % 3


class TestReset:
    def test_reset_zeros_both(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.advance_both()
        s.advance_tuning()
        s.reset()
        assert s.tuning_ptr == 0
        assert s.voice_ptr  == 0

    def test_reset_does_not_send(self, catalog, three_cues):
        midi = MockMidiOut()
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi)
        s.arm()
        s.reset()
        assert midi.sent == []


class TestOnChange:
    def test_on_change_fires_on_every_mutation(self, catalog, three_cues):
        midi = MockMidiOut()
        calls = []
        s = PerformanceState(cues=three_cues, catalog=catalog, midi_out=midi,
                             on_change=lambda: calls.append(1))
        s.arm()
        s.advance_both()
        s.advance_tuning()
        s.advance_voice()
        s.jump_tuning(0)
        s.reset()
        s.disarm()
        assert len(calls) == 7
