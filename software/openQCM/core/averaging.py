"""
Robust averaging of the acquisition ring buffers.

Replaces ``scipy.stats.trim_mean`` at the six places that average the raw
frequency, dissipation and temperature buffers. The estimator is the same --
sort, drop k samples from each tail, average the rest -- but k is chosen so that
outlier rejection is a property of the algorithm instead of a coincidence.

``trim_mean`` drops ``int(proportiontocut * N)`` samples per tail, which is
**zero for every N below 10**. With ``proportiontocut = 0.10`` the rejection the
VER 0.1.6 change was introduced for therefore existed only because
``Constants.environment`` happened to be exactly 10: any future resizing of the
buffer switched it off in silence, with nothing in the output to show that the
average had quietly become a plain arithmetic mean. Measured on a buffer of nine
100s and one 1000: ``trim_mean`` returns 100 at N=10 and 400 at N=3.

The floor of one sample per tail fixes that. For N >= 10 the retained set and the
order it is summed in are identical to ``trim_mean``'s, so logged production
values do not move -- verified bit for bit against scipy on the real buffers.
"""

import numpy as np


def trim_count(n, proportiontocut):
    """How many samples to drop from *each* tail of an n-sample buffer.

    The proportion still governs how much is cut on a large buffer, but with two
    bounds:

    * a **floor of one** sample per tail, so a small buffer still rejects its
      extremes rather than degenerating into a plain mean;
    * a **ceiling of ``(n - 1) // 2``**, so at least one sample always survives.
      Without it, dropping one per tail of a 2-sample buffer would leave nothing
      to average.

    Below three samples there is nothing meaningful to trim, so nothing is:
    trimming a pair leaves a single sample, which is not an average of anything.

    :return: k, the number of samples to drop at each end (0 <= 2k < n).
    """
    if n <= 2:
        return 0
    return min(max(1, int(proportiontocut * n)), (n - 1) // 2)


def robust_mean(values, proportiontocut):
    """Trimmed mean of ``values`` with :func:`trim_count`'s k per tail.

    NaN is ordered above every real number, so a NaN is discarded as the high
    extreme instead of poisoning the average -- as long as there are no more NaNs
    than k. This is a **behaviour change** at the current development buffer size:
    with ``trim_mean`` and N=3, k was 0 and a single NaN made the logged value
    NaN; here it is trimmed. At N >= 10 ``trim_mean`` already dropped it, so
    nothing changes there.

    ``np.partition`` rather than ``np.sort``, with the same kth arguments
    ``trim_mean`` uses, because ``np.mean`` adds in array order: sorting fully
    would leave the retained samples in a different order from ``trim_mean``'s
    and the result would differ in the last bit. Measured before this was
    matched: 25.045000000000002 against 25.044999999999998 on a temperature
    buffer, one ULP, from summation order alone. Since k equals
    ``int(proportiontocut * n)`` for every n >= 10, the result is now identical
    bit for bit wherever the old code was doing any trimming at all.

    :param values: the buffer, as returned by ``RingBuffer.get_all()``.
    :param proportiontocut: fraction to cut per tail before the floor/ceiling.
    :return: the trimmed mean as a float, or NaN for an empty buffer.
    """
    data = np.asarray(values, dtype=float).ravel()
    n = data.size
    if n == 0:
        return float("nan")
    k = trim_count(n, proportiontocut)
    if k == 0:
        # n <= 2 only: a one- or two-sample mean is order-independent anyway
        return float(np.mean(data))
    ordered = np.partition(data, (k, n - k - 1))
    return float(np.mean(ordered[k:n - k]))
