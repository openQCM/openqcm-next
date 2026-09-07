"""
Development-only dump of the raw sweeps to ``sweep_data/<n>.txt``.

This is the *only* place that writes those files, and nothing else depends on
it: the live Raw Data View reads the acquisition buffers in memory and shares no
state and no code path with this module, so deleting this file leaves the dialog
working and unchanged. That separation is the point -- in openQCM Q-1 the viewer
read the dump, which meant the debugging tool and the user-facing view could not
be told apart, and one could not be removed without breaking the other.

Off by default. Turn it on for a session with the environment variable, without
editing any source:

    OPENQCM_SWEEP_DUMP=1 python3 run.py

Each sweep overwrites the previous one, so the files hold the most recent sweep
per overtone and nothing more. Copy them somewhere else before analysing them.
"""

import os
import re

from openQCM.core.constants import Constants
from openQCM.common.architecture import Architecture, OSType
from openQCM.common.fileStorage import FileStorage

ENV_VAR = "OPENQCM_SWEEP_DUMP"

_OFF = ("", "0", "false", "no", "off")


def is_enabled():
    """True when the sweep dump should run.

    The environment variable wins over the constant, so a release build with
    Constants.dev_sweep_dump = False can still be asked for a dump when
    something needs debugging on a machine one cannot rebuild on.
    """
    value = os.environ.get(ENV_VAR)
    if value is not None:
        return value.strip().lower() not in _OFF
    return bool(Constants.dev_sweep_dump)


CAL_ENV_VAR = "OPENQCM_CAL_DUMP"


def calibration_label():
    """The label a calibration dump was asked for, or None when it is off.

    The variable carries the LABEL, not a flag:

        OPENQCM_CAL_DUMP=open python3 run.py

    so each run writes its own file and the next one cannot overwrite it.
    ⚠️ That is deliberate. Every other dump in this codebase overwrites, and
    the datasets behind the July 2026 validation tables were lost exactly that
    way; a characterisation made of three runs must not depend on somebody
    copying a file out between them.
    """
    value = os.environ.get(CAL_ENV_VAR)
    if value is None:
        return None
    value = value.strip()
    if not value or value.lower() in _OFF:
        return None
    return value


def _export_directory():
    """``openQCM/sweep_data``, with the separator this OS uses."""
    if Architecture.get_os() in {OSType.macosx, OSType.linux}:
        slash = "/"
    elif Architecture.get_os() is OSType.windows:
        slash = "\\"
    else:
        slash = "/"
    return "openQCM" + slash + Constants.sweep_export_path


def save_calibration_sweep(frequency, magnitude, phase):
    """Write the whole calibration sweep, whatever the peak logic decides.

    ⚠️ Why this exists. `Calibration_5MHz.txt` is only written when the first
    detected peak looks like a 5 MHz fundamental. That is right for the
    instrument -- a sweep with no resonance has no calibration to save -- but it
    means the raw 1-51 MHz sweep is unreachable for exactly the measurements
    that characterise the electronics: an open, a short and a 50 ohm load have
    no resonance by construction, and produce nothing at all.

    Off unless OPENQCM_CAL_DUMP names a label. Writes `cal_<label>.txt` beside
    the other dumps, in the same three-column format.

    :return: the path written, or None.
    """
    label = calibration_label()
    if label is None:
        return None
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", label)
    name = "cal_" + safe
    FileStorage.TXT_sweeps_save(name, _export_directory(),
                                frequency, magnitude, phase)
    return name


def save_sweep(overtone_index, frequency, magnitude, phase, prefix=""):
    """Write one overtone's raw sweep, if the dump is enabled.

    :param overtone_index: 0 for the fundamental, 1 for the 3rd overtone, ...
        The file is named after the harmonic order, so index 2 becomes 5.txt.
    :param prefix: prepended to the file name, for callers that dump a second
        series alongside the first. The impedance work writes the divider's raw
        V_MAG/V_PHS as ``g1.txt`` .. ``g9.txt`` next to ``1.txt`` .. ``9.txt``;
        the parameter lives here rather than in that caller so the export path
        and the enable flag stay in one place.
    :return: True if a file was written.
    """
    if not is_enabled():
        return False
    name = "{}{}".format(prefix, (int(overtone_index) * 2) + 1)
    FileStorage.TXT_sweeps_save(name,
                                _export_directory(),
                                frequency, magnitude, phase)
    return True
