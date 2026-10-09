# -*- coding: utf-8 -*-
"""
make_figures_v2b.py — Figs. 3, 4, 6, 7, 8 of manuscript v0.2, revision of 2026-10-09 (figure handoff of that date,
reviewed previews installed byte-identical; Python 3.9.12, numpy 1.21.5, pandas 1.4.2, matplotlib 3.5.1).
Called by make_figures_v2.py, which keeps Figs. 2, 5 and the SI; can also be run alone:
    python make_figures_v2b.py [--out DIR]          (default ../figures_v2)
Inputs: results/v2/asis/{shifts,t4_sweep_points,t4_ds2_datalog,phi_all,glucose_xrel}.csv, summary.json, and the two
plot palettes of the instrument software (software/openQCM/core/constants.py, read as literals, no Qt import).
Reads results only: no fit, no refit. Lines joining points are guides to the eye. All shifts are relative to the air of
the same dataset. Fig. 7 (c, d) divides each solution shift by the water shift at the SAME overtone; water is (0 %, 1)
by definition; no regression, no inferred sqrt(rho*eta) coordinate, no resolution band.
Side output: results/v2/asis/glucose_ratios_to_water.csv (the 40 ratios of Fig. 7 c, d).
"""
from pathlib import Path
import ast
import json
import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = HERE / 'results/v2/asis'
OUT = (HERE / '../figures_v2').resolve()
RATIOS_CSV = DATA / 'glucose_ratios_to_water.csv'
N = [1, 3, 5, 7, 9]
# Read literal palette assignments without importing the application or Qt.
tree = ast.parse((ROOT / 'software/openQCM/core/constants.py').read_text())
palettes = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ('plot_color_multi', 'plot_color_multi_diss'):
                palettes[target.id] = ast.literal_eval(node.value)
FC = dict(zip(N, [tuple(v / 255 for v in c) for c in palettes['plot_color_multi']]))
GC = dict(zip(N, [tuple(v / 255 for v in c) for c in palettes['plot_color_multi_diss']]))
MED = dict(air='#929292', water='#2a78d6', ipa='#159570', gluc05='#ca9500', gluc075='#d66a35', gluc10='#99468c')
ML = dict(air='Air', water='Water', ipa='Isopropanol', gluc05='Glucose 5%', gluc075='Glucose 7.5%', gluc10='Glucose 10%')
MK = dict(water='o', ipa='s', gluc05='s', gluc075='D', gluc10='^')
SH = pd.read_csv(DATA / 'shifts.csv')
PTS = pd.read_csv(DATA / 't4_sweep_points.csv')
PHI = pd.read_csv(DATA / 'phi_all.csv')
XR = pd.read_csv(DATA / 'glucose_xrel.csv').query("estimator == 'psl'").set_index('liquid')
SUMMARY = json.loads((DATA / 'summary.json').read_text())
STYLE = {
    'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.titlesize': 12,
    'axes.titleweight': 'semibold', 'axes.labelsize': 11, 'axes.labelpad': 8,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#555555',
    'axes.axisbelow': True, 'axes.grid': True, 'grid.color': '#e4e7eb',
    'grid.linewidth': .6, 'xtick.color': '#444444', 'ytick.color': '#444444',
    'legend.frameon': False, 'legend.fontsize': 9, 'savefig.dpi': 200,
    'pdf.fonttype': 42, 'lines.linewidth': 1.2,
}
CAPTIONS = {}
CHECKS = []
SOURCES = {
    'fig03_T4_time_traces': 'results/v2/asis/t4_sweep_points.csv (PSL, 45 sweeps DS-2 + 75 DS-3); t4_ds2_datalog.csv (time origin of DS-2 only)',
    'fig04_exp1_T5_KG1': 'results/v2/asis/shifts.csv (DS-2 and DS-3, water, estimators argmax_hh and psl)',
    'fig06_exp2_water_ipa': 'results/v2/asis/shifts.csv (DS-2, water and isopropanol, psl); summary.json (tabulated sqrt(rho*eta), KG coefficient)',
    'fig07_exp3_glucose': 'results/v2/asis/shifts.csv (DS-3, water and glucose, psl); glucose_xrel.csv (cross-check of the ratios); writes glucose_ratios_to_water.csv',
    'fig08_phi_all_media': 'results/v2/asis/phi_all.csv',
}

