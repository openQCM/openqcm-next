"""
The MTD415T error register, decoded and reported on change.

The firmware appends the controller's error register to every temperature
sample, and the acquisition processes used to print one warning line per
sweep per active bit -- to the console only, since a child process's print
never reaches the System Log. Both processes decode here now, once, and report
through `ParserProcess.add_message()` only when the set of active errors
changes: one line when an error appears, one when it clears. The pill in the
Temperature card shows the continuous state; the log shows the transitions.
"The error cleared" is also the only observable that a TEC Reset did what the
data sheet says it does.

Bit 0, "Enable pin not set", is the normal state of a TEC that is switched
off and is never reported, as before.
"""

from openQCM.core.constants import Constants

# bit 0 is not an error: it says the TEC is off
IGNORED_BITS = {0}


def decode_error_register(value):
    """Set of active error names for a 16-bit register value (bit 0 excluded).

    Bit numbers follow the data sheet, 6.3, through Constants.ERROR_REG_EVENT.
    """
    active = set()
    try:
        value = int(value)
    except (TypeError, ValueError):
        return active
    for bit, name in enumerate(Constants.ERROR_REG_EVENT):
        if bit in IGNORED_BITS or name == "Not used":
            continue
        if value & (1 << bit):
            active.add(name)
    return active


def report_error_changes(active, previous, add_message):
    """Send one line per error that appeared or cleared; return `active`.

    `previous` is the set from the last sweep (None on the first one: every
    active error is then reported as new).
    """
    previous = set() if previous is None else previous
    for name in sorted(active - previous):
        add_message("WARNING: MTD415T Temperature control error: {}".format(name))
    for name in sorted(previous - active):
        add_message("MTD415T Temperature control error cleared: {}".format(name))
    return active
