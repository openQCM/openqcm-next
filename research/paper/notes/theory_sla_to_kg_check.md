# Theory check: small-load approximation → Kanazawa–Gordon

Independent re-derivation of the "Theory" paragraph of the manuscript, written **before** reading
`derivations.md` §6 and the manuscript (see §7 for the comparison). Date: 2026-10-08.

Grading of every source claim: **(V)** verified from text fetched in this session, **(I)** inferred,
**(U)** unverified (source not reachable). Arithmetic in python3 (scripts in the session scratchpad;
all numbers reproduced inline).

## 0. Sources actually reached

| Source | What was obtained | Grade |
|---|---|---|
| Johannsmann, Langhoff, Leppin, *Sensors* **2021**, 21, 3490 (doi:10.3390/s21103490) | Full JATS XML with MathML from Europe PMC (PMC8157064); eqs. 1–2, 12, 20–33 transcribed from the MathML | (V) |
| Johannsmann, *The QCM in Soft Matter Research*, Springer 2015 (doi:10.1007/978-3-319-07836-6) | Table of contents; abstract and symbol glossary of Ch. 6 "The Small Load Approximation Revisited" and abstract of Ch. 9 "Homogeneous Semi-infinite Samples" (SpringerLink preview). Body text paywalled | (V) for glossary/abstracts, (U) for the equations |
| Johannsmann & Reviakine, *Nat. Rev. Methods Primers* **2024**, 4, 63 (doi:10.1038/s43586-024-00340-4) | Abstract, reference list and glossary (nature.com preview). Body text paywalled | (V) for abstract/glossary, (U) for the equations |
| Johannsmann, *PCCP* **2008**, 10, 4516 (doi:10.1039/b803960g) | **Not reached**: pubs.rsc.org answers with an interactive Cloudflare bot check (WebFetch 403, curl "Just a moment", browser pane shows the "verify you are human" widget, which I did not operate) | (U) |
| Kanazawa & Gordon, *Anal. Chem.* **1985**, 57, 1770 (doi:10.1021/ac00285a062) | **Not reached** (same Cloudflare check at pubs.acs.org; Crossref and Semantic Scholar carry no abstract). Secondary: Stanford Research Systems QCM200 manual (thinksrs.com, PDF fetched), which prints "Kanazawa's" eqn. 15 with symbol definitions and cites both 1985 papers | (U) primary, (V) secondary |
| Meléndez, Vázquez-Quesada, Delgado-Buscalioni, arXiv:2005.03380 (2020) | PDF fetched; eq. (3) is the SLA in the $f_0$-fundamental form | (V) secondary |
| Wikipedia "Quartz crystal microbalance" (raw wikitext) | SLA with $f_\mathrm{f}$ = fundamental, cites the 2015 book | (V) secondary |
| NIST Chemistry WebBook, fluid properties of water (IAPWS-95 EoS, Wagner & Pruß 2002; viscosity IAPWS 2008 / Huber et al. 2009) | ρ, η at 20–30 °C, 1 K steps, 0.101325 MPa | (V) |
| Kerscher et al., *Int. J. Thermophys.* **2024**, 45, 8 (doi:10.1007/s10765-023-03294-z, open access) | 2-propanol: measured ρ_L, η_L (Table 3), density fit Eq. 3 / Table 2, viscosity fit Eq. 5 / Table 6 | (V) |

## 1. The SLA as printed in the sources

### 1.1 Sensors 2021 (V)

Sign convention, Sect. 2: the source term is $\hat F_\mathrm{ext}\exp(\mathrm{i}\omega t)$; "Instead of
exp(iωt), one might have also written exp(−iωt). That is a matter of convention, addressed in Box 1."
Box 1 (for $\exp(+\mathrm{i}\omega t)$): $\tilde\eta=\eta'-\mathrm{i}\eta''$, $\tilde G=\mathrm{i}\omega\tilde\eta$,
$\tilde Z=(\rho\tilde G)^{1/2}=(\mathrm{i}\omega\rho\tilde\eta)^{1/2}$,
$\tilde\omega_\mathrm{res}=\omega_0+\mathrm{i}\gamma=2\pi(f_\mathrm{res}+\mathrm{i}\Gamma)$.

Definitions: $Z_q=8.8\times10^{6}\ \mathrm{kg\,m^{-2}s^{-1}}$ "is the resonator's shear-wave impedance,
$f_0$ is the frequency of the fundamental (often 5 MHz), and $n$ is the overtone order" (Sect. 1).
"The relations $c_q=(G_q/\rho_q)^{1/2}$ and $Z_q=(G_q\rho_q)^{1/2}$ were used" (after eq. 21).
Load impedance, eq. (20): $\tilde Z_L=-\hat\sigma_S/\hat v_S=\dots=-\mathrm{i}Z_q\tan(\tilde k_q d_q)$.