def sel(ds, liq, est='psl'):
    return SH[(SH.dataset == ds) & (SH.liquid == liq) & (SH.estimator == est)].sort_values('n')

def point(ax, x, y, color, marker='o', filled=True, err=None, size=6, **kw):
    return ax.errorbar(x, y, yerr=err, fmt=marker, linestyle='none', ms=size,
                       mfc=color if filled else 'none', mec='#414141' if filled else color,
                       mew=.45 if filled else 1.2, ecolor=color, elinewidth=1,
                       capsize=2.2 if err is not None else 0, zorder=4, **kw)

def handle(color, label, marker='o', filled=True):
    return Line2D([], [], marker=marker, ls='none', ms=6, color=color,
                  mfc=color if filled else 'none', mec='#414141' if filled else color,
                  mew=.45 if filled else 1.2, label=label)

def nlegend(ax, colors, y=1.015):
    ax.legend(handles=[handle(colors[n], f'$n={n}$') for n in N], loc='lower left',
              bbox_to_anchor=(0, y, 1, .08), mode='expand', ncol=5,
              borderaxespad=0, handletextpad=.35, columnspacing=.7, fontsize=9)

def panel(ax, letter, title):
    ax.set_title(f'({letter})  {title}', loc='left', pad=13)

def save(fig, name, caption):
    fig.canvas.draw()
    # Check text stays inside the exported canvas (legends included).
    renderer = fig.canvas.get_renderer()
    outside = []
    ticks = set()
    def collect_ticks(a):
        for axis in (a.xaxis, a.yaxis):
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                ticks.update((tick.label1, tick.label2))
        for child in a.child_axes: collect_ticks(child)
    for a in fig.axes: collect_ticks(a)
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text():
            continue
        box = t.get_window_extent(renderer)
        # Invisible/out-of-range tick labels are not drawn by Matplotlib.
        if t in ticks:
            continue
        if box.x0 < -2 or box.y0 < -2 or box.x1 > fig.bbox.width + 2 or box.y1 > fig.bbox.height + 2:
            outside.append(t.get_text())
    CHECKS.append({'figure': name, 'text_outside_canvas': outside})
    for ext in ('png', 'pdf'):
        fig.savefig(OUT / f'{name}.{ext}', facecolor='white')
    plt.close(fig)
    CAPTIONS[name] = caption
    print(name, 'saved', flush=True)

