from __future__ import annotations

import ipywidgets as w
from IPython.display import display

from catalog import ScaleEntry, VoiceEntry
from midi import MidiOut
from state import PerformanceState

# ------------------------------------------------------------------ helpers

_DIM   = "color: #888888;"
_BOLD  = "font-weight: bold;"
_MONO  = "font-family: monospace;"
_ARM_ON  = "background-color: #2e7d32; color: white; font-weight: bold;"
_ARM_OFF = "background-color: #c62828; color: white; font-weight: bold;"


def _scale_table(scale: ScaleEntry) -> str:
    midi = scale.midi_values
    img  = scale.image_values

    _HDR = "color:#888;padding-right:10px;font-family:monospace"
    _VAL = "text-align:right;padding:0 6px;font-family:monospace"
    _OCT = "text-align:right;padding:0 6px;font-family:monospace;color:#888"

    def td(content, style=_VAL):
        return f'<td style="{style}">{content}</td>'

    midi_cells = "".join(td(f"{v:.2f}") for v in midi[:5])
    oct_midi   = td(f"({midi[5]:.1f})", _OCT) if len(midi) > 5 else ""
    img_cells  = "".join(td(v) for v in img[:5])
    oct_img    = td(img[5], _OCT) if len(img) > 5 else ""

    row1 = f"<tr>{td('midi', _HDR)}{midi_cells}{oct_midi}</tr>"
    row2 = f"<tr>{td('', _HDR)}{img_cells}{oct_img}</tr>"
    return f'<table style="border-collapse:collapse;margin:4px 0">{row1}{row2}</table>'


def _voice_line2(voice: VoiceEntry) -> str:
    parts = [voice.category_abbr, voice.category_1]
    if voice.category_2:
        parts.append(voice.category_2)
    return " / ".join(p for p in parts if p)


# ------------------------------------------------------------------ builder

