#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build admittance-circle-fit.pdf from the text and figures in this directory.

    python3 research/admittance-circle-fit/make_pdf.py

No LaTeX on this machine, so the document is assembled with reportlab. Two
constraints follow: the built-in fonts are WinAnsi, so no Greek and no maths
glyphs (write "Gamma", "<=", "+-", "R2"), and every figure is sized by hand to
the text width.
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
OUT = os.path.join(HERE, "admittance-circle-fit.pdf")

INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#6b6b6b")
RULE = colors.HexColor("#d8d8d8")

MARGIN = 22 * mm
WIDTH = A4[0] - 2 * MARGIN

S = dict(
    title=ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=16,
                         leading=20, textColor=INK, spaceAfter=4),
    subtitle=ParagraphStyle("subtitle", fontName="Helvetica", fontSize=9.5,
                            leading=13.5, textColor=MUTED, spaceAfter=3),
    meta=ParagraphStyle("meta", fontName="Helvetica", fontSize=7.5, leading=11,
                        textColor=MUTED, spaceAfter=13),
    h=ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=10, leading=13.5,
                     textColor=INK, spaceBefore=14, spaceAfter=5),
    lead=ParagraphStyle("lead", fontName="Helvetica", fontSize=9.2,
                        leading=13.8, textColor=INK, spaceAfter=8),
    body=ParagraphStyle("body", fontName="Helvetica", fontSize=8.8,
                        leading=13.2, textColor=INK, alignment=TA_LEFT,
                        spaceAfter=7),
    cap=ParagraphStyle("cap", fontName="Helvetica-Oblique", fontSize=7.5,
                       leading=10.5, textColor=MUTED, spaceBefore=4,
                       spaceAfter=12),
    code=ParagraphStyle("code", fontName="Courier", fontSize=7.6, leading=10.5,
                        textColor=INK, spaceAfter=8, leftIndent=8),
    ref=ParagraphStyle("ref", fontName="Helvetica", fontSize=7.8, leading=11.5,
                       textColor=MUTED, spaceAfter=6),
)

MONO = "<font name='Courier' size='8'>%s</font>"


def rule():
    t = Table([[""]], colWidths=[WIDTH], rowHeights=[0.4])
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.5, RULE)]))
    return t


