import os
from dataclasses import dataclass

from coll import parse_coll_ints, parse_coll_strs, split_sysex


@dataclass
class ScaleEntry:
    index: int
    name: str
    description: str
    midi_values: list[float]   # 6 values: root, 4 degrees, octave
    image_values: list[str]    # 6 values: root, 4 degrees, octave (cents or ratios)
    provenance: str = ""       # comment line from the .scl source file


@dataclass
class VoiceEntry:
    bank: str           # "PRE1", "PRE2", "PRE3", "USER", "GM"
    index: int          # 0-based within bank
    slot: str           # e.g. "A43"
    name: str           # e.g. "Long_Spit"
    category_abbr: str  # e.g. "Ba"
    category_1: str     # e.g. "SYNTH"
    category_2: str     # e.g. "BASS" (empty string if absent)


_BANKS = ("PRE1", "PRE2", "PRE3", "USER", "GM")

# Framing messages required by the Motif to open and commit a sysex bulk dump.
# Source: pentatonic-motif-scales.pd → hide-scale-message subpatch;
#         my-seqer.pd → send-midi-messages → hide-coll (voice bank).
_SYSEX_OPEN  = bytes([240, 67, 0, 107, 0, 0, 14, 47, 0, 67, 247])
_SYSEX_CLOSE = bytes([240, 67, 0, 107, 0, 0, 15, 47, 0, 66, 247])

_SYSEX_FILES = {
    "PRE1": "PRE1-voices.txt",
    "PRE2": "PRE2-voices.txt",
    "PRE3": "PRE3-voices.txt",
    "USER": "USER-voices.txt",
    "GM":   "GM-voices.txt",
}

_DESC_FILES = {
    "PRE1": "pre1-voice-descriptions.txt",
    "PRE2": "pre2-voice-descriptions.txt",
    "PRE3": "pre3-voice-descriptions.txt",
    "USER": "user-voice-descriptions.txt",
    "GM":   "gm-voice-descriptions.txt",
}


class Catalog:
    def __init__(self, resources_dir: str):
        self._dir = resources_dir
        self._scales: list[ScaleEntry] = []
        self._scale_by_name: dict[str, ScaleEntry] = {}
        self._scale_sysex: dict[int, list[bytes]] = {}

        self._voices: dict[str, list[VoiceEntry]] = {}
        self._voice_by_name: dict[str, dict[str, VoiceEntry]] = {}
        self._voice_sysex: dict[str, dict[int, list[bytes]]] = {}

        self._load_scales()
        self._load_voices()

    # ------------------------------------------------------------------ scales

    @staticmethod
    def _read_scl_provenance(scl2_dir: str, name: str) -> str:
        stem = name.lower()
        for candidate in (stem, stem.replace("_", " ")):
            path = os.path.join(scl2_dir, candidate + ".scl")
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                if len(lines) >= 3:
                    return lines[2].strip()
            except FileNotFoundError:
                pass
        return ""

    def _load_scales(self):
        p = lambda f: os.path.join(self._dir, f)
        scl2_dir = os.path.join(self._dir, "scl2")

        names = parse_coll_strs(p("penta-scales-names.txt"))
        descs = parse_coll_strs(p("penta-scales-desc.txt"))
        data  = parse_coll_strs(p("penta-scale-data.txt"))
        image = parse_coll_strs(p("penta-scale-image.txt"))
        sysex_raw = parse_coll_ints(p("penta-scales2.txt"))

        for idx in sorted(names):
            name = names[idx][0] if names[idx] else ""
            desc = descs.get(idx, [""])[0]
            midi_vals = [float(v) for v in data.get(idx, [])]
            img_vals  = list(image.get(idx, []))

            entry = ScaleEntry(
                index=idx,
                name=name,
                description=desc,
                midi_values=midi_vals,
                image_values=img_vals,
                provenance=self._read_scl_provenance(scl2_dir, name),
            )
            self._scales.append(entry)
            self._scale_by_name[name.upper()] = entry
            if idx in sysex_raw:
                self._scale_sysex[idx] = split_sysex(sysex_raw[idx])

    # ------------------------------------------------------------------ voices

    def _load_voices(self):
        p = lambda f: os.path.join(self._dir, f)

        for bank in _BANKS:
            sysex_raw = parse_coll_ints(p(_SYSEX_FILES[bank]))
            # description files are 1-indexed; subtract 1 to align with sysex
            raw_descs = parse_coll_strs(p(_DESC_FILES[bank]))
            descs = {k - 1: v for k, v in raw_descs.items()}

            entries: list[VoiceEntry] = []
            by_name: dict[str, VoiceEntry] = {}
            sysex_map: dict[int, list[bytes]] = {}

            for idx in sorted(sysex_raw):
                tokens = descs.get(idx, [])
                slot        = tokens[0] if len(tokens) > 0 else ""
                name        = tokens[1] if len(tokens) > 1 else ""
                cat_abbr    = tokens[2] if len(tokens) > 2 else ""
                cat_1       = tokens[3] if len(tokens) > 3 else ""
                cat_2       = tokens[4] if len(tokens) > 4 else ""

                entry = VoiceEntry(
                    bank=bank,
                    index=idx,
                    slot=slot,
                    name=name,
                    category_abbr=cat_abbr,
                    category_1=cat_1,
                    category_2=cat_2,
                )
                entries.append(entry)
                if name:
                    by_name[name.upper()] = entry
                sysex_map[idx] = split_sysex(sysex_raw[idx])

            self._voices[bank] = entries
            self._voice_by_name[bank] = by_name
            self._voice_sysex[bank] = sysex_map

    # ------------------------------------------------------------------ lookups

    def scale_by_name(self, name: str) -> ScaleEntry:
        key = name.strip().upper()
        if key not in self._scale_by_name:
            raise ValueError(f"Unknown scale: {name!r}")
        return self._scale_by_name[key]

    def voice_by_name(self, bank: str, name: str) -> VoiceEntry:
        bank_key = bank.strip().upper()
        name_key = name.strip().upper()
        bank_map = self._voice_by_name.get(bank_key)
        if bank_map is None:
            raise ValueError(f"Unknown bank: {bank!r}. Valid banks: {list(_BANKS)}")
        if name_key not in bank_map:
            raise ValueError(f"Unknown voice {name!r} in bank {bank!r}")
        return bank_map[name_key]

    def sysex_for_scale(self, index: int) -> list[bytes]:
        if index not in self._scale_sysex:
            raise ValueError(f"No sysex data for scale index {index}")
        return [_SYSEX_OPEN] + self._scale_sysex[index] + [_SYSEX_CLOSE]

    def sysex_for_voice(self, bank: str, voice_index: int) -> list[bytes]:
        bank_key = bank.strip().upper()
        bank_map = self._voice_sysex.get(bank_key)
        if bank_map is None:
            raise ValueError(f"Unknown bank: {bank!r}")
        if voice_index not in bank_map:
            raise ValueError(f"No sysex data for voice index {voice_index} in bank {bank!r}")
        return [_SYSEX_OPEN] + bank_map[voice_index] + [_SYSEX_CLOSE]

    # ------------------------------------------------------------------ accessors

    @property
    def scales(self) -> list[ScaleEntry]:
        return list(self._scales)

    def voices(self, bank: str) -> list[VoiceEntry]:
        return list(self._voices.get(bank.upper(), []))
