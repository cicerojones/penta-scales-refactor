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

## UI notes (to revisit after first live render)

- `next:` row currently shows dimmed name only. Could also dim the
  category line — worth checking whether it's too cluttered.

- Tuning "line 2" in the display currently shows the scale description text
  (truncated to 40 chars) rather than a category field, since scales don't
  have the same bank/category structure as voices. May want a different field
  or just nothing there.

- Fixed widget width of 520px may need adjustment depending on browser zoom
  and notebook theme.

- The scale `image_values` field can contain rational fractions (e.g. `9/8`,
  `4/3`) for JI tunings, not just decimals. These display correctly as
  strings but won't sort/compare numerically if that's ever needed.

## Unused resource files (probably safe to ignore)

`penta-scales.txt`, `penta-scales3.txt`, `5-big.txt` through `12-big.txt`,
`double-octave-scales0-999.txt`, `MIDI1-3.txt`, `PRE1-122.txt`,
`PRE1-123.txt`, `two-coll-tunings.txt`, `two-coll-voices.txt`,
`motif-12-31.txt`, `motif-wilson_17.txt`, `notenames.txt`,
`ten-scale-names.txt`, `some-scale.txt`, `a-single-scale.txt`, `coll-baby.txt`
