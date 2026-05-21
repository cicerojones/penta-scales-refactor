import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tempfile, textwrap
import pytest
from catalog import Catalog
from cuelist import load_cuelist

RESOURCES = os.path.join(os.path.dirname(__file__), "..", "resources")


@pytest.fixture(scope="module")
def catalog():
    return Catalog(RESOURCES)


def write_csv(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    f.write(content)
    f.flush()
    return f.name


class TestLoadCuelist:
    def test_valid_csv(self, catalog):
        path = write_csv(textwrap.dedent("""\
            tuning,voice
            SLENDROB3,PRE1:PowerGrand
            HIRAJOSHI,PRE2:PWM_Lead
        """))
        cues = load_cuelist(path, catalog)
        assert len(cues) == 2
        assert cues[0].tuning.name == "SLENDROB3"
        assert cues[0].voice.bank == "PRE1"
        assert cues[0].voice.name == "PowerGrand"
        assert cues[1].tuning.name == "HIRAJOSHI"

    def test_case_insensitive_bank(self, catalog):
        path = write_csv("tuning,voice\nSLENDROB3,pre1:PowerGrand\n")
        cues = load_cuelist(path, catalog)
        assert cues[0].voice.bank == "PRE1"

    def test_unknown_tuning_raises_with_row(self, catalog):
        path = write_csv("tuning,voice\nBADSCALE,PRE1:PowerGrand\n")
        with pytest.raises(ValueError, match="Row 2"):
            load_cuelist(path, catalog)

    def test_unknown_voice_raises_with_row(self, catalog):
        path = write_csv("tuning,voice\nSLENDROB3,PRE1:DOESNOTEXIST\n")
        with pytest.raises(ValueError, match="Row 2"):
            load_cuelist(path, catalog)

    def test_missing_colon_raises(self, catalog):
        path = write_csv("tuning,voice\nSLENDROB3,PowerGrand\n")
        with pytest.raises(ValueError, match="BANK:name"):
            load_cuelist(path, catalog)

    def test_empty_file_raises(self, catalog):
        path = write_csv("tuning,voice\n")
        with pytest.raises(ValueError, match="empty"):
            load_cuelist(path, catalog)
