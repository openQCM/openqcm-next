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


def _export_directory():
    """``openQCM/sweep_data``, with the separator this OS uses."""
    if Architecture.get_os() in {OSType.macosx, OSType.linux}:
        slash = "/"
    elif Architecture.get_os() is OSType.windows:
        slash = "\\"
    else:
        slash = "/"
    return "openQCM" + slash + Constants.sweep_export_path


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
