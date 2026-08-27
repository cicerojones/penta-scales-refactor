import mido

# Match on "motif" rather than an exact string: the Motif's reported port
# name has been observed with different casing across machines (e.g.
# "YAMAHA MOTIF6 PORT1" vs "YAMAHA MOTIF6 Port1"), so an exact-match
# constant silently fell back to whatever port happened to be first
# (e.g. IAC Driver Bus 1) instead of the Motif.
_PREFERRED_SUBSTRING = "motif"


class MidiOut:
    def __init__(self, port_name: str | None = None):
        """
        Open a MIDI output port.
        port_name=None prefers the first port containing "motif" (case-insensitive),
        else the first available port.
        """
        available = mido.get_output_names()
        if not available:
            raise RuntimeError("No MIDI output ports found")
        if port_name is None:
            motif_ports = [p for p in available if _PREFERRED_SUBSTRING in p.lower()]
            if motif_ports:
                port_name = motif_ports[0]
            else:
                port_name = available[0]
                print(f"Warning: no MIDI port matching {_PREFERRED_SUBSTRING!r} found; "
                      f"defaulting to {port_name!r}")
        self._port_name = port_name
        self._port = mido.open_output(port_name)

    @property
    def port_name(self) -> str:
        return self._port_name

    def set_port(self, name: str) -> None:
        """Close the current port and open a new one by name."""
        self._port.close()
        self._port = mido.open_output(name)
        self._port_name = name

    def send_sysex(self, messages: list[bytes]) -> None:
        """Send a list of pre-assembled sysex messages (each bytes object 240...247)."""
        for msg_bytes in messages:
            # mido SysexData strips the 0xF0/0xF7 framing bytes
            data = tuple(msg_bytes[1:-1])
            self._port.send(mido.Message("sysex", data=data))

    def close(self) -> None:
        self._port.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @staticmethod
    def list_ports() -> list[str]:
        return mido.get_output_names()