def time_traces():
    fig, axs = plt.subplots(2, 2, figsize=(12.8, 8.5), sharex='col')
    fig.subplots_adjust(left=.09, right=.985, top=.84, bottom=.085, hspace=.28, wspace=.19)
    fig.suptitle('Time evolution · phase-shifted Lorentzian', y=.985, fontsize=16, fontweight='semibold')
    fig.text(.5, .941, 'Frequency shift (blue)     |     Half-bandwidth shift (brown)', ha='center', fontsize=10, color='#555555')
    backgrounds = dict(air='#f2f3f4', water='#eaf2fb', ipa='#e6f3eb', gluc05='#faf1d7', gluc075='#f7dfca', gluc10='#e5d8f0')
    datalog_t0 = pd.to_datetime(pd.read_csv(DATA / 't4_ds2_datalog.csv').t).min()
    for col, ds in enumerate(('DS-2', 'DS-3')):
        pts = PTS[(PTS.dataset == ds) & (PTS.estimator == 'psl')].copy()
        t0 = datalog_t0 if ds == 'DS-2' else pd.to_datetime(pts.mtime).min()
        pts['tm'] = (pd.to_datetime(pts.mtime) - t0).dt.total_seconds() / 60
        assert len(pts) == (45 if ds == 'DS-2' else 75)
        for row, (field, colors) in enumerate((('df_over_n', FC), ('dG_over_n', GC))):
            a = axs[row, col]
            for n in N:
                s = pts[pts.n == n].sort_values('tm')
                a.plot(s.tm, s[field], color=colors[n], lw=1.1, zorder=3)
                point(a, s.tm, s[field], colors[n], size=5.4)
            nlegend(a, colors)
            a.set_ylabel(r'$\Delta f_n/n$ [Hz]' if row == 0 else r'$\Delta\Gamma_n/n$ [Hz]')
            a.margins(y=.14)
            if row == 1: a.set_xlabel('Time [min]')
        if ds == 'DS-2':
            bands = [(0, 37.25, 'air'), (37.25, 61.05, 'water'), (61.05, 75.3, 'ipa')]
        else:
            bounds = pts.groupby('phase').tm.agg(['min', 'max'])
            order = ['air', 'water', 'gluc05', 'gluc075', 'gluc10']
            # Keep the original phase-boundary convention; no new timing inference.
            bands = [(bounds.loc[p, 'min'] - 1.5,
                      bounds.loc[order[k+1], 'min'] - 1.5 if k+1 < len(order) else bounds.loc[p, 'max'] + 1.5, p)
                     for k,p in enumerate(order)]
        for lo, hi, medium in bands:
            for a in axs[:, col]:
                a.axvspan(lo, hi, color=backgrounds[medium], lw=0, zorder=0)
                a.axvline(lo, lw=.5, color='#d1d3d7', zorder=1)
            lab = ML[medium].replace('Glucose ', 'Glc ')
            axs[0,col].text((lo+hi)/2, .955, lab, transform=axs[0,col].get_xaxis_transform(),
                            ha='center', va='top', fontsize=9, color='#333333')
        for a in axs[:, col]: a.set_xlim(bands[0][0]-1, bands[-1][1]+1)
    fig.text(.31, .893, '(a) DS-2 · board 1920', ha='center', fontweight='semibold', fontsize=12)
    fig.text(.785, .893, '(b) DS-3 · second instrument', ha='center', fontweight='semibold', fontsize=12)
    save(fig, 'fig03_T4_time_traces', 'PSL only; Δf_n/n and ΔΓ_n/n relative to the mean of the three air sweeps of the same dataset; DS-2 time origin = start of its datalog; lines join successive sweeps of one overtone (guide to the eye); shaded bands: plateau convention of v0.2 (DS-2 fixed at 37.25 / 61.05 min; DS-3 1.5 min before the first sweep of each phase), not a liquid-change time estimate; palettes plot_color_multi (Δf) and plot_color_multi_diss (ΔΓ) of the instrument software')

def water_comparison():
    fig, ax = plt.subplots(2, 2, figsize=(11.8, 8.8), sharex=True, sharey='row',
                           gridspec_kw={'height_ratios': [1.65, 1]})
    fig.subplots_adjust(left=.105, right=.98, top=.79, bottom=.09, hspace=.15, wspace=.13)
    fig.suptitle('Air → water · estimator comparison', y=.984, fontsize=16, fontweight='semibold')
    fig.legend(handles=[handle('#555555', 'A: maximum of G + half-height', 'v', False),
                        handle('#555555', 'P: phase-shifted Lorentzian'),
                        Line2D([], [], color='#555555', label='Kanazawa–Gordon · water at 25 °C')],
               loc='upper center', bbox_to_anchor=(.5,.955), ncol=3, fontsize=9.5)
    for col, ds in enumerate(('DS-2', 'DS-3')):
        s0 = sel(ds, 'water')
        for sign in (1, -1):
            ax[0,col].plot(s0.n, sign*s0.df_KG/s0.n, color='#555555', zorder=2)
        ax[1,col].axhline(1, color='#555555', ls='--')
        for est, mk, filled, size in [('argmax_hh','v',False,11), ('psl','o',True,8)]:
            for r in sel(ds,'water',est).itertuples():
                for row,y,err,colors in [(0,r.df_over_n,r.df_sd/r.n,FC), (0,r.dG_over_n,r.dG_sd/r.n,GC), (1,r.r_KG1,r.r_KG1_sd,FC)]:
                    point(ax[row,col], r.n, y, colors[r.n], mk, filled, err, size)
        ax[0,col].set_title(f'({chr(97+col)})  {ds}' + (' · board 1920' if col == 0 else ' · second instrument'), pad=14)
        ax[1,col].set_xlabel('Overtone order $n$')
        for a in ax[:,col]: a.set_xticks(N); a.set_xlim(.5,9.5)
    for row,label in enumerate([r'$\Delta f_n/n,\ \Delta\Gamma_n/n$ [Hz]',r'KG-1: $\Delta\Gamma_n/(-\Delta f_n)$']): ax[row,0].set_ylabel(label)
    ax[1,0].set_ylim(.65,1.35)
    for y,colors,lab in [(.917,FC,'Frequency / KG-1'),(.885,GC,'Half-bandwidth')]:
        fig.legend(handles=[Line2D([],[],ls='none',label=lab)] + [handle(colors[n],f'$n={n}$') for n in N], loc='upper center', bbox_to_anchor=(.5,y), ncol=6, fontsize=9)
    save(fig,'fig04_exp1_T5_KG1','top: signed Δf_n/n and ΔΓ_n/n with ±KG for water at 25 °C (Eq. 4, measured air fundamental); bottom: r_n = ΔΓ_n/(−Δf_n), dashed y = 1; A = argmax_hh (open ▽), P = psl (filled ○); error bars: quadrature sd of the two plateaus (÷n), ratio sd propagated')

