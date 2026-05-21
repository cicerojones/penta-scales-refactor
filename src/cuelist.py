import csv
from dataclasses import dataclass

from catalog import Catalog, ScaleEntry, VoiceEntry


@dataclass
class Cue:
    tuning: ScaleEntry
    voice: VoiceEntry


def load_cuelist(path: str, catalog: Catalog) -> list[Cue]:
    """
    Parse a CSV cue list with columns 'tuning' and 'voice'.

    tuning: scale name (case-insensitive), e.g. SLENDROB3
    voice:  BANK:name (case-insensitive), e.g. PRE1:AiryNYlon

    Raises ValueError with row number if any name cannot be resolved.
    """
    cues: list[Cue] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # row 1 is header
            tuning_name = row.get("tuning", "").strip()
            voice_ref   = row.get("voice", "").strip()

            if not tuning_name or not voice_ref:
                raise ValueError(
                    f"Row {row_num}: both 'tuning' and 'voice' columns are required"
                )

            if ":" not in voice_ref:
                raise ValueError(
                    f"Row {row_num}: voice must be BANK:name (e.g. PRE1:AiryNYlon), "
                    f"got {voice_ref!r}"
                )

            bank, voice_name = voice_ref.split(":", 1)

            try:
                tuning = catalog.scale_by_name(tuning_name)
            except ValueError as e:
                raise ValueError(f"Row {row_num}: {e}") from None

            try:
                voice = catalog.voice_by_name(bank, voice_name)
            except ValueError as e:
                raise ValueError(f"Row {row_num}: {e}") from None

            cues.append(Cue(tuning=tuning, voice=voice))

    if not cues:
        raise ValueError(f"Cue list {path!r} is empty")

    return cues
