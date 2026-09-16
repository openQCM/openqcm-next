"""
openQCM NEXT -- the circle drawn over an admittance locus. DISPLAY ONLY.

Shared by the main-window impedance panel and the live fit window, so the two
views draw the SAME circle for the same sweep and the rule of what is drawn
lives in one place:

  experimental run  the published fit's own circle. A rotated Lorentzian IS a
                    circle in the complex plane: diameter G_max, centre at
                    offset + (G_max/2)·e^{jφ}. G_off comes from the fit (in the
                    frame of the shipped, baseline-removed G); B_off was never
                    fitted -- the process fits G alone -- so it is anchored on
                    the measured B at f_res, one lookup. Nothing new is
                    estimated: the geometry is the published model.

  standard run      there is no model. A circle is fitted HERE, on the ±Γ core
                    of the measured locus, in closed form (Taubin). It is drawn
                    and labelled as fitted here; nothing is published from it.

⚠️ Neither branch feeds back into the acquisition: f_res, Γ and D are what the
process shipped in the G/B message, always.

Also here: the framing rule for an aspect-locked locus view (LocusFramer), for
the same reason -- one behaviour, two windows.
"""
import numpy as np

# radians around the circle for the polyline
_THETA = np.linspace(0.0, 2.0 * np.pi, 361)

# the colour of everything that comes from the fit, in both windows
FIT_COLOUR = "#f44336"

KIND_PUBLISHED = "published"      # the fit's circle, experimental run
KIND_FITTED = "fitted"            # Taubin on the measured core, standard run


def finite(x):
    try:
        return x is not None and np.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def taubin_circle(x, y):
    """Algebraic circle through a point cloud, closed form (Taubin). DISPLAY ONLY.

    Returns (xc, yc, r) or None when fewer than 8 finite points or degenerate.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    keep = np.isfinite(x) & np.isfinite(y)
    x, y = x[keep], y[keep]
    if len(x) < 8:
        return None
    mx, my = x.mean(), y.mean()
    u, v = x - mx, y - my
    z = u * u + v * v
    Muu, Mvv, Muv = (u * u).mean(), (v * v).mean(), (u * v).mean()
    Muz, Mvz = (u * z).mean(), (v * z).mean()
    cov = Muu * Mvv - Muv * Muv
    if abs(cov) < 1e-30:
        return None
    xc = (Muz * Mvv - Mvz * Muv) / cov / 2.0
    yc = (Mvz * Muu - Muz * Muv) / cov / 2.0
    r2 = xc * xc + yc * yc + Muu + Mvv
    if not np.isfinite(r2) or r2 <= 0:
        return None
    return xc + mx, yc + my, float(np.sqrt(r2))


def is_experimental(fit):
    """True when the fit dict carries a published rotated-Lorentzian model."""
    return bool(fit) and fit.get("mode") != "argmax" and all(
        finite(fit.get(k)) for k in ("gmax_mS", "phi_deg", "g_off_mS"))


def circle_for(fit, f, g, b, f_pub):
    """The circle to draw over the locus (g, b) of one overtone.

    fit    the worker's fit dict for the overtone (get_fit_G_buffer), or None
    f, g   shipped frequency axis and conductance (G baseline-removed, mS)
    b      shipped susceptance (as computed, mS)
    f_pub  the published resonance frequency, Hz

    Returns None, or a dict with
      kind   KIND_PUBLISHED | KIND_FITTED
      xc, yc, r
      x, y   the polyline of the circle, ready for setData
      label  one line saying which circle this is, for a title
      rms    (fitted only) radial residual, % of r
    """
    f = np.asarray(f, dtype=float)
    g = np.asarray(g, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(f) < 8 or len(g) != len(f) or len(b) != len(f):
        return None

    if is_experimental(fit):
        gmax, phi = float(fit["gmax_mS"]), np.radians(float(fit["phi_deg"]))
        b_at = float(np.interp(f_pub, f, b))          # one lookup, anchors B_off
        b_off = b_at - gmax * np.sin(phi)
        xc = float(fit["g_off_mS"]) + 0.5 * gmax * np.cos(phi)
        yc = b_off + 0.5 * gmax * np.sin(phi)
        r = 0.5 * abs(gmax)
        out = dict(kind=KIND_PUBLISHED, xc=xc, yc=yc, r=r, rms=float("nan"),
                   label=("circle of the published fit: R1 = %.0f Ω, φ = %+.1f°"
                          % (1e3 / gmax if gmax else float("inf"), np.degrees(phi))))
    else:
        gam = None if not fit else fit.get("gamma_hh")
        core = np.ones(len(f), dtype=bool)
        if finite(gam) and gam > 0:
            sel = np.abs(f - f_pub) <= gam
            if sel.sum() >= 12:
                core = sel
        circ = taubin_circle(g[core], b[core])
        if circ is None:
            return None
        xc, yc, r = circ
        rad = np.hypot(g[core] - xc, b[core] - yc)
        rms = 100.0 * float(np.sqrt(np.mean((rad - r) ** 2)) / r) if r else float("nan")
        out = dict(kind=KIND_FITTED, xc=xc, yc=yc, r=r, rms=rms,
                   label=("circle fitted HERE on the ±Γ core (display only): "
                          "R1 = %.0f Ω, residual %.1f %% of r"
                          % (1e3 / (2.0 * r) if r else float("inf"), rms)))
    out["x"] = xc + r * np.cos(_THETA)
    out["y"] = yc + r * np.sin(_THETA)
    return out


def union_bounds(*xy_pairs):
    """(xmin, xmax, ymin, ymax) over any number of (x, y) arrays; None if empty."""
    xs = [np.asarray(x, dtype=float) for x, _ in xy_pairs if x is not None and len(x)]
    ys = [np.asarray(y, dtype=float) for _, y in xy_pairs if y is not None and len(y)]
    if not xs or not ys:
        return None
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    x, y = x[np.isfinite(x)], y[np.isfinite(y)]
    if not len(x) or not len(y):
        return None
    return float(x.min()), float(x.max()), float(y.min()), float(y.max())


class LocusFramer(object):
    """Fit an aspect-locked locus view to the measurement AND the circle, once.

    ⚠️ Auto-range does not do this. With the aspect locked -- and it has to be,
    a circle must look like one -- pyqtgraph frames the data and then expands
    one axis to satisfy the ratio; the circle overlay, which reaches further
    than the arc it is drawn over, came out cut on the right (measured on the
    fundamental in air, 2026-09-16). So the range is set here, over the union
    of both.

    Framed only when the required bounds are new or have changed by more than
    a fifth -- a new liquid, a new overtone -- so that a zoom made by hand
    survives the next sweep instead of being reset twenty times a second. The
    right-click menu's Auto-scale is still there to give the view back.
    """

    def __init__(self, plot, padding=0.06):
        self.plot = plot
        self.padding = padding
        self.framed = None            # the bounds last framed on

    def reset(self):
        self.framed = None

    def frame(self, xmin, xmax, ymin, ymax):
        want = (float(xmin), float(xmax), float(ymin), float(ymax))
        if not all(np.isfinite(want)):
            return False
        span = max(want[1] - want[0], want[3] - want[2])
        if span <= 0:
            return False
        if self.framed is not None:
            moved = max(abs(a - b) for a, b in zip(want, self.framed))
            if moved < 0.2 * span:
                return False
        self.framed = want
        self.plot.setRange(xRange=(want[0], want[1]), yRange=(want[2], want[3]),
                           padding=self.padding)
        return True