def table(data, widths, align_right=(), unit_row=False):
    t = Table(data, colWidths=widths, hAlign="LEFT")
    head_last = 1 if unit_row else 0
    style = [
        ("FONT", (0, 0), (-1, head_last), "Helvetica-Bold", 7.5),
        ("FONT", (0, head_last + 1), (-1, -1), "Helvetica", 7.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("LINEBELOW", (0, head_last), (-1, head_last), 0.6, INK),
        ("LINEBELOW", (0, head_last + 1), (-1, -2), 0.25, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if unit_row:
        style += [("FONT", (0, 1), (-1, 1), "Helvetica", 6.6),
                  ("TEXTCOLOR", (0, 1), (-1, 1), MUTED),
                  ("LINEBELOW", (0, 0), (-1, 0), 0, colors.white)]
    for col in align_right:
        style.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def figure(name, width_mm, caption):
    path = os.path.join(FIG, name)
    iw, ih = ImageReader(path).getSize()
    w = width_mm * mm
    return [Image(path, width=w, height=w * ih / iw, hAlign="CENTER"),
            Paragraph(caption, S["cap"])]


def build():
    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN,
                          rightMargin=MARGIN, topMargin=20 * mm,
                          bottomMargin=18 * mm,
                          title="Two circle fits on one admittance locus",
                          author="openQCM NEXT")
    frame = Frame(MARGIN, 18 * mm, WIDTH, A4[1] - 38 * mm, id="f",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, 11 * mm,
                          "openQCM NEXT - branch impedance-analysis - 2026-08-28")
        canvas.drawRightString(A4[0] - MARGIN, 11 * mm,
                               str(canvas.getPageNumber()))
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, 14 * mm, A4[0] - MARGIN, 14 * mm)
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=footer)])

    P = lambda t, s="body": Paragraph(t, S[s])            # noqa: E731
    story = []

    # ------------------------------------------------------------------ head
    story += [
        P("Two circle fits on one admittance locus", "title"),
        P("Quantitative comparison of the two Butterworth-Van Dyke circle "
          "estimates openQCM NEXT computes from the same measured admittance: "
          "the overlay in the main window's impedance panel and the fit in the "
          "live admittance-fit window.", "subtitle"),
        P("Branch impedance-analysis. Archived five-overtone air sweep, "
          "2026-08-28. Every number reproduced by compare_circle_fits.py.",
          "meta"),
        rule(),
    ]

    # --------------------------------------------------------------- summary
    story += [
        P("Summary", "h"),
        P("The two circles differ by 0.9 % to 10.1 % in radius, hence 0.9 % to "
          "11.3 % in the implied R1, with a sign that never changes: the "
          "panel's circle is always the smaller one.", "lead"),
        P("The cause is <b>which points are fitted</b>, not which algorithm "
          "fits them. Restricting the fit to abs(f - f_s) <= 1 half width "
          "reproduces almost the entire difference on its own; swapping the "
          "estimator while keeping the whole band accounts for at most a third "
          "of it, and on some overtones for nothing.", "lead"),
        P("That selection matters at all only because the measured locus is "
          "<b>not a circle</b>. Its radial residual against the best-fit circle "
          "is 1.5 % to 4.3 % of the radius and is smooth and systematic, not "
          "scatter. The disagreement scales with that residual across the five "
          "overtones: R2 = 0.92, slope 3.0.", "lead"),
        P("The quantity that separates the two views is therefore a "
          "model-error diagnostic, not a numerical accident. Where the BVD "
          "circle describes the data (n = 5, residual 1.5 %) the two agree to "
          "0.9 %; where it does not (n = 1, residual 4.3 %) they diverge by "
          "10 %. Neither estimate reaches the datalog: both views are "
          "display-only.", "lead"),
    ]

    # --------------------------------------------------------------- section 1
    story += [
        P("1 &nbsp; The two estimators", "h"),
        P("Both read the same three buffers - " + MONO % "get_G_exact_buffer"
          + ", " + MONO % "get_B_exact_buffer" + ", "
          + MONO % "get_F_G_values_buffer" + " - populated by MultiscanProcess "
          "from the exact complex inversion, and both draw a dashed circle over "
          "the measured locus."),
        table([
            ["", "main-window panel", "live fit window"],
            ["implementation", "MainWindow._fit_circle_taubin\n(ui/mainWindow.py)",
             "fit1_circle\n(sweep_data/fit_admittance.py)"],
            ["domain", "decimated to ~250 samples, then\nabs(f - f_s) <= 1 half width",
             "decimated to 250 samples, whole\npublished band, +- 3 half widths"],
            ["cost function", "Taubin algebraic, then up to 6\nrounds of 2-sigma trimming",
             "Taubin as initial guess, then\northogonal-distance least squares"],
            ["derived output", "none; the circle is the result",
             "theta, f_s, Gamma from the arc,\nR1, L1, C1, residual"],
        ], [26 * mm, 66 * mm, 74 * mm]),
        Spacer(1, 9),
        P("The producer publishes +- 3 half widths, so the two domains differ "
          "by a factor of three in span and roughly a factor of three in sample "
          "count. Measured against the reference centre, the band subtends "
          "293-304 degrees and the core 176-187 degrees."),
    ]
    story += figure("fig2_point-selection.png", 130,
                    "Conductance of the fundamental. Blue: the published band, "
                    "and the whole of what the fit window fits. Red: the core "
                    "the panel restricts itself to.")

    # --------------------------------------------------------------- section 2
    story += [
        P("2 &nbsp; Magnitude of the disagreement", "h"),
        P("Both estimators started from the identical array. R1 = 1 / 2r, so a "
          "radius short by 10 % is a resistance high by 11 %."),
        table([
            ["n", "r ref", "r panel", "dr", "R1 ref", "R1 panel", "dR1",
             "band", "core"],
            ["", "mS", "mS", "%", "ohm", "ohm", "%", "pts", "pts"],
            ["1", "13.385", "12.029", "-10.1", "37.36", "41.56", "+11.3", "355", "119"],
            ["3", "20.025", "18.868", "-5.8", "24.97", "26.50", "+6.1", "255", "85"],
            ["5", "9.407", "9.320", "-0.9", "53.15", "53.65", "+0.9", "387", "129"],
            ["7", "6.250", "6.077", "-2.8", "80.00", "82.27", "+2.8", "259", "87"],
            ["9", "3.855", "3.708", "-3.8", "129.71", "134.84", "+4.0", "251", "84"],
        ], [10 * mm] + [20 * mm] * 6 + [16 * mm] * 2,
            align_right=tuple(range(1, 9)), unit_row=True),
        Spacer(1, 9),
        P("The centre moves consistently as well: on the fundamental from "
          "(12.761, -1.445) mS to (14.824, -1.904) mS, towards higher "
          "conductance, along the direction of the retained arc."),
    ]

    # --------------------------------------------------------------- section 3
    story += [
        P("3 &nbsp; Decomposition: domain against estimator", "h"),
        P("The two views differ in two respects at once. Running the four "
          "combinations separates them. Reference is the geometric fit on the "
          "whole band; values are radius relative to it."),
        table([
            ["n", "Taubin + trim, whole band", "geometric, core",
             "Taubin + trim, core (the panel)"],
            ["1", "-3.8 %", "-9.9 %", "-10.1 %"],
            ["3", "-1.3 %", "-5.6 %", "-5.8 %"],
            ["5", "-0.0 %", "-1.0 %", "-0.9 %"],
            ["7", "-0.8 %", "-3.3 %", "-2.8 %"],
            ["9", "-2.3 %", "-4.5 %", "-3.8 %"],
        ], [12 * mm, 50 * mm, 40 * mm, 50 * mm], align_right=(1, 2, 3)),
        Spacer(1, 9),
        P("The domain dominates. Keeping the geometric estimator and "
          "restricting it to the core already yields -9.9 % of the -10.1 % "
          "measured on the fundamental; the estimator alone, on the full band, "
          "yields -3.8 %. Once the domain is the core, which estimator runs on "
          "it is close to irrelevant. The effects are not additive, consistent "
          "with both being expressions of one underlying cause rather than two "
          "independent errors."),
    ]
    story += figure("fig3_decomposition.png", 128,
                    "Radius relative to the reference fit, by variant and "
                    "overtone.")

    # --------------------------------------------------------------- section 4
    story += [
        P("4 &nbsp; Why the domain matters: the locus is not a circle", "h"),
        P("If the data lay on a circle, any consistent estimator on any subset "
          "containing three non-collinear points would return the same circle, "
          "and the table above would be zero throughout. It is not, so the "
          "model is incomplete. The residual quantifies by how much."),
    ]
    story += figure("fig5_radial-residual.png", 130,
                    "Signed radial residual against the best-fit circle, as a "
                    "percentage of the radius, versus frequency in half widths. "
                    "Dotted lines mark the core boundary.")
    story += [
        P("The residual is a smooth function of frequency, not noise: on the "
          "fundamental it is +10 % of the radius at resonance and -7 % near "
          "+-1 half width, changing sign three times across the band. Its "
          "turning points sit at the core boundary, which is precisely why the "
          "choice of domain is consequential. A circle constrained to pass "
          "through an arc that bulges outward in its middle and inward at its "
          "ends settles at a smaller radius; a circle fitted to the whole band "
          "averages the excursion out."),
        P("Across the five overtones the disagreement tracks the residual."),
    ]
    story += figure("fig4_residual-vs-disagreement.png", 92,
                    "Disagreement in radius against the circle-model residual, "
                    "one point per overtone.")
    story += [
        P("R2 = 0.92, Pearson 0.961, Spearman 0.900, slope 3.0 - each "
          "percentage point of circle-model residual buys about three "
          "percentage points of radius disagreement. With five points this is "
          "an association, not a law, but the ordering is unambiguous and the "
          "mechanism is visible directly in the residual."),
        P("The residual also settles which fit is preferable on its own terms. "
          "Over the whole band the reference circle leaves 4.33 % rms on the "
          "fundamental and the panel's circle 17.91 %. Over the core only the "
          "ordering reverses, 5.88 % against 2.95 %, as it must, since that is "
          "the domain the panel optimised. Each estimator wins where it was "
          "fitted: the signature of model error, not of one estimator being "
          "numerically better."),
    ]
    story += figure("fig1_two-circles.png", 104,
                    "Fundamental. Grey: the published band. Black: the core. "
                    "Blue: geometric fit on the whole band. Red: the panel. "
                    "Purple: geometric fit on the core, which almost coincides "
                    "with the panel and confirms the domain as the cause.")

    # --------------------------------------------------------------- section 5
    story += [
        P("5 &nbsp; What this affects", "h"),
        P("Within the fit window the radius enters R1 = 1 / 2r and through it "
          "L1 and C1. f_s and Gamma are read from the arc - from the centre and "
          "the rotation theta, not the radius - so they are affected only "
          "through the centre displacement, and second-order in it."),
        P("The panel reports no numbers at all; it draws a circle. The overlay "
          "is therefore the entire visible consequence, and the practical rule "
          "is that it must not be read as an estimate of R1."),
        P("Neither path reaches the datalog: _update_impedance_panel is "
          "display-only, and the logged frequency and dissipation still come "
          "from the approximate formula in MultiscanProcess. A disagreement of "
          "10 % between the two overlays leaves the logged record untouched."),
        P("The fit window is the reference of the two, by construction rather "
          "than by argument: ui/impedanceFitWindow.py imports "
          "sweep_data/fit_admittance.py by file path, so the live figures and "
          "the offline script cannot diverge. Keeping both is deliberate: two "
          "estimates whose difference measures model error are more informative "
          "than one number that looks authoritative."),
    ]

    # --------------------------------------------------------------- section 6
    story += [
        P("6 &nbsp; Method", "h"),
        P("cd software<br/>QT_QPA_PLATFORM=offscreen python3 \\<br/>"
          "&nbsp;&nbsp;../research/admittance-circle-fit/compare_circle_fits.py "
          "openQCM/sweep_data", "code"),
        P("The argument is a directory of g1.txt ... g9.txt as written by the "
          "sweep dump, and defaults to the path above. Those files are "
          "overwritten by every acquisition, so pass a copy when the numbers "
          "have to stay put."),
        P("The script rebuilds the admittance with the offline admittance(), "
          "applies the AD8302 ratio mask and the +- 3 half-width clip that "
          "MultiscanProcess applies, then runs both estimators on that single "
          "array - the same array both views receive at run time. Qt is "
          "required only because the panel's estimator is a static method on "
          "MainWindow; nothing is displayed. The decomposition of section 3 and "
          "the residuals of section 4 use the same preparation, with "
          "geometric_circle called directly for the mixed cases."),
    ]

    # --------------------------------------------------------------- section 7
    story += [
        P("7 &nbsp; Limits", "h"),
        P("One instrument, one sweep, air. The residual is expected to grow in "
          "liquid, where damping widens the resonance and pushes more of the "
          "band into the AD8302 dynamic-range corner, but that has not been "
          "measured, and with it the extrapolation of section 4 is untested."),
        P("The origin of the non-circularity is not attributed here. The "
          "residual is smooth and antisymmetric-plus-peak in shape, which is "
          "consistent with an unmodelled series element, with a "
          "frequency-dependent error in the amplitude or phase calibration, or "
          "with the constant-baseline removal applied before publication. "
          "Distinguishing these requires a measurement this document does not "
          "contain."),
        P("The reference is itself a fit, not ground truth. Where the model "
          "residual is 4 % of the radius, calling any one of these circles "
          "correct to better than a few percent is not supported by the data."),
    ]

    story += [
        P("References", "h"),
        P("Taubin, G. (1991). Estimation of planar curves, surfaces and "
          "nonplanar space curves defined by implicit equations, with "
          "applications to edge and range image segmentation. IEEE Transactions "
          "on Pattern Analysis and Machine Intelligence 13(11), 1115-1138. "
          "The algebraic estimator used as the panel's fit and as the initial "
          "guess of the geometric one.", "ref"),
        P("Chernov, N. and Lesort, C. (2005). Least squares fitting of circles. "
          "Journal of Mathematical Imaging and Vision 23, 239-252. The "
          "geometric, orthogonal-distance formulation and its relation to the "
          "algebraic estimators.", "ref"),
    ]

    doc.build(story)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
