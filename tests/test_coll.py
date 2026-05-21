import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tempfile, textwrap
import pytest
from coll import parse_coll_ints, parse_coll_strs, split_sysex


SAMPLE_INTS = textwrap.dedent("""\
    0, 240 67 0 247 240 67 1 247 ;
    1, 10 20 30 ;
    2, 255 ;
""")

SAMPLE_STRS = textwrap.dedent("""\
       0, SCALE_A;
       1, Desc_with_underscores;
       2, A01  PowerGrand  Ap  A  PIANO ;
""")


def write_tmp(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    f.write(content)
    f.flush()
    return f.name


class TestParseCollInts:
    def test_keys_and_values(self):
        path = write_tmp(SAMPLE_INTS)
        result = parse_coll_ints(path)
        assert set(result.keys()) == {0, 1, 2}
        assert result[1] == [10, 20, 30]
        assert result[2] == [255]

    def test_sysex_bytes_in_value(self):
        path = write_tmp(SAMPLE_INTS)
        result = parse_coll_ints(path)
        assert result[0] == [240, 67, 0, 247, 240, 67, 1, 247]

    def test_leading_whitespace_on_key(self):
        content = "   5, 1 2 3 ;\n"
        path = write_tmp(content)
        result = parse_coll_ints(path)
        assert 5 in result
        assert result[5] == [1, 2, 3]


class TestParseCollStrs:
    def test_single_token(self):
        path = write_tmp(SAMPLE_STRS)
        result = parse_coll_strs(path)
        assert result[0] == ["SCALE_A"]
        assert result[1] == ["Desc_with_underscores"]

    def test_five_tokens(self):
        path = write_tmp(SAMPLE_STRS)
        result = parse_coll_strs(path)
        assert result[2] == ["A01", "PowerGrand", "Ap", "A", "PIANO"]

    def test_strips_quotes(self):
        content = '0, "quoted_string" ;\n'
        path = write_tmp(content)
        result = parse_coll_strs(path)
        assert result[0] == ["quoted_string"]


class TestSplitSysex:
    def test_single_message(self):
        flat = [240, 67, 0, 12, 247]
        msgs = split_sysex(flat)
        assert len(msgs) == 1
        assert msgs[0] == bytes([240, 67, 0, 12, 247])

    def test_two_messages(self):
        flat = [240, 1, 247, 240, 2, 247]
        msgs = split_sysex(flat)
        assert len(msgs) == 2
        assert msgs[0] == bytes([240, 1, 247])
        assert msgs[1] == bytes([240, 2, 247])

    def test_empty_input(self):
        assert split_sysex([]) == []

    def test_incomplete_message_ignored(self):
        # Bytes after a 240 without 247 are not emitted
        flat = [240, 1, 2]
        assert split_sysex(flat) == []
