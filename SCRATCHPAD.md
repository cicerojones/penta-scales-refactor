# Scratchpad

## Data quirks to be aware of

- Several voice description entries have a trailing integer as a 5th field,
  e.g. `Pd  BRIGHT  72`. This appears to be a 0-based voice index used as a
  cross-reference in the original Pd patch. The catalog stores it as
  `category_2`; the UI displays it literally. Harmless but looks odd.

- Voice description files are 1-indexed (keys 1–128) while sysex files are
  0-indexed (keys 0–127). The catalog applies `key - 1` at load time.

- `AiryNYlon` appears in the Pd patch's hardcoded favorites list but the
  actual name in the description file is `Airy_Nylon` (PRE2, index 91).

- `penta-scales.txt` exists in resources/ alongside `penta-scales2.txt`.
  The patch only reads the `2` version. Relationship between the two unknown.

## Open questions

- Is the `penta-scales.txt` file an older/alternate tuning set, or is it a
  duplicate? Worth diffing the two if switching tuning banks becomes needed.

- The `three-coll-tunings.txt` file holds Wilson 17, 31, 41 scales. These
  were accessible in the original patch via a separate `other-scales`
  subpatch. Adding a `WILSON` bank or a separate coll source is
  straightforward when needed.

- Some voice names likely appear in multiple banks (not verified). The
  `BANK:name` syntax in the CSV handles this unambiguously.

- MIDI port name on the target machine is unknown — needs to be filled in at
  `MIDI_PORT` in cell 1 of the notebook, or left `None` to auto-select first
  port.

## UI notes

- Tuning "line 2" shows scale description text (truncated to 40 chars).
  No clean category equivalent for scales — may want to drop it or show
  image_values[0] (the 1/1 ratio) as a hint about the tonal system instead.

- The scale `image_values` field can contain rational fractions (e.g. `9/8`,
  `4/3`) for JI tunings. Displays correctly as strings; not numerically comparable.

- Fixed widget width of 560px. May need adjustment for different browser zoom
  or notebook themes.

- category_2 on voice entries sometimes contains a stray integer (e.g. `72`),
  a 0-based cross-reference from the original Pd patch. Stored and displayed
  literally; harmless but potentially confusing in the UI.

## In-progress / soon

### Cuelist generator — next capabilities
The filter+weight approach is in place. Likely next steps:

- **Scale family helpers**: convenience wrappers that group scales by
  cultural/tonal family (Gamelan, Mbira, Harrison, Slendro variants, etc.)
  so the generator cell reads `gamelan_scales` rather than a long `contains`
  list. These could live as constants or functions in `cuelist_gen.py`.

- **Constraint pairing**: some musical contexts want to pair a scale family
  with a matching timbral category (e.g. Gamelan scales → mallet/bell voices,
  Mbira scales → pluck voices). A `constrained_pairs(rules)` function could
  express this as a list of `(scale_filter, voice_filter, weight)` tuples
  and produce a weighted-random mix across multiple constraint groups.

- **Anchor cues**: ability to fix certain (tuning, voice) pairs at specific
  positions and fill the rest randomly — useful for pieces with a known
  opening and closing but a generative middle section.

### Autostep — possible refinements
- **Humanize**: add optional jitter (`± N seconds`) to the interval so the
  advance doesn't feel metronomic. Small random offset drawn each cycle.
- **Count-based stopping**: stop after N advances rather than running until
  manually toggled off.
- **Sync to manual**: reset the autostep timer whenever a manual advance
  fires, so manual and auto don't pile up.

### Wilson scales
`three-coll-tunings.txt` holds Wilson 17, 31, 41 scales. The original patch
accessed them via a separate `other-scales` subpatch with hardcoded sysex.
Adding them as a second `Catalog` source or a new bank is straightforward;
blocked only on deciding whether to expose them through the same scale-name
lookup or as a separate pool.

## Unused resource files (probably safe to ignore)

`penta-scales.txt`, `penta-scales3.txt`, `5-big.txt` through `12-big.txt`,
`double-octave-scales0-999.txt`, `MIDI1-3.txt`, `PRE1-122.txt`,
`PRE1-123.txt`, `two-coll-tunings.txt`, `two-coll-voices.txt`,
`motif-12-31.txt`, `motif-wilson_17.txt`, `notenames.txt`,
`ten-scale-names.txt`, `some-scale.txt`, `a-single-scale.txt`, `coll-baby.txt`