Implicit relation, eq. (22):
$$-\mathrm{i}Z_q\tan\!\left(\pi\frac{\Delta\tilde f}{f_0}\right)=\tilde Z_L .$$

SLA, eq. (23), obtained by "linearizing the tangent as $\tan(\pi\Delta\tilde f/f_0)\approx\pi\Delta\tilde f/f_0$"
and "evaluating the load impedance $\tilde Z_L(f)$ at the frequency of the unloaded crystal, rather than the
resonance frequency in the presence of the load":
$$\boxed{\;\frac{\Delta\tilde f}{f_0}=\frac{\mathrm{i}}{\pi Z_q}\tilde Z_L=\frac{\mathrm{i}}{\pi Z_q}\frac{-\hat\sigma_S}{\hat v_S}\;}\qquad(\text{Sensors 2021, eq. 23})$$

Overtone-normalised restatement, eq. (24):
$$\frac{\Delta f+\mathrm{i}\Delta\Gamma}{n f_0}=\frac{\Delta f+\mathrm{i}\Delta\Gamma}{f_\mathrm{ref}}
=\frac{\Delta f}{f_\mathrm{ref}}+\mathrm{i}\frac{\Delta D}{2}=\frac1n\frac{\mathrm{i}}{\pi Z_q}\tilde Z_L .$$

Semi-infinite medium, eq. (28): $\Delta\tilde f/f_0=(\mathrm{i}/(\pi Z_q))\tilde Z_\mathrm{bulk}$, and
eq. (29) ("the Gordon-Kanazawa relation [23,24]"):
$$\frac{\Delta f+\mathrm{i}\Delta\Gamma}{f_0}=\frac{\mathrm{i}}{\pi Z_q}\sqrt{\mathrm{i}\omega\rho\tilde\eta}
=\frac{-1+\mathrm{i}}{\sqrt2}\frac{1}{\pi Z_q}\sqrt{\omega\rho\tilde\eta}
=\frac{(-1+\mathrm{i})}{\sqrt\pi\,Z_q}\sqrt{f_0}\sqrt{n}\sqrt{\rho\tilde\eta}\;.$$
Followed by: "If $\tilde\eta$ is independent of frequency, $\Delta f$ and $\Delta\Gamma$ scale as $n^{1/2}$."
Sauerbrey, eq. (27): $\Delta\tilde f/f_0=(\mathrm{i}/(\pi Z_q))\,\mathrm{i}\omega m_f=-2nf_0m_f/Z_q$.
Dissipation, eq. (12): $\Delta\tilde f/n=\Delta f/n+\mathrm{i}\Delta\Gamma/n=\Delta f/n+\mathrm{i}(f_0/2)\Delta D$.
Numerical statement, Sect. 4.1: "With 5 MHz crystals, $-\Delta f/n^{1/2}=716$ Hz corresponds to a viscosity of 1 mPa s."

Summary for this source: denominator = **fundamental** $f_0$; prefactor $\mathrm{i}/(\pi Z_q)$;
convention $\exp(+\mathrm{i}\omega t)$; $Z_q=(G_q\rho_q)^{1/2}$ with the shear modulus written $G_q$;
$\tilde Z_L$ evaluated at the overtone frequency $\omega=2\pi nf_0$.

### 1.2 Springer book 2015 (glossary V, equations U)

Ch. 6 glossary: "$f_0$ — Resonance frequency at the fundamental ($f_0=Z_q/(2m_q)=Z_q/(2\rho_q d_q)$)";
"$f_n$ — Resonance frequency at overtone order n"; "$G_q$ — Shear modulus of AT-cut quartz ($G_q\approx29\times10^9$ Pa)";
"$Z_q$ — Acoustic wave impedance of AT-cut quartz ($Z_q=8.8\times10^6$ kg m$^{-2}$ s$^{-1}$)";
"$\Gamma$ — Imaginary part of a resonance frequency". Ch. 9 abstract: "The load impedance of a homogeneous,
semi-infinite medium … is equal to the material's shear-wave impedance, which leads to the
Gordon-Kanazawa-Mason result. For Newtonian liquids the QCM determines the viscosity-density product."
The SLA equation itself is in the paywalled body (Ch. 4 "Modeling the Resonator as a Parallel Plate",
pp. 49–123, and Ch. 6, pp. 143–168); its form is **(I)**: identical to eq. (23) above with $f_0$ the
fundamental (the Wikipedia article, which cites this book for the SLA, prints
$\Delta f^{*}/f_\mathrm{f}=(\mathrm{i}/(\pi Z_q))Z_L$ with "$f_\mathrm{f}$ is the frequency of the fundamental", (V) for the wikitext).

