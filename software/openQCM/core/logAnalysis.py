"""
Two-window statistics over a logged run: what changed between a starting state
and a final one, and how quiet the instrument was in each.

This is the analysis that lived inside the legacy matplotlib viewer
(`data_view/main.py`, `process_data`) as 350 lines of copy-pasted-per-overtone
code. It is here, on its own and without Qt, for the reason every shared module
in this codebase exists: a viewer that re-derives a measured quantity is a
viewer that ends up disagreeing with the instrument. Import it; do not write a
second copy.

WHAT IS REPORTED, AND WHAT IT DEPENDS ON
----------------------------------------
Three of the four quantities are **independent of the reference** the caller
draws its curves against, which is what makes them safe to show next to a
Datalog View whose reference is a cursor the user can drag:

- ``shift``      mean(final) - mean(initial). A difference of means: any constant
                 subtracted from the whole series cancels.
- ``std``        the spread inside one window.
- ``hadamard``   see below.
- ``mean``       the ONLY one that moves with the reference. It is the mean of the
                 window in whatever units and origin the caller passed in.

HADAMARD DEVIATION
------------------
The second-difference estimator, the one that answers "how much does this drift
on top of its noise" without being fooled by a linear ramp -- which is exactly
what a QCM run has:

    H = sqrt( sum_n (x[n-1] - 2 x[n] + x[n+1])^2 / (6 N) )

with N the number of terms actually summed. It is reported **normalised by the
harmonic order** (the 3rd overtone divided by 3, and so on), which is what makes
the five numbers comparable: an overtone measures the same physical drift at a
frequency that is a multiple of the fundamental's.

⚠️ FOUR DEFECTS OF THE LEGACY IMPLEMENTATION ARE FIXED HERE, and the numbers it
printed for them were wrong, not merely differently rounded:

1. **The 9th overtone reported the 7th's value.** `f_3_hadamard/9.0` where it had
   to be `f_4_hadamard/9.0` -- `data_view/main.py` lines 508 and 516, in both the
   initial and the final block. Measured on a probe file built with a quiet 7th
   and a noisy 9th: the window showed **0.03** where the answer is **1.30**.
2. **The final window was normalised by the initial window's length**,
   `6 * (j - i)` instead of `6 * (l - k)`. Harmless only while the two windows
   happen to be the same length, which nothing enforced.
3. **The Hadamard loop ran off the front of the array.** `range(i, j)` reads
   ``x[i-1]``, so a window starting at sample 0 folded the LAST sample of the run
   into the first term through Python's negative indexing. Here the sum runs over
   the terms that exist, and a window too short to hold one is reported as NaN
   rather than as a number.
4. **A window reaching past the end of the run silently lost its last sample.**
   The legacy index search was a `for` loop with a `break`; when nothing exceeded
   the requested time it fell out with the index of the LAST sample rather than
   one past it, so the slice stopped one short. This is not an edge case -- it is
   what happens every time someone asks for a final window that runs to the end
   of the run, which is the normal way to use it.

WINDOW SELECTION
----------------
Otherwise ``window_indices`` keeps the legacy semantics exactly -- first sample
**strictly after** the start time, first sample strictly after start+duration --
because moving where a window begins would move every number in the report for
reasons that have nothing to do with the fixes above.
"""

from collections import namedtuple

import numpy as np

# One overtone inside one window.
WindowStats = namedtuple("WindowStats", "order n mean std hadamard")

# One overtone across both windows. `shift` is final.mean - initial.mean.
SeriesReport = namedtuple("SeriesReport", "order initial final shift")

# The whole analysis. `initial_span` / `final_span` are the (start, end) times
# actually covered, which is not the requested pair: a window is bounded by the
# samples that exist.
Report = namedtuple("Report",
                    "frequency dissipation initial_span final_span")


###############################################################################
def window_indices(time_s, start, duration):
    """Half-open [lo, hi) index range for the window (start, start+duration].

    The legacy rule, kept deliberately: `lo` is the first sample strictly after
    `start`, `hi` the first strictly after `start + duration`. Returns
    ``(lo, hi)`` with ``lo <= hi``; an empty window gives ``lo == hi``.

    Where nothing exceeds the requested time the index is the array length, not
    the last sample -- see defect 4 in the module docstring. That one difference
    is deliberate; every other window lands exactly where the legacy loop put it.
    """
    t = np.asarray(time_s, dtype=float).ravel()
    n = t.size
    if n == 0:
        return 0, 0

    def first_after(x):
        idx = np.searchsorted(t, x, side="right")
        return int(min(idx, n))

    lo = first_after(float(start))
    hi = first_after(float(start) + float(duration))
    if hi < lo:
        hi = lo
    return lo, hi