def kg_panel(ax, ds, liqs, relative=False):
    coords=[]
    for liq in liqs:
        x = float(XR.loc[liq,'x_both_n3_9']) if relative else SUMMARY['sqrt_rhoeta'][liq]
        for r in sel(ds,liq).itertuples(): coords.append((x,r.n,-r.df_over_sqrtn,r.dG_over_sqrtn))
    water=sel(ds,'water')
    slope = float(np.mean(-water[water.n>=3].df_over_sqrtn)) if relative else SUMMARY['kg_coef']['DS2']
    xmin=min(c[0] for c in coords); xmax=max(c[0] for c in coords)
    yvals=[v for c in coords for v in c[2:]]
    xpad=.035 if relative else .07
    limits=(xmin-xpad,xmax+xpad,min(yvals)-35,max(yvals)+35)
    xx=np.linspace(0,xmax+xpad,200)
    def draw(a, small=False):
        a.plot(xx,slope*xx,color='#555555',lw=1.1,zorder=2)
        for x,n,f,g in coords:
            point(a,x,f,FC[n],size=3 if small else 5.8)
            point(a,x,g,GC[n],filled=False,size=3 if small else 6.7)
    draw(ax)
    ax.set_xlim(limits[:2]); ax.set_ylim(limits[2:])
    ax.set_ylabel(r'$-\Delta f_n/\sqrt{n},\ \Delta\Gamma_n/\sqrt{n}$ [Hz]')
    ax.set_xlabel(r'$x_{\rm rel}=\sqrt{\rho\eta}/\sqrt{\rho\eta}_{\rm water}$' if relative else r'$\sqrt{\rho\eta}$ [kg m$^{-2}$ s$^{-1/2}$]')
    # Full-range context makes the zero intercept explicit without shrinking the data region.
    inset=ax.inset_axes([.08,.62,.30,.34])
    draw(inset,True)
    inset.plot(0,0,'o',color='#555555',ms=3,clip_on=False)
    inset.set_xlim(-.04,xmax+.10); inset.set_ylim(-30,max(yvals)+75)
    inset.set_xticks([0,1]); inset.set_yticks([0,800]); inset.tick_params(labelsize=7,pad=1)
    inset.set_facecolor('white'); inset.patch.set_alpha(1)
    inset.set_title('Full range · (0, 0)',fontsize=8,pad=4)
    inset.add_patch(Rectangle((limits[0],limits[2]),limits[1]-limits[0],limits[3]-limits[2],fill=False,edgecolor='#777777',ls=':',lw=.8))
    hidden=[]
    for x,n,f,g in coords:
        for y in (f,g):
            fx=(x-limits[0])/(limits[1]-limits[0]); fy=(y-limits[2])/(limits[3]-limits[2])
            if .08<=fx<=.38 and .62<=fy<=.96: hidden.append((x,n,y))
    assert not hidden, 'Inset obscures experimental points'
    CHECKS.append({'kg_dataset':ds,'points_in_zoom':all(limits[0]<=x<=limits[1] and limits[2]<=f<=limits[3] and limits[2]<=g<=limits[3] for x,n,f,g in coords),'observations':2*len(coords),'points_hidden_by_inset':hidden,'zero_intercept_visible_in_inset':True})

