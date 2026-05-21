import re


def parse_coll_ints(path: str) -> dict[int, list[int]]:
    """Parse a Pd coll file whose values are decimal integers."""
    result = {}
    with open(path) as f:
        text = f.read()
    for match in re.finditer(r'^\s*(\d+)\s*,\s*(.*?)\s*;', text, re.MULTILINE | re.DOTALL):
        key = int(match.group(1))
        result[key] = [int(x) for x in match.group(2).split()]
    return result


def parse_coll_strs(path: str) -> dict[int, list[str]]:
    """Parse a Pd coll file whose values are whitespace-separated tokens (strings)."""
    result = {}
    with open(path) as f:
        text = f.read()
    for match in re.finditer(r'^\s*(\d+)\s*,\s*(.*?)\s*;', text, re.MULTILINE | re.DOTALL):
        key = int(match.group(1))
        # Strip enclosing quotes from individual tokens if present
        tokens = []
        for tok in match.group(2).split():
            tok = tok.strip('"')
            if tok:
                tokens.append(tok)
        result[key] = tokens
    return result


def split_sysex(flat_bytes: list[int]) -> list[bytes]:
    """Split a flat list of decimal bytes into individual sysex messages (240...247)."""
    messages = []
    current: list[int] = []
    for b in flat_bytes:
        if b == 0xF0:  # 240 — sysex start
            current = [b]
        elif b == 0xF7:  # 247 — sysex end
            if current:
                current.append(b)
                messages.append(bytes(current))
                current = []
        elif current:
            current.append(b)
    return messages