### 1.3 Nature Reviews Methods Primers 2024 (abstract/glossary V, equations U)

Abstract: "The changes in the resonance frequency, $\Delta f$, and the half-width at half-maximum of the
resonance, $\Delta\Gamma$ (closely related to the changes in the dissipation, $\Delta D$) … are proportional to
the in-phase and out-of-phase components of the area-averaged transverse stress at the resonator surface."
Glossary uses $\Delta f_n/n$, $\Delta\Gamma_n/n$, $\tilde G$ for the shear modulus,
$\tilde\eta=\eta'-\mathrm{i}\eta''$, $\tilde Z=(\rho\tilde G)^{1/2}$. Equation numbers and the printed SLA are not visible.

### 1.4 PCCP 2008 (U)

Not reached. Expected (I), from the same author's other texts: $\Delta\tilde f/f_\mathrm{f}=(\mathrm{i}/(\pi Z_q))\tilde Z_L$
with $f_\mathrm{f}$ the fundamental and $Z_q=8.8\times10^6$ kg m$^{-2}$ s$^{-1}$. Equation number unknown.

### 1.5 Secondary corroboration of the $f_0$ form (V)

Meléndez et al. 2020, eq. (3): $\Delta f+\mathrm{i}\Delta\Gamma=\mathrm{i}f_0Z_L/(\pi Z_Q)$, with "the fundamental
frequency equals $f_0=5$ MHz, the acoustic impedance of the quartz $Z_Q=8.8\times10^6$ kg/(m$^2$s)".

## 2. Derivation: Newtonian liquid inserted into the SLA

Notation: $f_F$ = fundamental ($=f_0$ of Johannsmann), $f_n=nf_F$, $\omega=2\pi f_n$,
$Z_q=\sqrt{\rho_q\mu_q}$ ($\mu_q\equiv G_q$), convention $\exp(+\mathrm{i}\omega t)$.

**Step 1 — SLA at overtone $n$** (eq. 23, with $\tilde Z_L$ evaluated at $\omega=2\pi nf_F$):
$$\Delta f_n+\mathrm{i}\Delta\Gamma_n=\frac{\mathrm{i}f_F}{\pi Z_q}\tilde Z_L(\omega).$$

**Step 2 — shear-wave impedance of a semi-infinite Newtonian liquid** (Box 1 with $\tilde\eta=\eta_L$ real):
$$\tilde Z_L=\sqrt{\mathrm{i}\omega\rho_L\eta_L}.$$
Principal root: $\sqrt{\mathrm i}=\mathrm e^{\mathrm i\pi/4}=\frac{1+\mathrm i}{\sqrt2}$ (the other root,
$-(1+\mathrm i)/\sqrt2$, has $\mathrm{Re}\,\tilde Z<0$ and would describe a wave growing into the liquid; the physical
branch is $\mathrm{Re}\,\tilde Z>0$). Hence
$$\tilde Z_L=\frac{1+\mathrm i}{\sqrt2}\sqrt{\omega\rho_L\eta_L}.$$

**Step 3 — multiply by the prefactor**, using $\mathrm i(1+\mathrm i)=\mathrm i+\mathrm i^2=-1+\mathrm i$:
$$\Delta f_n+\mathrm i\Delta\Gamma_n=\frac{f_F}{\pi Z_q}\frac{-1+\mathrm i}{\sqrt2}\sqrt{\omega\rho_L\eta_L}.$$
This is the middle member of Sensors 2021 eq. (29) (V).

**Step 4 — insert $\omega=2\pi nf_F$**: $\sqrt{\omega}=\sqrt{2\pi}\sqrt n\sqrt{f_F}$, and $\sqrt{2\pi}/(\sqrt2\,\pi)=1/\sqrt\pi$:
$$\Delta f_n+\mathrm i\Delta\Gamma_n=(-1+\mathrm i)\,\frac{f_F\sqrt{f_F}\sqrt n}{\sqrt\pi\,Z_q}\sqrt{\rho_L\eta_L}
=(-1+\mathrm i)\,\frac{\sqrt n\,f_F^{3/2}}{\sqrt\pi\,Z_q}\sqrt{\rho_L\eta_L}.$$
This is the last member of eq. (29) (V).

**Step 5 — separate real and imaginary parts** and write $Z_q=\sqrt{\rho_q\mu_q}$:
$$\boxed{\;\Delta f_n=-\sqrt n\,f_F^{3/2}\sqrt{\frac{\eta_L\rho_L}{\pi\,\mu_q\rho_q}}\;},\qquad
\boxed{\;\Delta\Gamma_n=+\sqrt n\,f_F^{3/2}\sqrt{\frac{\eta_L\rho_L}{\pi\,\mu_q\rho_q}}=-\Delta f_n\;}.$$
**No discrepancy** in sign or prefactor with the target forms.