def kg_legends(fig, y):
    # Separate rows retain the two application palettes and identify the physical channel.
    for offset,colors,label,filled in [(0,FC,r'$-\Delta f_n/\sqrt{n}$',True),(-.036,GC,r'$\Delta\Gamma_n/\sqrt{n}$',False)]:
        handles=[Line2D([],[],ls='none',label=label)] + [handle(colors[n],f'$n={n}$',filled=filled) for n in N]
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,y+offset),ncol=6,fontsize=9,handletextpad=.3,columnspacing=1.0)

def water_ipa():
    fig,ax=plt.subplots(1,3,figsize=(15,6.3),gridspec_kw={'width_ratios':[1,1,1.4]})
    fig.subplots_adjust(left=.058,right=.985,top=.79,bottom=.27,wspace=.31)
    fig.suptitle('Water and isopropanol · DS-2 · phase-shifted Lorentzian',y=.985,fontsize=16,fontweight='semibold')
    for liq in ['water','ipa']:
        s=sel('DS-2',liq); c=MED[liq]; mk=MK[liq]
        ax[0].plot(s.n,-s.df_KG/s.n,color=c,alpha=.6)
        point(ax[0],s.n,-s.df_over_n,c,mk,True,s.df_sd/s.n)
        point(ax[0],s.n,s.dG_over_n,c,mk,False,s.dG_sd/s.n,size=7)
        ax[1].plot(s.n,s.r_KG1,color=c,lw=1)
        point(ax[1],s.n,s.r_KG1,c,mk,True,s.r_KG1_sd)
    ax[0].set_ylabel(r'$-\Delta f_n/n,\ \Delta\Gamma_n/n$ [Hz]')
    ax[1].set_ylabel(r'$\Delta\Gamma_n/(-\Delta f_n)$'); ax[1].axhline(1,color='#555555'); ax[1].set_ylim(.85,1.36)
    for a in ax[:2]: a.set_xticks(N); a.set_xlabel('Overtone order $n$'); a.set_xlim(.5,9.5)
    kg_panel(ax[2],'DS-2',['water','ipa'])
    for a,l,t in zip(ax,'abc',['T5 · normalised shifts','KG-1 · Newtonian ratio','KG-3 · experimental region']): panel(a,l,t)
    fig.legend(handles=[handle(MED[l],ML[l],MK[l]) for l in ['water','ipa']],loc='upper center',bbox_to_anchor=(.5,.943),ncol=2,fontsize=10)
    fig.text(.5,.885,'T5: filled = frequency shift; open = half-bandwidth shift; lines = Kanazawa–Gordon',ha='center',fontsize=10,color='#555555')
    kg_legends(fig,.19)
    save(fig,'fig06_exp2_water_ipa','(a) −Δf_n/n (filled), ΔΓ_n/n (open) with KG; (b) r_n, line y = 1; (c) −Δf_n/√n and ΔΓ_n/√n against tabulated √(ρη) (water 997.05 kg/m³ · 0.890 mPa s, isopropanol 781.0 · 2.038, 25 °C) with the KG line of slope summary.json kg_coef DS2; main axes zoomed on the data, inset to the model origin (0, 0), which is not a measurement')

