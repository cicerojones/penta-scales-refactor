"""
Programmatic cuelist generation.

Typical notebook usage:

    from cuelist_gen import filter_scales, filter_voices, generate_cuelist, write_cuelist
    from cuelist import load_cuelist

    scales = filter_scales(catalog, contains=['DEGUNG', 'PELOG', 'SLENDRO'])
    voices = filter_voices(catalog, banks=['PRE2'], category_abbr=['Pd', 'St'])
    pairs  = generate_cuelist(scales, voices, n=20, seed=42)
    write_cuelist(CUELIST_PATH, pairs)
    state.reload(load_cuelist(CUELIST_PATH, catalog))

category_abbr reference (from resources):
    Ap  acoustic piano     Pd  pad          St  strings
    Br  brass              Or  organ        Gt  guitar
    Ba  bass               Ld  lead         Cp  chromatic perc
    Se  sound effect       Kb  keyboard     Ens ensemble
    Dr  drums/percussion   Co  combo        Me  melodic

category_1 reference (selected):
    A  A.PIANO    E.PIANO   SYNTH    CHOIR
    STRINGS  BRASS  E.GUITAR  A.GUITAR  E.BASS  A.BASS
    BELL  MALLET  PLUCK  PIPE  SAX/REED  ENSEMBLE
"""

from __future__ import annotations

import csv
import random

from catalog import Catalog, ScaleEntry, VoiceEntry


def filter_scales(
    catalog: Catalog,
    *,
    contains: str | list[str] | None = None,
) -> list[ScaleEntry]:
    """Return scales whose names contain any of the given substrings (case-insensitive).

    Pass a single string or a list for OR matching:
        filter_scales(catalog, contains='DEGUNG')
        filter_scales(catalog, contains=['DEGUNG', 'PELOG', 'SLENDRO'])
    """
    scales = catalog.scales
    if contains is None:
        return scales
    patterns = [contains] if isinstance(contains, str) else list(contains)
    patterns = [p.upper() for p in patterns]
    return [s for s in scales if any(p in s.name.upper() for p in patterns)]


def filter_voices(
    catalog: Catalog,
    *,
    banks: list[str] | None = None,
    category_abbr: str | list[str] | None = None,
    category_1: str | list[str] | None = None,
) -> list[VoiceEntry]:
    """Return voices matching bank and/or category constraints.

    banks: subset of ["PRE1","PRE2","PRE3","USER","GM"]; None = all banks.
    category_abbr: exact match(es) against the short code (Ap, Pd, St, Br, ...).
    category_1: substring match(es) against the long category (PIANO, SYNTH, ...).

    Both filters are ANDed; within each filter, multiple values are ORed.
    """
    target_banks = banks if banks is not None else ["PRE1", "PRE2", "PRE3", "USER", "GM"]
    voices: list[VoiceEntry] = []
    for bank in target_banks:
        voices.extend(catalog.voices(bank))

    if category_abbr is not None:
        abbrs = {category_abbr} if isinstance(category_abbr, str) else set(category_abbr)
        voices = [v for v in voices if v.category_abbr in abbrs]

    if category_1 is not None:
        patterns = [category_1] if isinstance(category_1, str) else list(category_1)
        patterns = [p.upper() for p in patterns]
        voices = [v for v in voices if any(p in v.category_1.upper() for p in patterns)]

    return voices


def generate_cuelist(
    scales: list[ScaleEntry],
    voices: list[VoiceEntry],
    *,
    n: int | None = None,
    strategy: str = "random",
    weights_s: list[float] | None = None,
    weights_v: list[float] | None = None,
    seed: int | None = None,
) -> list[tuple[ScaleEntry, VoiceEntry]]:
    """Produce a list of (ScaleEntry, VoiceEntry) pairs.

    strategy:
        "random"        – sample n pairs with replacement (default n = len(scales))
        "cross_product" – every scale × every voice; n randomly trims if given
        "zip"           – scales[i] paired with voices[i % len(voices)]; n trims

    weights_s / weights_v: relative weights for random sampling.
        Pass a list the same length as scales/voices to bias selection.
        Example: double the chance of the first scale —
            weights_s = [2] + [1] * (len(scales) - 1)

    seed: integer for reproducible output; None for a new random sequence each call.
    """
    if not scales:
        raise ValueError("scales list is empty after filtering")
    if not voices:
        raise ValueError("voices list is empty after filtering")

    rng = random.Random(seed)

    if strategy == "cross_product":
        pairs = [(s, v) for s in scales for v in voices]
        if n is not None:
            rng.shuffle(pairs)
            return pairs[:n]
        return pairs

    if strategy == "zip":
        length = n if n is not None else max(len(scales), len(voices))
        return [
            (scales[i % len(scales)], voices[i % len(voices)])
            for i in range(length)
        ]

    # "random"
    length = n if n is not None else len(scales)
    chosen_s = rng.choices(scales, weights=weights_s, k=length)
    chosen_v = rng.choices(voices, weights=weights_v, k=length)
    return list(zip(chosen_s, chosen_v))


def write_cuelist(path: str, pairs: list[tuple[ScaleEntry, VoiceEntry]]) -> None:
    """Write pairs to a CSV file loadable by load_cuelist()."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tuning", "voice"])
        for scale, voice in pairs:
            writer.writerow([scale.name, f"{voice.bank}:{voice.name}"])
