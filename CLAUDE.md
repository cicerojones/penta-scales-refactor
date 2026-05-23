# CLAUDE.md — Pd Tuning App Refactoring

## Project summary

Rewrite an existing Pure Data patch as a Python tool with an ipywidgets UI.
The patch sends sysex messages to a Yamaha Motif synthesizer to change tunings
and programs. This is a proof-of-concept for managing creative coding projects
with Claude Code.

## What this tool does

A control surface — it sends MIDI/sysex messages to the Motif but does not
play anything back. Playback happens separately (Logic Pro or by hand).

Two send streams, each triggered independently:

- **Tuning sends**: reads a byte sequence from disk, sends a sysex re-tuning
  message to the Motif, displays the tuning name and relevant details
- **Program sends**: reads a byte sequence from disk, sends a sysex voice/program
  message to the Motif, displays the instrument name and relevant details

The two streams are semi-independent: tuning and program can advance on
separate cue pointers, or together.

## Core interaction model

The central abstraction is a **cue list**: an ordered sequence of (tuning,
program) pairs defined in advance by the user. The user advances through cues
manually at musically appropriate moments. The tool does not attempt to
synchronize with Logic Pro's transport or any external clock.

```
Cue 1: tuning=pentatonic_03  program=strings_bright
Cue 2: tuning=pentatonic_03  program=brass_muted     # same tuning, new program
Cue 3: tuning=pentatonic_17  program=brass_muted     # new tuning, same program
```

Cue lists are defined in a plain text file (CSV or org-table format) edited in
Emacs. The Python tool reads this file at startup (and optionally on reload).

## What "systematic" means here

The original Pd patch had no master controls — metro objects were not linked to
a single on/off switch, and timing was ad hoc. The rewrite should have:

- A single "arm/disarm" toggle governing all sends
- Clear current-cue and next-cue display at all times
- Explicit "advance" trigger (button or keystroke)
- Optional separate advance controls for tuning and program independently
- Reset / jump-to-cue controls

## Hardware context

- **Target device**: Yamaha Motif (2000s era)
- **Connection**: MIDI via sysex messages (not standard program change messages)
- **Byte sequences**: stored as files on disk, generated previously from Scala
  and Common Lisp tuning tools. Do not regenerate these — treat them as
  read-only input data.
- **No audio output**: the tool is purely a controller

## Tech stack

- Python 3.11 (target; runtime machine is macOS Catalina with Homebrew Python)
- `mido` (rtmidi backend) for MIDI/sysex sending
- `ipywidgets` for UI (Jupyter notebook)
- Cue list format: CSV (`tuning,BANK:voice`)

## Current file structure

```
src/
  coll.py          parse Pd coll format; split_sysex
  catalog.py       Catalog, ScaleEntry, VoiceEntry; sysex lookups
  cuelist.py       load_cuelist; Cue dataclass
  cuelist_gen.py   filter_scales, filter_voices, generate_cuelist, write_cuelist
  midi.py          MidiOut wrapper (20 ms inter-message delay for DIN MIDI)
  state.py         PerformanceState; arm/advance/jump/reset/reload
  autostepper.py   AutoStepper(state, interval_s, mode); daemon thread
  ui.py            build_ui → ipywidgets layout
tests/
  test_coll.py  test_catalog.py  test_cuelist.py  test_state.py   (47 tests)
notebook.ipynb   cells: config | port check | main widget | cuelist generator
example_cuelist.csv
```

## Critical sysex detail

Every bulk sysex send (tuning or voice) must be wrapped with two Motif
framing messages discovered in the original Pd patch subpatches:

- **Open**:  `F0 43 00 6B 00 00 0E 47 00 43 F7`
- **Close**: `F0 43 00 6B 00 00 0F 47 00 42 F7`

`catalog.sysex_for_scale()` and `catalog.sysex_for_voice()` both prepend/
append these automatically. Do not remove them.

## Autostep

Two independent `AutoStepper` instances (tuning, voice) live inside
`build_ui`. Each has its own toggle button and interval spinner in the UI.
`mode` parameter: `"tuning"`, `"voice"`, or `"both"`. The thread is
`daemon=True` and advances the state on a background thread; ipywidgets
handles cross-thread display updates.

## Cuelist generation

`cuelist_gen.py` provides:
- `filter_scales(catalog, contains=...)` — name substring filter
- `filter_voices(catalog, banks=..., category_abbr=..., category_1=...)` — bank/category filter
- `generate_cuelist(scales, voices, n, strategy, weights_s, weights_v, seed)`
  strategies: `"random"` (default), `"cross_product"`, `"zip"`
- `write_cuelist(path, pairs)` — CSV output

`state.reload(cues)` hot-swaps the cue list without restarting the widget.
The generator notebook cell uses `try/except NameError` to work both before
and after the main cell has been run.

## Known deferred problems

- Timing delay (`_INTER_MSG_DELAY = 0.020` in `midi.py`) may be unnecessary
  now that the sysex framing is correct — worth testing with `0` once stable.
- Integration with Logic Pro transport: **future project**
- Wilson 17/31/41 scales (`three-coll-tunings.txt`) not yet wired in;
  straightforward to add as a separate bank when needed.

## User context

- Works primarily in Emacs + Org-mode
- Multiple machines running older versions of macOS
- Fluent in Lisp (Common Lisp, Clojure); relatively new to Claude Code
- Domain expert in microtonality and Scala tuning systems — do not over-explain
  these concepts
- Prefers top-down, clearly structured code over incremental bottom-up growth
- Score/positional thinking about musical time, not CPU-clock thinking
