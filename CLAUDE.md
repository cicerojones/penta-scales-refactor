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

- Python 3.x (compatible with older macOS)
- `mido` or `python-rtmidi` for MIDI/sysex sending
- `ipywidgets` for UI (target environment: Jupyter notebook)
- Cue list format: CSV or org-table (TBD — ask user)

## Known deferred problems

- Tuning changes interrupting mid-sequence playback: **out of scope for v1**.
  The user controls timing manually; the tool does not attempt to solve this.
- Integration with Logic Pro transport: **future project**
- Visual patch-like frontend (beyond ipywidgets): **future project**

## What to ask the user before writing code

1. What is the exact format of the on-disk byte sequence files?
2. Preferred cue list format: CSV, org-table, or something else?
3. Which MIDI library has already been tested on their machines: mido or python-rtmidi?
4. Should tuning and program advance together (single cue pointer) or independently?

## User context

- Works primarily in Emacs + Org-mode
- Multiple machines running older versions of macOS
- Fluent in Lisp (Common Lisp, Clojure); relatively new to Claude Code
- Domain expert in microtonality and Scala tuning systems — do not over-explain
  these concepts
- Prefers top-down, clearly structured code over incremental bottom-up growth
- Score/positional thinking about musical time, not CPU-clock thinking