def glucose_ratios(axes, liqs):
    water = sel('DS-3', 'water').set_index('n')
    rows = []
    for liq in liqs:
        for r in sel('DS-3', liq).itertuples():
            rf = r.df / water.loc[r.n, 'df']
            rg = r.dG / water.loc[r.n, 'dG']
            assert np.isclose(rf, XR.loc[liq, f'x_df_n{r.n}'])
            assert np.isclose(rg, XR.loc[liq, f'x_dG_n{r.n}'])
            rows.append(dict(liquid=liq, concentration_pct_wv=r.conc, n=r.n,
                             df_solution=r.df, df_water=water.loc[r.n, 'df'],
                             dG_solution=r.dG, dG_water=water.loc[r.n, 'dG'],
                             R_f=rf, R_Gamma=rg))
    ratios = pd.DataFrame(rows)
    assert (ratios.loc[ratios.liquid == 'water', ['R_f', 'R_Gamma']] == 1).all().all()
    assert (ratios.loc[ratios.liquid == 'water', 'concentration_pct_wv'] == 0).all()
    ratios.to_csv(RATIOS_CSV, index=False)
    for ax, field, colors, filled, label in [
            (axes[0], 'R_f', FC, True, r'$\Delta f_{n,\rm sol}/\Delta f_{n,\rm water}$'),
            (axes[1], 'R_Gamma', GC, False, r'$\Delta\Gamma_{n,\rm sol}/\Delta\Gamma_{n,\rm water}$')]:
        for n in N:
            s = ratios[ratios.n == n].sort_values('concentration_pct_wv')
            ax.plot(s.concentration_pct_wv, s[field], color=colors[n], lw=1.1, zorder=2)
            point(ax, s.concentration_pct_wv, s[field], colors[n], filled=filled, size=8 if filled else 9)
        ax.set_xlim(-.4, 10.4); ax.set_ylim(.985, 1.21)
        ax.set_xticks([0, 5, 7.5, 10]); ax.set_yticks([1, 1.05, 1.10, 1.15, 1.20])
        ax.set_xlabel('Glucose concentration [% w/v]')
        ax.set_ylabel(label)
        ax.text(.035, .945, 'Water: (0%, 1) for all n', transform=ax.transAxes, va='top', fontsize=9)
    CHECKS.append({'figure': 'fig07_exp3_glucose', 'ratio_values_match_existing_analysis': True,
                   'water_at_0_percent_1': True, 'ratios': 2*len(ratios),
                   'x_is_sample_concentration_pct_wv': True, 'same_y_limits_for_both_channels': True,
                   'all_ratios_visible': bool(ratios[['R_f', 'R_Gamma']].ge(.985).all().all()
                                             and ratios[['R_f', 'R_Gamma']].le(1.21).all().all())})

def glucose():
    fig, ax = plt.subplots(2,2,figsize=(13,11.3))
    fig.subplots_adjust(left=.09,right=.975,top=.835,bottom=.18,hspace=.44,wspace=.24)
    fig.suptitle('Glucose series · DS-3 · phase-shifted Lorentzian',y=.982,fontsize=16,fontweight='semibold')
    liqs=['water','gluc05','gluc075','gluc10']; s0=sel('DS-3','water')
    ax[0,0].plot(s0.n,s0.df_KG/s0.n,color='#555555')
    ax[0,0].plot(s0.n,s0.dG_KG/s0.n,color='#555555')
    for liq in liqs:
        s=sel('DS-3',liq); c=MED[liq]; mk=MK[liq]
        point(ax[0,0],s.n,s.df_over_n,c,mk,True,size=8)
        point(ax[0,0],s.n,s.dG_over_n,c,mk,False,size=9.5)
        ax[0,1].plot(s.n,s.r_KG1,color=c,lw=1)
        point(ax[0,1],s.n,s.r_KG1,c,mk,True,s.r_KG1_sd,size=8)
    ax[0,0].set_ylabel(r'$\Delta f_n/n,\ \Delta\Gamma_n/n$ [Hz]')
    ax[0,1].set_ylabel(r'$\Delta\Gamma_n/(-\Delta f_n)$'); ax[0,1].axhline(1,color='#555555',ls='--'); ax[0,1].set_ylim(.8,1.10)
    for a in ax[0]: a.set_xticks(N); a.set_xlim(.5,9.5); a.set_xlabel('Overtone order $n$')
    glucose_ratios(ax[1], liqs)
    for a,l,t in zip(ax.flat,'abcd',['T5 · signed normalised shifts','KG-1 · Newtonian ratio','Frequency · relative to water','Half-bandwidth · relative to water']): panel(a,l,t)
    fig.legend(handles=[handle(MED[l],ML[l],MK[l]) for l in liqs],loc='upper center',bbox_to_anchor=(.5,.946),ncol=4,fontsize=10)
    fig.text(.5,.906,'Concentrations in % w/v. T5: filled = frequency; open = half-bandwidth; line = KG for water at 25 °C.',ha='center',fontsize=10,color='#555555')
    for y,colors,label,filled in [(.112,FC,r'$R_{f,n}=\Delta f_{n,\rm sol}/\Delta f_{n,\rm water}$',True),
                                (.078,GC,r'$R_{\Gamma,n}=\Delta\Gamma_{n,\rm sol}/\Delta\Gamma_{n,\rm water}$',False)]:
        handles=[Line2D([],[],ls='none',label=label)] + [handle(colors[n],f'$n={n}$',filled=filled) for n in N]
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,y),ncol=6,fontsize=9,handletextpad=.3,columnspacing=1)
    fig.text(.5,.018,'Panels (c, d): air-referenced shifts divided by the water shift at the same overtone. Lines connect measurements as guides to the eye.',
             ha='center',fontsize=9,color='#555555')
    save(fig,'fig07_exp3_glucose','(a) signed Δf_n/n (filled), ΔΓ_n/n (open) with KG for water; (b) r_n, dashed y = 1; (c) R_f,n = Δf_n,sol/Δf_n,water, (d) R_Γ,n = ΔΓ_n,sol/ΔΓ_n,water at the same n against nominal concentration (% w/v), identical axes, water (0, 1) by definition; lines join points (guide to the eye), no fit, no error bars on the ratios')