**Equivalent forms in $f_n$.** Since $f_n^{3/2}=n^{3/2}f_F^{3/2}$,
$$\sqrt n\,f_F^{3/2}=\frac{f_n^{3/2}}{n}=f_F\sqrt{f_n},\qquad
\Delta f_n=-\frac{f_n^{3/2}}{n}\sqrt{\frac{\eta_L\rho_L}{\pi\mu_q\rho_q}}=-f_F\sqrt{f_n}\sqrt{\frac{\eta_L\rho_L}{\pi\mu_q\rho_q}}.$$
Pitfall to avoid: writing $\Delta f_n=-f_n^{3/2}\sqrt{\cdots}$ (i.e. replacing $f_F$ by $f_n$ in the fundamental-only KG
formula) overestimates the overtone shift by a factor $n$.

**Check against Kanazawa & Gordon 1985 (fundamental).** For $n=1$ the result reduces to
$$\Delta f=-f_F^{3/2}\left(\frac{\rho_L\eta_L}{\pi\mu_q\rho_q}\right)^{1/2}.$$
The primary text was not reachable (U). The SRS QCM200 manual (V, secondary) prints "Kanazawa's treatment … (eqn. 15)"
with the symbol list "$f_U$ = frequency of oscillation of unloaded crystal, $\rho_q$ = density of quartz = 2.648 g cm$^{-3}$,
$\mu_q$ = shear modulus of quartz = 2.947 × 10$^{11}$ g cm$^{-1}$ s$^{-2}$, $\rho_L$ = density of the liquid …,
$\eta_L$ = viscosity of the liquid …" and cites Anal. Chem. 57 (1985) 1770 and Anal. Chim. Acta 175 (1985) 99–105.
The equation body is garbled by text extraction (I): the token order ("$f_U$", "3/2", "$\rho_L\eta_L$", "$\pi\mu_q\rho_q$", "1/2")
is that of $\Delta f=-f_U^{3/2}(\rho_L\eta_L/(\pi\mu_q\rho_q))^{1/2}$. The manual's worked example — "a decrease in $f_0$ of 715 Hz
on transfer from vacuum to pure water at 20 °C" for 5 MHz crystals — is reproduced by that formula with NIST water at 20 °C
($\rho=998.207$, $\eta=1.0016$ mPa·s): **714.0 Hz** (computed), which confirms the $f^{3/2}$ form and the constants (V, numerical).
Second numerical cross-check: Sensors 2021 says $-\Delta f/n^{1/2}=716$ Hz for 1 mPa·s at 5 MHz; eq. (29) with
$Z_q=8.8\times10^6$, $\rho=1000$, $\eta=10^{-3}$ gives **716.8 Hz** (V).

## 3. The three KG properties, as tests, and $\Delta D_n$

With $k\equiv f_F^{3/2}\sqrt{\eta_L\rho_L/(\pi\mu_q\rho_q)}$ (a liquid-dependent constant, Hz) the SLA–KG result is
$\Delta f_n=-k\sqrt n$, $\Delta\Gamma_n=+k\sqrt n$.

- **KG-1 (acoustic ratio).** $\dfrac{\Delta\Gamma_n}{-\Delta f_n}=\dfrac{k\sqrt n}{k\sqrt n}=1$, independent of
  $\eta_L$, $\rho_L$, $n$ and $f_F$. Root cause: $\arg\sqrt{\mathrm i}=\pi/4$, so the load is at 45°; any Newtonian
  liquid and any overtone give ratio 1. (Also $\Delta f_n^2=\Delta\Gamma_n^2$, which is why Sensors 2021 eq. (30) reads
  $\rho\eta''\propto\Delta\Gamma^2-\Delta f^2=0$ for a Newtonian liquid.)
- **KG-2 ($\sqrt n$ scaling).** $\Delta f_n/\sqrt n=-k$ and $\Delta\Gamma_n/\sqrt n=+k$ are overtone-independent;
  the overtone-normalised quantities scale as $\Delta f_n/n=-k\,n^{-1/2}$ and $\Delta\Gamma_n/n=k\,n^{-1/2}$. (Contrast
  Sauerbrey: $\Delta f_n/n$ constant.)
- **KG-3 ($\sqrt{\eta\rho}$ law).** $\Delta f_n\propto\sqrt{\eta_L\rho_L}$ at fixed $n$; the QCM measures the product
  $\eta_L\rho_L$ only, not the factors (book Ch. 9 abstract, V).

