# QCM Overtone Normalization Note

In QCM measurements, the complex frequency shift is usually normalized by the overtone number \(n\):

\[
\frac{\Delta \tilde f_n}{n}
=
\frac{\Delta f_n}{n}
+
i\frac{\Delta\Gamma_n}{n}
\]

Therefore, both the frequency shift \(\Delta f_n\) and the half-bandwidth shift \(\Delta\Gamma_n\) should be divided by \(n\).

The dissipation factor is different. Since it is defined as:

\[
D_n \simeq \frac{2\Gamma_n}{n f_0}
\]

it already contains the overtone scaling through the resonance frequency \(f_n \simeq n f_0\). Therefore, \(D_n\) should not be divided again by \(n\).

For shifts:

\[
\frac{\Delta\Gamma_n}{n}
=
\frac{f_0}{2}\Delta D_n
\]

In practice:

\[
\Delta f_n \rightarrow \Delta f_n/n
\]

\[
\Delta\Gamma_n \rightarrow \Delta\Gamma_n/n
\]

\[
\Delta D_n \rightarrow \Delta D_n
\]