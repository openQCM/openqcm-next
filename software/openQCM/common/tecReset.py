"""
The TEC controller's error-register reset, as a sequence on an open serial port.

MTD415T data sheet, 6.3: the error register is cleared by the "c" command or by
setting the Enable pin Off and On again. The firmware forwards neither "c" nor
the pin directly; it takes X0 / X1 and drives the pin, so the reset is the
sequence X0, pause, X1, pause, X0 -- the same one `mainWindow._TEC_Reset_button`
has always sent from Standby, ending with the TEC not active.

This module exists so that the acquisition process can run the very same
sequence when it owns the port. Before it, a reset asked during a measurement
went through the TEC flag in config.txt, which the process re-reads once per
sweep: a 0 / 1 / 0 written over four seconds could reach the controller as a
single X0, and nothing said which. Measured at the bench, 2026-09-09.
"""

from time import sleep

SEQUENCE = ("X0", "X1", "X0")
# the pauses the Standby path has used since 0.1.5: the module needs the time
PAUSE_S = 2.0
SETTLE_S = 0.5


def reset_sequence(port, pause_s=PAUSE_S, settle_s=SETTLE_S):
    """Write X0, X1, X0 on `port` with the standard pauses; returns the
    commands written, for the log."""
    sent = []
    for i, cmd in enumerate(SEQUENCE):
        port.write("{}\n".format(cmd).encode())
        sent.append(cmd)
        sleep(pause_s if i < len(SEQUENCE) - 1 else settle_s)
    return sent