**Dissipation.** From Sensors 2021 eq. (12), $\Delta D=2\Delta\Gamma/(nf_0)=2\Delta\Gamma_n/f_n$. Then
$$\Delta D_n=\frac{2\Delta\Gamma_n}{f_n}=\frac{2k\sqrt n}{nf_F}=\frac{2k}{\sqrt n\,f_F}
=2\sqrt{\frac{f_F}{n}}\sqrt{\frac{\eta_L\rho_L}{\pi\mu_q\rho_q}}
=\frac{2}{Z_q}\sqrt{\frac{\eta_L\rho_L f_F}{\pi n}}=\frac{2}{Z_q}\sqrt{\frac{\eta_L\rho_L\,f_n}{\pi}}\;\frac1n .$$
So $\Delta D_n\propto n^{-1/2}$ **and** $\propto f_F^{+1/2}$ (through $k\propto f_F^{3/2}$ divided by $f_n=nf_F$);
also $\Delta D_n\cdot\sqrt n=\text{const}$ and $\Delta D_n/\Delta D_1=n^{-1/2}$.
Equivalently $\Delta D_n=-2\Delta f_n/f_n$, i.e. the acoustic ratio in $D$-units is $\Delta D_n/(-\Delta f_n/n)=2/f_F$ for every $n$.

## 4. Numerical check

Constants: $\rho_q=2648$ kg m$^{-3}$, $\mu_q=2.947\times10^{10}$ Pa (SRS manual values in SI, V secondary; book glossary
"$G_q\approx29\times10^9$ Pa", V), $f_F=5\,004\,596$ Hz. Then $Z_q=\sqrt{\rho_q\mu_q}=8.834\times10^{6}$ kg m$^{-2}$ s$^{-1}$
(vs Johannsmann's rounded $8.8\times10^6$: −0.4 %).

Liquids at 25 °C: water $\rho=997.05$ kg m$^{-3}$, $\eta=0.890$ mPa·s (NIST WebBook at 25.000 °C, 0.101325 MPa:
997.048 kg m$^{-3}$, 890.022 µPa·s — V); isopropanol $\rho=781.0$ kg m$^{-3}$, $\eta=2.038$ mPa·s (values as given; see §5 for sourcing).

| liquid | $\sqrt{\rho\eta}$ (kg m$^{-2}$ s$^{-1/2}$) | $k$ (Hz) | $\Delta f_1$ | $\Delta f_3$ | $\Delta f_5$ | $\Delta f_7$ | $\Delta f_9$ |
|---|---|---|---|---|---|---|---|
| water 25 °C | 0.9420 | **673.57** | −673.6 | −1166.7 | −1506.2 | −1782.1 | −2020.7 |
| isopropanol 25 °C | 1.2616 | **902.11** | −902.1 | −1562.5 | −2017.2 | −2386.8 | −2706.3 |

$\Delta\Gamma_n=-\Delta f_n$ in every cell. Overtone-normalised, water: $\Delta f_n/n=-673.6,\ -388.9,\ -301.2,\ -254.6,\ -224.5$ Hz;
$\Delta D_n=269.2,\ 155.4,\ 120.4,\ 101.7,\ 89.7\times10^{-6}$ for $n=1,3,5,7,9$.
Isopropanol: $\Delta D_n=360.5,\ 208.1,\ 161.2,\ 136.3,\ 120.2\times10^{-6}$.
The expected "around 674 Hz" for water is reproduced (673.6 Hz with the NIST values as well).

**Temperature sensitivity of $\sqrt{\rho\eta}$.**

Water (NIST WebBook, IAPWS-95 density / IAPWS-2008 viscosity, V):

| T (°C) | ρ (kg m$^{-3}$) | η (µPa·s) |
|---|---|---|
| 23 | 997.541 | 932.126 |
| 25 | 997.048 | 890.022 |
| 27 | 996.516 | 850.906 |

$\dfrac{\mathrm d\ln\sqrt{\rho\eta}}{\mathrm dT}=\dfrac{\tfrac12\ln(996.516\cdot850.906)-\tfrac12\ln(997.541\cdot932.126)}{4\ \mathrm K}=\mathbf{-0.0115\ K^{-1}}$
(−1.15 %/K; density contributes −0.00026 K$^{-1}$, viscosity −0.0228 K$^{-1}$ halved). For $k=673.6$ Hz this is
$\mathrm dk/\mathrm dT\approx-7.8$ Hz K$^{-1}$ per $\sqrt n$ (≈ −7.8 Hz/K on $n=1$, −13.4 Hz/K on $n=3$, … ).

Isopropanol (Kerscher et al. 2024, V; correlations fitted to their own measurements, AARD 0.006 % for ρ and 0.31 % for η;
expanded uncertainty of η 1.5–1.9 %):
$\rho_L=\sum_{i=0}^3\rho_iT^i$ with $\rho_i=(1161.73,\,-2.5804,\,7.2987\times10^{-3},\,-9.8196\times10^{-6})$;
$\eta_L=\eta_0\exp\!\big(\sum_{i=1}^4\eta_iT^{-i}\big)$ mPa·s with $\eta_0=1.23842\times10^{-16}$,
$\eta_i=(4.37443\times10^4,\,-2.17822\times10^7,\,5.03956\times10^9,\,-4.30435\times10^{11})$.

| T (K) | ρ (kg m$^{-3}$) | η (mPa·s) |
|---|---|---|
| 296.15 | 782.62 | 2.2065 |
| 298.15 | 780.94 | 2.0738 |
| 300.15 | 779.24 | 1.9504 |

(Measured rows of their Table 3 for comparison: 293.16 K: 785.15 kg m$^{-3}$, 2.410 mPa·s; 303.16 K: 776.68, 1.780 — the fit
reproduces them to 0.01 % and 0.6 %.)
$\dfrac{\mathrm d\ln\sqrt{\rho\eta}}{\mathrm dT}=\mathbf{-0.0160\ K^{-1}}$ (−1.60 %/K; $\mathrm d\ln\eta/\mathrm dT=-0.0309$ K$^{-1}$,
$\mathrm d\ln\rho/\mathrm dT=-0.0011$ K$^{-1}$); $\mathrm dk/\mathrm dT\approx-14.4$ Hz K$^{-1}$ per $\sqrt n$.
Isopropanol is therefore ~1.4× more temperature-sensitive than water in the KG prediction.

## 5. The older internal document's water values

Old values: $\rho=1.102933$ g cm$^{-3}=1102.93$ kg m$^{-3}$, $\eta=0.010665$ g cm$^{-1}$ s$^{-1}=1.0665$ mPa·s.
Accepted (25 °C): $\rho=997.05$ kg m$^{-3}$, $\eta=0.890$ mPa·s.

- $\rho\eta$: old 1.17628 vs accepted 0.88737 kg$^2$ m$^{-4}$ s$^{-1}$ → ratio 1.3256.
- KG prediction scales with $\sqrt{\rho\eta}$ → inflation factor $\sqrt{1.3256}=\mathbf{1.151}$ (**+15.1 %**):
  $k_\mathrm{old}=775.5$ Hz vs $k=673.6$ Hz (water, $f_F=5\,004\,596$ Hz).
- Separately: density +10.6 %, viscosity +19.8 % relative to the accepted values. (Neither old value corresponds to pure
  water at any temperature; 1.103 g cm$^{-3}$ is far outside the 0.958–1.000 g cm$^{-3}$ range of liquid water.)

Accepted values and their sourcing:

- Water 25 °C: $\rho=997.048$ kg m$^{-3}$, $\eta=0.890022$ mPa·s — NIST Chemistry WebBook "Thermophysical Properties of
  Fluid Systems" (EoS: Wagner & Pruß, J. Phys. Chem. Ref. Data 31, 387 (2002); viscosity: Huber et al., J. Phys. Chem. Ref.
  Data 38, 101 (2009) = IAPWS 2008 formulation). **(V)**. The rounded 997.05 / 0.890 used above agree to <0.01 %.
