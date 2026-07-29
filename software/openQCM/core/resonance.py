"""
Resonance analysis: the single source of truth for peak detection, the
dissipation band and the filtering/fitting chain that precedes them.

Both acquisition processes (MultiscanProcess, SerialProcess) and any viewer
that wants to draw what was measured must call these functions. Before this
module the chain lived as two hand-copied blocks, one per acquisition process;
they were still token-identical, but in openQCM Q-1 the same duplication was
copied a third time into the GUI and the copies drifted apart, so the band
drawn on screen stopped being the band that was measured.

Nothing here touches Qt, files or process state: given the same arrays it
returns the same numbers, which is what makes it safe to call from the GUI
thread while an acquisition is running.
"""

from collections import namedtuple
from math import factorial

import numpy as np
from scipy.interpolate import UnivariateSpline


###############################################################################
# FILTERING - Savitzky-Golay
###############################################################################
def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    r"""Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    """
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')


###############################################################################
# FITTING/INTERPOLATING - SPLINE
###############################################################################
def spline_fit(freq_axis, signal, spline_factor, spline_points):
    """Resample ``signal`` onto ``spline_points`` evenly spaced frequencies.

    The spline is built against the sample *index*, not the frequency, exactly
    as the acquisition path has always done: with a uniform sweep step the two
    are equivalent up to an affine change of variable, and the smoothing factor
    is calibrated for the index scale.

    :return: (freq_fine, signal_fit), both of length ``spline_points``.
    """
    xrange = range(len(signal))
    freq_fine = np.linspace(freq_axis[0], freq_axis[-1], spline_points)
    s = UnivariateSpline(xrange, signal, s=spline_factor)
    xs = np.linspace(0, len(signal) - 1, spline_points)
    return freq_fine, s(xs)


###############################################################################
# Resonance Frequency, Resonance Peak, Bandwidth
###############################################################################
Band = namedtuple("Band", [
    "peak_index",        # index of the maximum in the fitted arrays
    "peak_value",        # the maximum itself, dB above the corrected baseline
    "peak_frequency",    # resonance frequency, Hz: the frequency of the maximum
    "leading_index",     # last sample index still above threshold, left side
    "trailing_index",    # ... right side
    "leading_frequency", # interpolated left crossing, Hz
    "trailing_frequency",# interpolated right crossing, Hz
    "bandwidth",         # trailing - leading, Hz
    "err_left",          # threshold never crossed on the left: band is truncated
    "err_right",         # ... on the right
])


def find_peak_and_band(freq, signal, threshold):
    """Locate the resonance peak and the band used for the dissipation.

    ``threshold`` is a drop in dB *below the maximum* (Constants.THRESHOLD_DB,
    0.3 dB), not a fraction of it: the sweep is baseline-corrected, so it
    crosses zero and a proportional threshold — what openQCM Q-1 uses, with
    0.707 — would move with the baseline instead of with the peak.

    The two edges are found by walking outwards from the maximum until the
    signal drops below ``f_max - threshold``, then linearly interpolating
    between the last sample above and the first below. The returned edges are
    therefore frequencies in Hz, not indices, and the band is generally
    narrower than ``trailing_index - leading_index`` sample steps.

    Since VER 0.1.4 the fundamental and the overtones share this definition,
    so there is one code path for both; before that the overtones used the
    midpoint between maximum and minimum, and the two branches survived as
    duplicated code long after they had become numerically identical.

    :param freq: frequency axis, Hz, same length as ``signal``.
    :param signal: baseline-corrected, filtered and fitted amplitude, dB.
    :param threshold: band threshold below the maximum, dB.
    :return: a :class:`Band`.
    """
    err_left = 0
    err_right = 0

    f_max = np.max(signal)              # Find maximum
    i_max = np.argmax(signal, axis=0)   # Find index of maximum

    # LEADING EDGE: walk left from the peak
    index_m = i_max
    while signal[index_m] > (f_max - threshold):
        if index_m < 1:
            err_left = 1
            break
        index_m = index_m - 1

    # linearly interpolate between the previous values to find the value of
    # freq at the leading edge. Note this runs on the truncated index too when
    # err_left is set, which keeps the historical behaviour: the edge is then
    # extrapolated from the first two samples rather than clamped to freq[0].
    m = (signal[index_m+1] - signal[index_m]) / (freq[index_m+1] - freq[index_m])
    c = signal[index_m] - freq[index_m] * m
    i_leading = (f_max - threshold - c) / m

    # TRAILING EDGE: walk right from the peak
    index_M = i_max
    while signal[index_M] > (f_max - threshold):
        if index_M >= len(signal) - 1:
            err_right = 1
            break
        index_M = index_M + 1

    # linearly interpolate between the previous values to find the value of
    # freq at the trailing edge
    m = (signal[index_M-1] - signal[index_M]) / (freq[index_M-1] - freq[index_M])
    c = signal[index_M] - freq[index_M] * m
    i_trailing = (f_max - threshold - c) / m

    bandwidth = abs(i_trailing - i_leading)

    return Band(
        peak_index=i_max,
        peak_value=f_max,
        peak_frequency=freq[i_max],
        leading_index=index_m,
        trailing_index=index_M,
        leading_frequency=i_leading,
        trailing_frequency=i_trailing,
        bandwidth=bandwidth,
        err_left=err_left,
        err_right=err_right,
    )


###############################################################################
# The whole chain, for consumers that hold a raw sweep
###############################################################################
def analyze_sweep(freq_axis, mag_baseline_corrected, sg_window_size, sg_order,
                  spline_factor, spline_points, threshold):
    """Filter, fit and measure a baseline-corrected sweep in one call.

    This is the chain the acquisition path runs, in the same order and with the
    same constants, so a viewer calling this draws the numbers that were
    actually logged.

    :return: (freq_fine, mag_fit, band) with ``band`` a :class:`Band`.
    """
    filtered = savitzky_golay(mag_baseline_corrected,
                              window_size=sg_window_size, order=sg_order)
    freq_fine, mag_fit = spline_fit(freq_axis, filtered, spline_factor,
                                   spline_points)
    band = find_peak_and_band(freq_fine, mag_fit, threshold)
    return freq_fine, mag_fit, band