def build_ui(state: PerformanceState, midi_out: MidiOut) -> w.Widget:
    # -- port selector
    ports = MidiOut.list_ports()
    port_dropdown = w.Dropdown(
        options=ports,
        value=midi_out.port_name if midi_out.port_name in ports else (ports[0] if ports else None),
        description="MIDI port:",
        style={"description_width": "80px"},
        layout=w.Layout(width="420px"),
    )

    def on_port_change(change):
        try:
            midi_out.set_port(change["new"])
            port_dropdown.style.description_color = ""
        except Exception as exc:
            port_dropdown.style.description_color = "red"
            print(f"Failed to open port {change['new']!r}: {exc}")

    port_dropdown.observe(on_port_change, names="value")

    # -- arm toggle (plain Button; we track toggle state via state.armed)
    arm_btn = w.Button(
        description="DISARMED",
        layout=w.Layout(width="160px", height="40px"),
    )
    arm_btn.style.button_color = "#c62828"

    # -- tuning display
    t_now_name  = w.HTML()
    t_now_cat   = w.HTML()
    t_next_name = w.HTML()
    t_next_cat  = w.HTML()

    # -- voice display
    v_now_name  = w.HTML()
    v_now_cat   = w.HTML()
    v_next_name = w.HTML()
    v_next_cat  = w.HTML()

    # -- scale data table
    scale_table = w.HTML()

    # -- control buttons
    adv_both    = w.Button(description="Advance Both",   layout=w.Layout(width="140px"))
    adv_tuning  = w.Button(description="Adv Tuning",    layout=w.Layout(width="120px"))
    adv_voice   = w.Button(description="Adv Voice",     layout=w.Layout(width="120px"))
    reset_btn   = w.Button(description="Reset",         layout=w.Layout(width="80px"),
                           button_style="warning")

    jump_t = w.BoundedIntText(
        value=0, min=0, max=state.cue_count - 1,
        description="Jump tuning:", style={"description_width": "90px"},
        layout=w.Layout(width="180px"),
    )
    jump_v = w.BoundedIntText(
        value=0, min=0, max=state.cue_count - 1,
        description="Jump voice:", style={"description_width": "90px"},
        layout=w.Layout(width="180px"),
    )

    # ---------------------------------------------------------------- refresh

    def refresh():
        t_cur  = state.current_tuning()
        t_nxt  = state.next_tuning()
        v_cur  = state.current_voice()
        v_nxt  = state.next_voice()

        t_now_name.value  = f'<span style="{_BOLD}{_MONO}">{t_cur.name}</span>'
        t_now_cat.value   = f'<span style="{_MONO}">{_voice_line2_for_scale(t_cur)}</span>'
        t_next_name.value = f'<span style="{_DIM}{_MONO}">{t_nxt.name}</span>'
        t_next_cat.value  = f'<span style="{_DIM}{_MONO}">—</span>'

        v_now_name.value  = f'<span style="{_BOLD}{_MONO}">{v_cur.name}</span>'
        v_now_cat.value   = f'<span style="{_MONO}">{_voice_line2(v_cur)}</span>'
        v_next_name.value = f'<span style="{_DIM}{_MONO}">{v_nxt.name}</span>'
        v_next_cat.value  = f'<span style="{_DIM}{_MONO}">{_voice_line2(v_nxt)}</span>'

        scale_table.value = _scale_table(t_cur)

        # sync jump spinners to current pointers
        jump_t.value = state.tuning_ptr
        jump_v.value = state.voice_ptr

        armed = state.armed
        arm_btn.description  = "ARMED" if armed else "DISARMED"
        arm_btn.style.button_color = "#2e7d32" if armed else "#c62828"

    def _voice_line2_for_scale(_scale: ScaleEntry) -> str:
        return _scale.description.replace("_", " ")[:40]

    state._on_change = refresh
    refresh()

    # ---------------------------------------------------------------- wiring

    def on_arm_click(_):
        if state.armed:
            state.disarm()
        else:
            state.arm()

    arm_btn.on_click(on_arm_click)
    adv_both.on_click(lambda _: state.advance_both())
    adv_tuning.on_click(lambda _: state.advance_tuning())
    adv_voice.on_click(lambda _: state.advance_voice())
    reset_btn.on_click(lambda _: state.reset())

    def on_jump_t(change):
        if change["new"] != state.tuning_ptr:
            state.jump_tuning(change["new"])

    def on_jump_v(change):
        if change["new"] != state.voice_ptr:
            state.jump_voice(change["new"])

    jump_t.observe(on_jump_t, names="value")
    jump_v.observe(on_jump_v, names="value")

    # ---------------------------------------------------------------- layout

    tuning_box = w.VBox([
        w.HTML('<b>TUNING</b>'),
        w.HTML('<span style="color:#aaa">now:</span>'), t_now_name, t_now_cat,
        w.HTML('<span style="color:#aaa">next:</span>'), t_next_name,
    ], layout=w.Layout(border="1px solid #ccc", padding="8px", min_width="200px"))

    voice_box = w.VBox([
        w.HTML('<b>VOICE</b>'),
        w.HTML('<span style="color:#aaa">now:</span>'), v_now_name, v_now_cat,
        w.HTML('<span style="color:#aaa">next:</span>'), v_next_name, v_next_cat,
    ], layout=w.Layout(border="1px solid #ccc", padding="8px", min_width="200px"))

    display_row = w.HBox([tuning_box, w.HTML("&nbsp;&nbsp;&nbsp;"), voice_box])

    scale_info = scale_table

    button_row = w.HBox([adv_both, adv_tuning, adv_voice])
    jump_row   = w.HBox([jump_t, jump_v, reset_btn],
                        layout=w.Layout(align_items="flex-end"))

    return w.VBox([
        port_dropdown,
        arm_btn,
        w.HTML("<hr style='margin:6px 0'>"),
        display_row,
        scale_info,
        w.HTML("<hr style='margin:6px 0'>"),
        button_row,
        jump_row,
    ], layout=w.Layout(padding="12px", width="520px"))
