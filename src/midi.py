import mido


class MidiOut:
    def __init__(self, port_name: str | None = None):
        """
        Open a MIDI output port.
        port_name=None opens the first available port.
        """
        available = mido.get_output_names()
        if not available:
            raise RuntimeError("No MIDI output ports found")
        name = port_name if port_name is not None else available[0]
        self._port = mido.open_output(name)

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
