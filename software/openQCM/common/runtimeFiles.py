"""The runtime files the application reads, in one place (HANDOFF §5 "Runtime files").

``load_frequencies_file`` used to exist as five copies, identical down to the AST, in
``Serial``, ``Multiscan``, ``worker``, ``mainWindow`` and ``plot_sweep_spline``; each of
them now delegates here. It is the first brick of HANDOFF §5 item 1: the tolerant read
with an actionable error belongs in this module, and lands in every caller at once.
"""
from numpy import loadtxt

from openQCM.core.constants import Constants


def load_frequencies_file():
    """The peak frequencies, fundamental first: column 0 of PeakFrequencies.txt.

    ⚠️ Raises, as every copy always did, on a missing file (OSError) or a one-row one
    (``data[:, 0]`` needs two dimensions). ``Worker.reset_buffers`` relies on that to stop
    START early in every mode; making the read tolerant is HANDOFF §5 item 1, a decision
    of its own, not a side effect of moving the function.
    """
    data = loadtxt(Constants.cvs_peakfrequencies_path)
    return data[:, 0]