###############################################################################
def hadamard_deviation(values, lo, hi):
    """Hadamard deviation over ``values[lo:hi]``, in the units of ``values``.

    The second differences are formed only where all three samples exist, so a
    window at the very start of the run does not wrap around to the end of it.
    Returns NaN when fewer than one term can be formed, or when the window holds
    a NaN -- a silent zero would read as a perfectly quiet instrument.
    """
    x = np.asarray(values, dtype=float).ravel()
    lo = max(int(lo), 1)
    hi = min(int(hi), x.size - 1)
    if hi <= lo:
        return float("nan")
    terms = x[lo - 1:hi - 1] - 2.0 * x[lo:hi] + x[lo + 1:hi + 1]
    if terms.size == 0:
        return float("nan")
    return float(np.sqrt(np.sum(terms ** 2) / (6.0 * terms.size)))


###############################################################################
def _stats(values, order, lo, hi):
    x = np.asarray(values, dtype=float).ravel()[lo:hi]
    if x.size == 0:
        nan = float("nan")
        return WindowStats(order=order, n=0, mean=nan, std=nan, hadamard=nan)
    # normalised by the harmonic order: an overtone measures the same drift at a
    # multiple of the fundamental's frequency, so the raw numbers are not
    # comparable across the five and the divided ones are.
    h = hadamard_deviation(values, lo, hi) / float(order)
    return WindowStats(order=order, n=int(x.size),
                       mean=float(np.mean(x)), std=float(np.std(x)),
                       hadamard=h)


###############################################################################
def analyse(time_s, series, initial, final):
    """Run the two-window analysis.

    ``series`` is what `dataLogView.read_log` produces: a sequence of
    ``(harmonic order, frequency array, dissipation array)``. ``initial`` and
    ``final`` are ``(start, duration)`` in seconds, the units of ``time_s``.

    The caller decides what the arrays hold -- absolute values, or shifts against
    whatever reference the view is drawing. Only ``mean`` follows that choice;
    ``shift``, ``std`` and ``hadamard`` do not.
    """
    t = np.asarray(time_s, dtype=float).ravel()
    i, j = window_indices(t, *initial)
    k, l = window_indices(t, *final)

    freq, diss = [], []
    for order, f, d in series:
        order = int(order) or 1
        for values, out in ((f, freq), (d, diss)):
            a = _stats(values, order, i, j)
            b = _stats(values, order, k, l)
            out.append(SeriesReport(order=order, initial=a, final=b,
                                    shift=b.mean - a.mean))

    def span(lo, hi):
        if hi <= lo or t.size == 0:
            return (float("nan"), float("nan"))
        return (float(t[lo]), float(t[min(hi, t.size) - 1]))

    return Report(frequency=freq, dissipation=diss,
                  initial_span=span(i, j), final_span=span(k, l))


###############################################################################
def format_report(report, freq_unit="Hz", diss_unit="ppm"):
    """The analysis as plain text, in the order the legacy window printed it."""
    lines = []

    def block(title, rows, unit, key):
        lines.append("{} ({})".format(title, unit))
        for r in rows:
            lines.append("  F{:<2} {:>12}".format(r.order, _fmt(key(r))))
        lines.append("")

    a0, a1 = report.initial_span
    b0, b1 = report.final_span
    lines.append("initial window {} .. {} s   |   final window {} .. {} s"
                 .format(_fmt(a0, 1), _fmt(a1, 1), _fmt(b0, 1), _fmt(b1, 1)))
    lines.append("samples: {} initial, {} final".format(
        report.frequency[0].initial.n if report.frequency else 0,
        report.frequency[0].final.n if report.frequency else 0))
    lines.append("")

    block("Frequency shift", report.frequency, freq_unit, lambda r: r.shift)
    block("Dissipation shift", report.dissipation, diss_unit, lambda r: r.shift)
    block("Frequency noise, initial (Hadamard / order)", report.frequency,
          freq_unit, lambda r: r.initial.hadamard)
    block("Frequency noise, final (Hadamard / order)", report.frequency,
          freq_unit, lambda r: r.final.hadamard)
    block("Frequency std, initial", report.frequency, freq_unit,
          lambda r: r.initial.std)
    block("Frequency std, final", report.frequency, freq_unit,
          lambda r: r.final.std)
    block("Dissipation std, initial", report.dissipation, diss_unit,
          lambda r: r.initial.std)
    block("Dissipation std, final", report.dissipation, diss_unit,
          lambda r: r.final.std)
    return "\n".join(lines).rstrip()


def _fmt(value, decimals=2):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "-"
    return "{:.{}f}".format(value, decimals)
