# Pd Tuning App — Python Rewrite Plan

## What this is

A Python/ipywidgets control surface replacing `my-seqer.pd`. Sends sysex
messages to a Yamaha Motif to change tuning and program (voice). No audio
output. Cue list defined in a CSV file, advanced manually at musically
appropriate moments.

## Status

Core implementation complete. 47 tests passing.

## Architecture

```
src/
  coll.py       Pd coll file parser + sysex byte-list splitter
  catalog.py    Loads resources/ at startup; ScaleEntry/VoiceEntry dataclasses;
                name→index lookups; pre-split sysex storage
  cuelist.py    Parses CSV cue list; resolves BANK:name references
  midi.py       Thin mido wrapper — send_sysex only
  state.py      PerformanceState: arm toggle, two independent pointers,
                advance/jump/reset, on_change callback
  ui.py         ipywidgets layout
tests/          47 unit tests (no MIDI hardware required)
example_cuelist.csv
notebook.ipynb  Config cell → port listing cell → display(widget)
```

## Interaction model

Two independent pointers (`tuning_ptr`, `voice_ptr`) into a CSV-defined cue
list. Three advance actions:

| Button | Effect |
|---|---|
| Advance Both | both pointers +1, sends both if armed |
| Adv Tuning | tuning pointer +1 only |
| Adv Voice | voice pointer +1 only |

Independent advance supports combinatorial use: hold a tuning while stepping
through voices, or vice versa, without needing every combination in the CSV.

All sends are gated by a single arm/disarm toggle. Jump spinners allow direct
pointer positioning. Reset zeros both without sending.

## CSV format

```csv
tuning,voice
SLENDROB3,PRE2:Airy_Nylon
PELOG17,USER:BrokenStar
```

- `tuning` — all-caps scale name from `resources/penta-scales-names.txt`
- `voice` — `BANK:Name` where bank is one of PRE1/PRE2/PRE3/USER/GM and
  name is the second field from the corresponding
  `resources/<bank>-voice-descriptions.txt`

Names are case-insensitive. Underscore is significant (e.g. `Airy_Nylon`
not `AiryNylon`). Row number is included in error messages on bad names.

## Resource files used

| File | Content |
|---|---|
| `penta-scales2.txt` | tuning sysex bytes, 178 entries, 0-indexed |
| `penta-scales-names.txt` | short scale names |
| `penta-scales-desc.txt` | scale descriptions |
| `penta-scale-data.txt` | 6 MIDI pitch values per scale |
| `penta-scale-image.txt` | 6 cent/ratio values per scale |
| `PRE1/PRE2/PRE3/USER/GM-voices.txt` | voice sysex bytes, 128 per bank |
| `pre1/pre2/pre3/user/gm-voice-descriptions.txt` | 5-field voice metadata |

`penta-scales.txt` (no number) is present but unused — active file is
`penta-scales2.txt`.

## Deferred / future work

- **Wilson scales** — `three-coll-tunings.txt` (Wilson 17, 31, 41) can be
  added as a fourth coll source; out of scope for v1
- **UI layout tuning** — some details (field widths, color contrast, label
  truncation) are only apparent when rendered in a live notebook
- **Logic Pro transport integration** — explicitly out of scope
- **Keyboard shortcuts** — could bind advance actions to keys via ipyevents