- Isopropanol 25 °C: $\rho=780.9$ kg m$^{-3}$, $\eta=2.07$ mPa·s from Kerscher et al. 2024 (fit of their measurements,
  Table 3 points at 293.16 and 303.16 K bracket 298.15 K) **(V)**. The values in the prompt, 781.0 kg m$^{-3}$ and
  2.038 mPa·s, are the CRC-Handbook-type values (attribution **(U)**, not verified in this session); they agree with
  Kerscher to +0.01 % in ρ and −1.7 % in η, i.e. within Kerscher's stated 1.5–1.9 % uncertainty. Effect on $k$:
  Kerscher's values give 910.0 Hz vs 902.1 Hz (+0.9 %) — negligible against the KG level of agreement usually achieved.
- Quartz: $\rho_q=2.648$ g cm$^{-3}$, $\mu_q=2.947\times10^{11}$ g cm$^{-1}$ s$^{-2}$ ($=2648$ kg m$^{-3}$, $2.947\times10^{10}$ Pa)
  — printed in the SRS QCM200 manual in the Kanazawa section **(V, secondary)**; attribution to KG 1985 **(U)**.
  Johannsmann: $Z_q=8.8\times10^6$ kg m$^{-2}$ s$^{-1}$, $G_q\approx29$ GPa **(V)**.

## 6. Notation check

