import time

import mido

_PREFERRED = "YAMAHA MOTIF6 PORT1"
_INTER_MSG_DELAY = 0.020  # 20 ms between sysex messages (DIN MIDI rate limiting)


class MidiOut:
    def __init__(self, port_name: str | None = None):
        """
        Open a MIDI output port.
        port_name=None prefers YAMAHA MOTIF6 PORT1 if present, else first port.
        """
        available = mido.get_output_names()
        if not available:
            raise RuntimeError("No MIDI output ports found")
        if port_name is None:
            port_name = _PREFERRED if _PREFERRED in available else available[0]
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
        for i, msg_bytes in enumerate(messages):
            # mido SysexData strips the 0xF0/0xF7 framing bytes
            data = tuple(msg_bytes[1:-1])
            self._port.send(mido.Message("sysex", data=data))
            if i < len(messages) - 1:
                time.sleep(_INTER_MSG_DELAY)

    def close(self) -> None:
        self._port.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @staticmethod
    def list_ports() -> list[str]:
        return mido.get_output_names()
