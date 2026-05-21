import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from catalog import Catalog

RESOURCES = os.path.join(os.path.dirname(__file__), "..", "resources")


@pytest.fixture(scope="module")
def catalog():
    return Catalog(RESOURCES)


class TestScaleLookup:
    def test_scale_count(self, catalog):
        assert len(catalog.scales) == 178

    def test_lookup_by_name_exact(self, catalog):
        scale = catalog.scale_by_name("SLENDROB3")
        assert scale.name == "SLENDROB3"
        assert scale.index >= 0

    def test_lookup_case_insensitive(self, catalog):
        s1 = catalog.scale_by_name("SLENDROB3")
        s2 = catalog.scale_by_name("slendrob3")
        assert s1.index == s2.index

    def test_lookup_missing_raises(self, catalog):
        with pytest.raises(ValueError, match="Unknown scale"):
            catalog.scale_by_name("DOESNOTEXIST")

    def test_scale_has_six_midi_values(self, catalog):
        scale = catalog.scales[0]
        assert len(scale.midi_values) == 6

    def test_scale_has_six_image_values(self, catalog):
        scale = catalog.scales[0]
        assert len(scale.image_values) == 6

    def test_scale_description_nonempty(self, catalog):
        scale = catalog.scale_by_name("SLENDROB3")
        assert len(scale.description) > 0

    def test_sysex_for_scale(self, catalog):
        scale = catalog.scales[0]
        msgs = catalog.sysex_for_scale(scale.index)
        assert len(msgs) > 0
        for msg in msgs:
            assert msg[0] == 0xF0
            assert msg[-1] == 0xF7


class TestVoiceLookup:
    def test_voice_lookup_pre1(self, catalog):
        voice = catalog.voice_by_name("PRE1", "PowerGrand")
        assert voice.bank == "PRE1"
        assert voice.name == "PowerGrand"
        assert voice.slot == "A01"
        assert voice.index == 0

    def test_voice_lookup_case_insensitive(self, catalog):
        v1 = catalog.voice_by_name("PRE1", "PowerGrand")
        v2 = catalog.voice_by_name("pre1", "powergrand")
        assert v1.index == v2.index

    def test_voice_lookup_missing_raises(self, catalog):
        with pytest.raises(ValueError, match="Unknown voice"):
            catalog.voice_by_name("PRE1", "DOESNOTEXIST")

    def test_unknown_bank_raises(self, catalog):
        with pytest.raises(ValueError, match="Unknown bank"):
            catalog.voice_by_name("BADBANK", "PowerGrand")

    def test_four_token_description(self, catalog):
        # Long_Spit has only 4 tokens (no category_2)
        voice = catalog.voice_by_name("PRE1", "Long_Spit")
        assert voice.category_abbr == "Ba"
        assert voice.category_1 == "SYNTH"
        assert voice.category_2 == ""

    def test_five_token_description(self, catalog):
        # PowerGrand has 5 tokens including "A PIANO"
        voice = catalog.voice_by_name("PRE1", "PowerGrand")
        assert voice.category_abbr == "Ap"
        assert voice.category_1 != ""
        assert voice.category_2 != ""

    def test_voice_count_per_bank(self, catalog):
        for bank in ("PRE1", "PRE2", "PRE3", "USER", "GM"):
            assert len(catalog.voices(bank)) == 128

    def test_sysex_for_voice(self, catalog):
        msgs = catalog.sysex_for_voice("PRE1", 0)
        assert len(msgs) > 0
        for msg in msgs:
            assert msg[0] == 0xF0
            assert msg[-1] == 0xF7