- Sensors 2021 (V): quartz shear modulus **$G_q$**; $Z_q=(G_q\rho_q)^{1/2}$; liquid viscosity $\tilde\eta=\eta'-\mathrm i\eta''$.
- Springer book 2015 glossary (V): "$G_q$ — Shear modulus of AT-cut quartz"; "$\eta_\mathrm{liq}$ — Viscosity"; $\mu$ is used for
  a *non-dimensional mass* (Eq. 6.2.9), so $\mu_q$ is **not** Johannsmann's symbol.
- Nat. Rev. Methods Primers 2024 glossary (V): $\tilde G$ for the shear modulus, $\tilde Z=(\rho\tilde G)^{1/2}$.
- Kanazawa–Gordon tradition (SRS manual, V secondary; KG 1985 U): **$\mu_q$** for the quartz shear modulus, $\rho_q$, $\rho_L$, $\eta_L$.

Conclusion: the manuscript's $\mu_q$ is the standard symbol of the Kanazawa–Gordon literature and is unambiguous;
Johannsmann's sources write $G_q$. Either is acceptable provided it is defined once ("$\mu_q$ (also written $G_q$)").
The old document's $\eta_q$ for a *modulus* is non-standard and collides with the viscosity symbol; it should not be used.
Also recommended: state the convention $\exp(+\mathrm i\omega t)$ (it fixes the sign of $\mathrm i/(\pi Z_q)$ and of
$\sqrt{\mathrm i\omega\rho\eta}$), and write explicitly that $f_F$ in the SLA denominator is the fundamental while
$\tilde Z_L$ is evaluated at $f_n=nf_F$.

## 7. Comparison with the existing notes

Read after §1–6 were written: `derivations.md` §6 ("Kanazawa–Gordon with a consistent overtone convention") and the
**Theory** paragraph of `manuscript.md` (line 108, "Kanazawa–Gordon in the small-load form normalised to the fundamental $f_F$").

**Agreements (no discrepancy):**

- SLA written as $\Delta\tilde f_n/f_F=(j/(\pi Z_q))\tilde Z_L(\omega_n)$ with $f_F$ the fundamental and $\tilde Z_L$ at $\omega_n$ — identical to Sensors 2021 eq. (23) (§1.1).
- $\tilde Z_L=\sqrt{j\omega_n\rho\eta}=\sqrt{\omega_n\rho\eta/2}\,(1+j)$ — same branch of $\sqrt{j}$ as §2, step 2; implies $\exp(+j\omega t)$.
- $\Delta f_n=-\sqrt n f_F^{3/2}\sqrt{\rho\eta/(\pi\rho_q\mu_q)}$, $\Delta\Gamma_n=-\Delta f_n$, $\Delta f_n/n\propto n^{-1/2}$ — identical to §2, step 5, and to KG-1/KG-2/KG-3.
- Sauerbrey check $\Delta f_n=-2nf_F^2m_f/Z_q$ — identical to Sensors 2021 eq. (27).
- $\Delta D_n=2\Delta\Gamma_n/(nf_F)$ and $\Delta\Gamma_n/n=(f_F/2)\Delta D_n$ — identical to Sensors 2021 eq. (12) and §3.
- Constants $\rho_q=2648$ kg m$^{-3}$, $\mu_q=2.947\times10^{10}$ Pa, $f_F=5\,004\,596$ Hz; water 997.05 / 0.890 — same as §4; water coefficient 673.6 Hz reproduced exactly.
- Newtonian ratio = 1 "independent of $\rho\eta$ and of temperature" — KG-1.
- Water temperature sensitivity −1.1 %/K with $\eta$ 0.932 → 0.851 mPa·s (23 → 27 °C): the $\eta$ values are the IAPWS ones (NIST 0.932126 / 0.850906); my −1.15 %/K rounds to theirs.

**Discrepancies / items to fix (itemised):**

1. **Isopropanol coefficient: 901.5 Hz (both documents) vs 902.1 Hz.** With the constants printed in the same sentence
   ($\rho_q$, $\mu_q$, $f_F$, 781.0 kg m$^{-3}$, 2.038 mPa·s) the formula gives $k=902.11$ Hz. 901.5 Hz is what one obtains with
   $Z_q$ rounded to $8.84\times10^6$ (901.47 Hz), whereas the water figure 673.6 Hz was computed with the unrounded
   $Z_q=\sqrt{\rho_q\mu_q}=8.8338\times10^6$ (the rounded value would give 673.1 Hz). The two liquids were evaluated with
   different $Z_q$; the manuscript should print 902.1 Hz (or 673.1/901.5 if $Z_q=8.84\times10^6$ is the stated input). The 0.07 %
   difference is immaterial for the conclusions but is an internal inconsistency. Affected: `derivations.md` §6 ("901.5 Hz $\cdot\sqrt n$")
   and `manuscript.md` line 108 ("901.5 $\sqrt n$ Hz"); check also Table 2 / §6.5 if $\Delta f_\mathrm{KG}$ for isopropanol was taken from this number.