def phase():
    fig,ax=plt.subplots(figsize=(12.8,7.5))
    fig.subplots_adjust(left=.09,right=.975,top=.83,bottom=.26)
    fig.suptitle('Phase rotation by medium and instrument',y=.978,fontsize=16,fontweight='semibold')
    fig.text(.5,.925,'All symbols are centred on the measured overtone order · error bars: standard deviation of three sweeps',ha='center',fontsize=10,color='#555555')
    for ds,media,filled,ls in [('DS-2',['air','water','ipa'],True,'-'),('DS-3',['air','water','gluc05','gluc075','gluc10'],False,'--')]:
        for med in media:
            s=PHI[(PHI.dataset==ds)&(PHI.medium==med)].sort_values('n')
            mk=dict(air='o',water='s',ipa='^',gluc05='D',gluc075='v',gluc10='^')[med]
            ax.plot(s.n,s.phi,color=MED[med],ls=ls,lw=1.05,zorder=2)
            point(ax,s.n,s.phi,MED[med],mk,filled,s.phi_sd.fillna(0),size=6 if filled else 8,label=f'{ds} · {ML[med]}')
    s=PHI[PHI.dataset.str.startswith('air 2026-09-03')].sort_values('n')
    ax.plot(s.n,s.phi,'x',color='#222222',ms=9,mew=1.5,label='Air · 2026-09-03',zorder=5)
    s=PHI[PHI.dataset.str.startswith('water 2026-07-28')]
    ax.plot(s.n,s.phi,'*',color=MED['water'],mec='#222222',ms=13,mew=.7,label='Water · 2026-07-28 (board unknown)',zorder=5)
    ax.axhline(0,color='#777777',lw=.8); ax.set_xticks(N); ax.set_xlim(.65,9.35); ax.set_ylim(-35,6)
    ax.set_xlabel('Overtone order $n$'); ax.set_ylabel(r'PSL rotation angle $\varphi_n$ [°]')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.16),ncol=3,fontsize=9,columnspacing=2.5)
    CHECKS.append({'phase_markers_at_exact_n':all(np.isin(line.get_xdata(),N).all() for line in ax.lines if line.get_marker() not in ('None','none','',None) and len(line.get_xdata())>0)})
    save(fig,'fig08_phi_all_media','P fit on every sweep; mean ± sd over the three replicas per medium; single sweeps for 2026-09-03 (×) and 2026-07-28 (★); every symbol at the exact n, no horizontal offset; DS-2 filled / solid, DS-3 open / dashed')

def main(out=None):
    """Draw the five figures into `out` (default ../figures_v2); return provenance rows for figure_provenance_v2.md."""
    global OUT
    if out is not None:
        OUT = Path(out).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    CAPTIONS.clear(); CHECKS.clear()
    with plt.style.context(['default', STYLE]):      # independent of rcParams set by the caller
        time_traces(); water_comparison(); water_ipa(); glucose(); phase()
    assert all(not c.get('text_outside_canvas', []) for c in CHECKS), 'Text outside canvas'
    assert all(c.get('all_ratios_visible', True) for c in CHECKS), 'Clipped ratios'
    return [dict(figure=name, source=SOURCES[name], script='research/paper/analysis/make_figures_v2b.py', params=CAPTIONS[name])
            for name in CAPTIONS]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--out', type=Path, default=None, help='output folder (default ../figures_v2)')
    main(parser.parse_args().out)
    print(json.dumps(CHECKS, indent=2))
