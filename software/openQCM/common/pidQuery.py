"""
Ask the TEC controller for its PID parameters over an open serial handle.

Used by the acquisition processes (`Multiscan.py`, `Serial.py`) to answer a
Read PID asked from the window while they own the port. They can only do it
between sweeps: during a sweep the board is streaming and answers nothing, so
the call sits where the process already reads the TEC current with `A?`.

The GUI has its own path for Standby (`mainWindow._query_pid`), which drains
the port and recognises a board still streaming; this one assumes the caller
is already in the quiet gap between sweeps, which the acquisition loop is.
"""

from time import sleep

from openQCM.core.constants import Constants

KEYS = "CPID"


def read_pid(port, settle=0.1):
    """(C, P, I, D) as the controller reports them; None for a missing answer.

    One question at a time, `settle` seconds between write and read, the same
    rhythm the acquisition uses for `A?`. Total cost about 4 * 2 * settle.
    """
    values = []
    for key in KEYS:
        sleep(settle)
        port.reset_input_buffer()
        port.write("{}?\n".format(key).encode())
        sleep(settle)
        raw = port.read(port.inWaiting()).decode(Constants.app_encoding)
        line = ""
        for candidate in raw.splitlines():
            candidate = candidate.strip()
            if candidate:
                line = candidate
                break
        try:
            values.append(int(line))
        except ValueError:
            values.append(None)
    return tuple(values)