2. **$Z_q=8.84\times10^6$ in `derivations.md` §6** should read $8.83\times10^6$ ($\sqrt{2648\cdot2.947\times10^{10}}=8.8338\times10^6$). Rounding only.
3. **Symbol clash in `derivations.md`:** $Z_q$ denotes the *electrical* impedance of the crystal in §1–§3 (and throughout the
   manuscript, $M=|Z_q+R_{17}|$) and the *acoustic* impedance $\sqrt{\rho_q\mu_q}$ in §6. The manuscript's Theory paragraph avoids the
   acoustic $Z_q$ (it writes $\sqrt{\rho\eta/(\pi\rho_q\mu_q)}$), which is the right choice; §6 of the note should do the same or use a distinct symbol.
4. **Isopropanol temperature sensitivity −1.5 %/K vs −1.6 %/K.** Not an error: the note uses $\eta=2.37/2.04/1.77$ mPa·s at
   20/25/30 °C from mixed literature sources (flagged there as scattering "by a few %"); the single consistent measured data set
   of Kerscher et al. 2024 gives −1.60 %/K at 25 °C (local slope $\mathrm d\ln\eta/\mathrm dT=-0.031$ K$^{-1}$ vs −0.029 K$^{-1}$
   for the 10-K average of the mixed values). Recommend citing Kerscher et al. 2024 and quoting −1.6 %/K (or "−1.5 to −1.6 %/K").
5. **Attribution of the overtone form.** The manuscript cites [@KanazawaGordon1985AC; @Johannsmann2021] for the $\sqrt n$ form. KG 1985
   gives the fundamental only (§2, check); the overtone generalisation is the SLA result, Sensors 2021 eq. (29) ("$\Delta f$ and
   $\Delta\Gamma$ scale as $n^{1/2}$"). The pairing of references is correct; adding the equation numbers (eq. 23 for the SLA, eq. 29 for
   the liquid) would make the provenance explicit.
6. **Notation, manuscript line 108:** the Newtonian ratio is written $\rho_N=|\Delta f|/\Delta\Gamma$ in a sentence that also uses $\rho$
   (liquid density) and $\rho_q$; a letter other than $\rho$ would avoid the collision. Johannsmann & Reviakine 2024 call the inverse
   quantity, $\Delta\Gamma/(-\Delta f)$, the "acoustic ratio" (abstract, V); the manuscript's inverse definition is legitimate but
   should be stated as such if the Primer is cited for it.
7. **Liquid property values are uncited** in the Theory paragraph. Citable: water — NIST Chemistry WebBook (IAPWS-95; viscosity
   IAPWS 2008 / Huber et al. 2009), which gives 997.048 kg m$^{-3}$ and 0.890022 mPa·s at 25 °C; isopropanol — the 781.0 / 2.038 pair
   is CRC-type (not verified here), and Kerscher et al. 2024 (open access) gives 780.9 kg m$^{-3}$ / 2.07 mPa·s (−1.7 % in $\eta$, within
   their uncertainty; $k$ changes by +0.9 %).
8. **Sign convention not stated** in either text. §6 of the note is implicitly $\exp(+j\omega t)$ (consistent with the manuscript's
   $Z_q+R_{17}=Me^{-j\phi}$ phasor algebra); one clause would make the $j/(\pi Z_q)$ prefactor unambiguous. Not an error.

No discrepancy of sign, prefactor, overtone scaling or acoustic-ratio prediction was found between the manuscript's Theory
paragraph and the sources.

## 8. What could not be fetched

- Johannsmann, PCCP 2008 (pubs.rsc.org): interactive Cloudflare bot check on the HTML and landing pages; WebFetch 403; archived copies
  (web.archive.org) are not reachable from this tool. The SLA form and equation number in that paper remain (U).
- Kanazawa & Gordon, Anal. Chem. 1985 (pubs.acs.org): same bot check; no abstract in Crossref, Semantic Scholar or Europe PMC.
  Verified only through the SRS QCM200 manual's transcription of "Kanazawa's" equation and its 715 Hz example (numerically reproduced).
  The Anal. Chim. Acta 1985 companion paper was not attempted (ScienceDirect).
- Johannsmann 2015 (SpringerLink): body text paywalled; TOC, chapter abstracts and the Ch. 6 symbol glossary were read.
- Johannsmann & Reviakine 2024 (nature.com): body paywalled; abstract, glossary and reference list were read.
- MDPI's own HTML/PDF of Sensors 2021 returns 403 to this tool; the article was read from the Europe PMC JATS/MathML XML instead (identical content).
- Dortmund Data Bank pages for 2-propanol: 404 at the guessed URLs; replaced by Kerscher et al. 2024.
