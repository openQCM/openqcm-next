#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 15:30:37 2023

@author: marco
"""

# VER 0.1.5a_G_DEV
# plot conductance data 

import numpy as np
from numpy import loadtxt
import matplotlib.pyplot as plt
import tkinter as Tk
import math
from math import factorial
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import InterpolatedUnivariateSpline
from openQCM.core.constants import Constants


# SAVITZKY - GOLAY FILTER 
# -------------------------------------------------------------------------
def savitzky_golay(y, window_size, order, deriv=0, rate=1):
 
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order)) 
    except ValueError as msg:
        raise ValueError("WARNING: window size and order have to be of type int!")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("WARNING: window size must be a positive odd number!")
    if window_size < order + 2:
        raise TypeError("WARNING: window size is too small for the polynomials order!")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')


# LOAD PEAK FREQUENCIES FILE 
# -------------------------------------------------------------------------
def load_frequencies_file():
    data  = loadtxt(Constants.cvs_peakfrequencies_path)
    peaks_mag = data[:,0]
    #peaks_phase = data[:,1] #unused at the moment
    return peaks_mag

# LOAD CALIBRATION FILE 
# -------------------------------------------------------------------------
def load_calibration_file():
    # Loads Fundamental frequency and Overtones from file
    peaks_mag = load_frequencies_file()

    # Checks QCM type 5Mhz or 10MHz
    if (peaks_mag[0] >4e+06 and peaks_mag[0]<6e+06):
       filename = Constants.csv_calibration_path
    elif (peaks_mag[0] >9e+06 and peaks_mag[0]<11e+06):
       filename = Constants.csv_calibration_path10 
    
    # get calibration data all
    data  = loadtxt(filename)
    freq_all  = data[:,0]
    mag_all   = data[:,1]
    phase_all = data[:,2]
    
    return freq_all, mag_all, phase_all


# BASELINE CORRECTION
# -------------------------------------------------------------------------
def baseline_correction(x,y,poly_order):
    
    # Estimate Baseline with Least Squares Polynomial Fit (LSP)
    coeffs = np.polyfit(x,y,poly_order)
    # Evaluate a polynomial at specific values
    poly_fitted = np.polyval(coeffs,x) 
    return poly_fitted, coeffs    

# BASELINE COEFFICIENTS 
# -------------------------------------------------------------------------  
def baseline_coeffs():
    
    # initializations
    polyfitted_all = None
    coeffs_all = None
    polyfitted_all_phase = None
    coeffs_all_phase = None
    
    # loads Calibration (baseline correction) from file
    (freq_all, mag_all, phase_all) = load_calibration_file()
    
    # VER 0.1.6G convert mag_all to Vmag_all
    Vmag_all = (mag_all * 0.03) + 0.3
    
    # Baseline correction: input signal Amplitude (sweep all frequencies)
    (polyfitted_all, coeffs_all) = baseline_correction(freq_all, Vmag_all, 8)
    mag_beseline_corrected_all= Vmag_all - polyfitted_all

    return coeffs_all


def _Vmag_mirror (Vmag): 
        # mirroring gain signal 
        
        # find the frequency of maximum gain 
        idx_max = np.argmax(Vmag)
        
        # init an array of len = 2 * idmax
        if (2*idx_max < len(Vmag)):
            Vmag_mir = np.empty([2*idx_max])
        else: 
            # init an array of len = len(Vph)
            Vmag_mir = np.empty([len(Vmag)])
        
        # copy 
        Vmag_mir[:idx_max] = Vmag[:idx_max]
        
        # mirror
        if (2*idx_max < len(Vmag)):
            for nn in range (idx_max):
                Vmag_mir[(idx_max ) + nn] = Vmag[ idx_max - nn]
        else:
            for nn in (range (len(Vmag) - idx_max) ):
                Vmag_mir[(idx_max ) + nn] = Vmag[ idx_max - nn]
        
        # create the nan filling array 
        if ((len(Vmag) - 2*idx_max) > 0): 
            a = np.empty(len(Vmag) - 2*idx_max)
            a.fill(np.nan)
            # append nan
            Vmag_mir = np.append(Vmag_mir, a)
       
# =============================================================================
#         import matplotlib.pyplot as plt
#         plt.title("V mag mirror")
#         plt.plot(Vmag_mir)
#         plt.show()
# =============================================================================
        
        return (Vmag_mir)
    
def _Vph_mirror (Vph):
        #mirroring phase signal 
        # find the frequency of maximum phase 
        idx_max = np.argmax(Vph)
        
        if (2*idx_max < len(Vph)):
            # init an array of len = 2 * idmax
            Vph_mir = np.empty([2*idx_max])
        else: 
            # init an array of len = len(Vph)
            Vph_mir = np.empty([len(Vph)])
            
# =============================================================================
#         print ("IDX MAX = ", idx_max)
#         print ("LEN OF VPH = ", len(Vph) )
# =============================================================================
        
        # copy 
        Vph_mir[:idx_max] = Vph[:idx_max]
        
        # mirror
        if (2*idx_max < len(Vph)):
            for nn in range (idx_max):
                Vph_mir[(idx_max ) + nn] = Vph[ idx_max - nn]
        else:
            for nn in (range (len(Vph) - idx_max) ):
                Vph_mir[(idx_max ) + nn] = Vph[ idx_max - nn]
        
        # create the nan filling array 
        if ((len(Vph) - 2*idx_max) > 0): 
            a = np.empty(len(Vph) - 2*idx_max)
            a.fill(np.nan)
         
            # append nan
            Vph_mir = np.append(Vph_mir, a)
        
# =============================================================================
#         import matplotlib.pyplot as plt
#         plt.title("V phase mirror")
#         plt.plot(Vph_mir)
#         plt.show()
# =============================================================================
        
        return (Vph_mir)
    
    # impedance from Vmag 
def _Zabs_Vmag(V_mag): 
       
        R_add = 52.3    
        Zabs = R_add * ( 10**( (0.9 - V_mag)/0.6 ) ) + R_add
        
# =============================================================================
#         import matplotlib.pyplot as plt
#         plt.plot(Zabs)
#         plt.show()
# =============================================================================
    
        return Zabs
    
# phase from V phase 
def _phase_V_phase(Vph_var): 
        
        phase = (1.8 - Vph_var) / 0.01
        # flip over the min
        im_min = np.nanargmin(phase)
        # shift 
        phase = phase - phase[im_min] 
        # flip 
        phase[im_min:] = phase[im_min] - ( phase[im_min:] - phase[im_min] )
        # ph[im_min:] = -ph[im_min:]
        
# =============================================================================
#         import matplotlib.pyplot as plt
#         plt.title("phase")
#         plt.plot(phase)
#         plt.show()
# =============================================================================
        
        return phase

# phase raw from V phase 
def _phase_raw_V_phase(Vph_var): 
        
        phase = (1.8 - Vph_var) / 0.01
# =============================================================================
#         # flip over the min
#         im_min = np.nanargmin(phase)
#         # shift 
#         phase = phase - phase[im_min] 
#         # flip 
#         phase[im_min:] = phase[im_min] - ( phase[im_min:] - phase[im_min] )
#         # ph[im_min:] = -ph[im_min:]
# =============================================================================
        
# =============================================================================
#         import matplotlib.pyplot as plt
#         plt.title("phase")
#         plt.plot(phase)
#         plt.show()
# =============================================================================
        
        return phase
    
def _mag_V_mag(Vmag_var):
    # mag = log(Vina/Vinb)
    mag = (Vmag_var - 0.9)/0.6 
    
    return mag


def _phase_corr(phase):
    # init an array of len = len(phase)
    phase_corr = np.empty([len(phase)])
    # find the inex corresponding to phase = level level is near zero fr example 2 degree 
    for nn in range (len(phase)): 
        if (phase [nn] < 2):
            idx = nn
            break 
    
    # copy the phase until idx 
    phase_corr[:nn] = phase[:nn]
    # mirror and flip down the phase after idx 
    for ii in (range (len(phase) - idx)):
        # mirror and flip 
        phase_corr[idx + ii] = -(phase[idx - ii] - phase[idx]) + phase[idx]
        
        
    return phase_corr
    
def _G_calc(Zabs, phase): 
        phase_rad = np.deg2rad(phase)
        G = np.cos(phase_rad)/Zabs
        
# =============================================================================
#         import matplotlib.pyplot as plt
#         plt.title ("Conductance")
#         plt.plot(G)
#         plt.show()
# =============================================================================
        
        return G

def _B_calc(Zabs, phase):
        phase_rad = np.deg2rad(phase)
        B = np.sin(phase_rad)/Zabs
        
# =============================================================================
#         import matplotlib.pyplot as plt
#         plt.title("susceptance")
#         plt.plot(B)
#         plt.show()
# =============================================================================
        
        return B
    
def _Freq_G (G_conductance, F_sweep): 
        idx_max = np.nanargmax(G_conductance)
        print (idx_max)
        f_resonance = F_sweep[idx_max]
        
# =============================================================================
#         print (f_resonance)
# =============================================================================
        
        return idx_max, f_resonance
    
def _half_bandwidth_G(G_conductance,  F_sweep):
        # find min 
        min_G = np.nanmin(G_conductance)
        print (" G min value = ", min_G)
        # shift down
        G_conductance = G_conductance - min_G
        # find max value 
        max_G = np.nanmax(G_conductance)
        print (" G max value = ", max_G)
        max_half_G = max_G/2 
        print (" G max half value = ", max_half_G)
     
        for nn in range (len (G_conductance)):
            if (G_conductance[nn] > max_half_G):
                idx_l = nn
                print ("G index hwhm = ", idx_l)
                break 
        # find max index
        idx_max = np.nanargmax(G_conductance)
        
        bw = F_sweep[idx_max] - F_sweep[idx_l]   
        
        return idx_l, bw 
        

def _plot (plot_title, yaxis_label, x, y): 
    
    fig, axs = plt.subplots(3, 2)
    fig.tight_layout()
    
    axs[0,0].plot(x[0], y[0], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[0],  linewidth = 0)
    #axs[0,0].plot(xx_1_a, amp_1_a_sp, 'k',  linewidth = 2)
    axs[0,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,0].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "Fundamental" )

   
    axs[0,1].plot(x[1], y[1], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[1], linewidth = 0)
    #axs[0,1].plot(xx_3_a, amp_3_a_sp, 'k',  linewidth = 2)
    axs[0,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,1].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "3-rd Overtone" )

    
    axs[1,0].plot(x[2], y[2], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[2], linewidth = 0)
    #axs[1,0].plot(xx_5_a, amp_5_a_sp, 'k',  linewidth = 2)
    axs[1,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,0].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "5-th Overtone" )

   
    axs[1,1].plot(x[3], y[3], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[3], linewidth = 0)
    #axs[1,1].plot(xx_7_a, amp_7_a_sp, 'k',  linewidth = 2)
    axs[1,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,1].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "7-th Overtone" )

    
    axs[2,0].plot(x[4], y[4], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[4], linewidth = 0)
    #axs[2,0].plot(xx_9_a, amp_9_a_sp, 'k',  linewidth = 2)
    axs[2,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[2,0].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "9-th Overtone" )

    # turn off the axis of a last subplot in the grid 
    plt.title(plot_title)
    axs[-1, -1].axis('off')
    plt.tight_layout()
    plt.show()
    
def _plot_marker (plot_title, yaxis_label, x, y, idx_max, idx_left): 
    fig, axs = plt.subplots(3, 2)
    fig.tight_layout()
    
    axs[0,0].plot(x[0], y[0], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[0],  linewidth = 0)
    #axs[0,0].plot(xx_1_a, amp_1_a_sp, 'k',  linewidth = 2)
    axs[0,0].plot(x[0][idx_max[0]], y[0][idx_max[0]], 'xr', markersize = 20)
    axs[0,0].plot(x[0][idx_left[0]], y[0][idx_left[0]], 'xr', markersize = 20)
    axs[0,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,0].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "Fundamental" )

    axs[0,1].plot(x[1], y[1], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[1], linewidth = 0)
    #axs[0,1].plot(xx_3_a, amp_3_a_sp, 'k',  linewidth = 2)
    axs[0,1].plot(x[1][idx_max[1]], y[1][idx_max[1]], 'xr', markersize = 20)
    axs[0,1].plot(x[1][idx_left[1]], y[1][idx_left[1]], 'xr', markersize = 20)
    axs[0,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,1].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "3-rd Overtone" )

    
    axs[1,0].plot(x[2], y[2], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[2], linewidth = 0)
    #axs[1,0].plot(xx_5_a, amp_5_a_sp, 'k',  linewidth = 2)
    axs[1,0].plot(x[2][idx_max[2]], y[2][idx_max[2]], 'xr', markersize = 20)
    axs[1,0].plot(x[2][idx_left[2]], y[2][idx_left[2]], 'xr', markersize = 20)
    axs[1,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,0].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "5-th Overtone" )

   
    axs[1,1].plot(x[3], y[3], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[3], linewidth = 0)
    #axs[1,1].plot(xx_7_a, amp_7_a_sp, 'k',  linewidth = 2)
    axs[1,1].plot(x[3][idx_max[3]], y[3][idx_max[3]], 'xr', markersize = 20)
    axs[1,1].plot(x[3][idx_left[3]], y[3][idx_left[3]], 'xr', markersize = 20)
    axs[1,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,1].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "7-th Overtone" )

    
    axs[2,0].plot(x[4], y[4], marker = 'o', markersize = 1, color = Constants.plot_color_multi_g[4], linewidth = 0)
    #axs[2,0].plot(xx_9_a, amp_9_a_sp, 'k',  linewidth = 2)
    axs[2,0].plot(x[4][idx_max[4]], y[4][idx_max[4]], 'xr', markersize = 20)
    axs[2,0].plot(x[4][idx_left[4]], y[4][idx_left[4]], 'xr', markersize = 20)
    axs[2,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[2,0].set( ylabel = yaxis_label, xlabel = "Frequency (Hz)", title = "9-th Overtone" )

    # turn off the axis of a last subplot in the grid 
    plt.title(plot_title)
    axs[-1, -1].axis('off')
    plt.tight_layout()
    plt.show()               
                   
                   

def script():
    print ("PLOT CONDUCTANCE")    
    
    # %% VMAG VPHASE GET RAW DATA
    # get raw data sweep files
    fileName_1_a = "openQCM" + "/" + "sweep_data" + "/" + "g1.txt"
    fileName_3_a = "openQCM" + "/" + "sweep_data" + "/" + "g3.txt"
    fileName_5_a = "openQCM" + "/" + "sweep_data" + "/" + "g5.txt"
    fileName_7_a = "openQCM" + "/" + "sweep_data" + "/" + "g7.txt"
    fileName_9_a = "openQCM" + "/" + "sweep_data" + "/" + "g9.txt"
    
    # get all raw data from files
    dataAll_1_a = loadtxt(fileName_1_a)
    dataAll_3_a = loadtxt(fileName_3_a)
    dataAll_5_a = loadtxt(fileName_5_a)
    dataAll_7_a = loadtxt(fileName_7_a)
    dataAll_9_a = loadtxt(fileName_9_a)

    # get frequency amplitude and phase data for each overtone
    frq_1_a = dataAll_1_a[:, 0]
    amp_1_a = dataAll_1_a[:, 1]
    phs_1_a = dataAll_1_a[:, 2]

    frq_3_a = dataAll_3_a[:, 0]
    amp_3_a = dataAll_3_a[:, 1]
    phs_3_a = dataAll_3_a[:, 2]

    frq_5_a = dataAll_5_a[:, 0]
    amp_5_a = dataAll_5_a[:, 1]
    phs_5_a = dataAll_5_a[:, 2]

    frq_7_a = dataAll_7_a[:, 0]
    amp_7_a = dataAll_7_a[:, 1]
    phs_7_a = dataAll_7_a[:, 2]

    frq_9_a = dataAll_9_a[:, 0]
    amp_9_a = dataAll_9_a[:, 1]
    phs_9_a = dataAll_9_a[:, 2]
    
    
    # %% VMAG ROUTINE
    # -------------------------------------------------------------------------
    # BASELINE CORRECTION
    # -------------------------------------------------------------------------
    # polynomial values for baseline correction for each overtones 
    polyfitted_list = [0,0,0,0,0]
    # get the coefficient of the calibration polinomial 
    coeffs_all = baseline_coeffs()
    
    # 1
    polyfitted_list[0] = np.polyval(coeffs_all, frq_1_a) 
    # 3
    polyfitted_list[1] = np.polyval(coeffs_all, frq_3_a) 
    # 5
    polyfitted_list[2] = np.polyval(coeffs_all, frq_5_a) 
    # 7
    polyfitted_list[3] = np.polyval(coeffs_all, frq_7_a) 
    # 9
    polyfitted_list[4] = np.polyval(coeffs_all, frq_9_a) 
    
    # init amplitude baseline corrected 
    amp_1_a_b = 0
    amp_3_a_b = 0
    amp_5_a_b = 0
    amp_7_a_b = 0
    amp_9_a_b = 0
    
    amp_1_a_b = amp_1_a - polyfitted_list[0]
    amp_3_a_b = amp_3_a - polyfitted_list[1]
    amp_5_a_b = amp_5_a - polyfitted_list[2]
    amp_7_a_b = amp_7_a - polyfitted_list[3]
    amp_9_a_b = amp_9_a - polyfitted_list[4] 
    
    # FILTERING
    # SAVITZKY - GOLAY FILTER 
    # -------------------------------------------------------------------------
    amp_1_a_filter = 0
    amp_3_a_filter = 0
    amp_5_a_filter = 0
    amp_7_a_filter = 0
    amp_9_a_filter = 0
    
    
    # SG window size array depending on ovettone 
    sg_window_size = [Constants.SG_WINDOW_SIZE_G, 
                      Constants.SG_WINDOW_SIZE_G, 
                      Constants.SG_WINDOW_SIZE_G, 
                      Constants.SG_WINDOW_SIZE_G,
                      Constants.SG_WINDOW_SIZE_G]
    
    # SG order 
    sg_order = [Constants.SG_order, Constants.SG_order, Constants.SG_order, Constants.SG_order, Constants.SG_order]
    
    # prototype: 
    # savitzky_golay(y, window_size, order, deriv=0, rate=1):  
    # usage: 
    # filtered_mag = self.savitzky_golay(mag_beseline_corrected, window_size = SG_window_size, order = Constants.SG_order)
    
    amp_1_a_filter = savitzky_golay(amp_1_a_b, window_size = sg_window_size[0], order = Constants.SG_order)
    amp_3_a_filter = savitzky_golay(amp_3_a_b, window_size = sg_window_size[1], order = Constants.SG_order)
    amp_5_a_filter = savitzky_golay(amp_5_a_b, window_size = sg_window_size[2], order = Constants.SG_order)
    amp_7_a_filter = savitzky_golay(amp_7_a_b, window_size = sg_window_size[3], order = Constants.SG_order)
    amp_9_a_filter = savitzky_golay(amp_9_a_b, window_size = sg_window_size[4], order = Constants.SG_order)
    
    
    # SPLINE ROUTINE 
    # -------------------------------------------------------------------------
    # init spline variable 
    amp_1_a_sp = 0
    amp_3_a_sp = 0
    amp_5_a_sp = 0
    amp_7_a_sp = 0
    amp_9_a_sp = 0
    
    spline_factor = [Constants.SPLINE_FACTOR_G,
                     Constants.SPLINE_FACTOR_G, 
                     Constants.SPLINE_FACTOR_G, 
                     Constants.SPLINE_FACTOR_G, 
                     Constants.SPLINE_FACTOR_G]
   

    # SPLINE FITTING 
    s_1_a = UnivariateSpline(frq_1_a, amp_1_a_filter, s = spline_factor[0])
    xx_1_a = np.arange(frq_1_a[0],frq_1_a[-1], 1)
    amp_1_a_sp = s_1_a(xx_1_a)

    s_3_a = UnivariateSpline(frq_3_a, amp_3_a_filter, s = spline_factor[1])
    xx_3_a = np.arange(frq_3_a[0],frq_3_a[-1], 1)
    amp_3_a_sp = s_3_a(xx_3_a)

    s_5_a = UnivariateSpline(frq_5_a, amp_5_a_filter, s = spline_factor[2])
    xx_5_a = np.arange(frq_5_a[0],frq_5_a[-1], 1)
    amp_5_a_sp = s_5_a(xx_5_a)

    s_7_a = UnivariateSpline(frq_7_a, amp_7_a_filter, s = spline_factor[3])
    xx_7_a = np.arange(frq_7_a[0],frq_7_a[-1], 1)
    amp_7_a_sp = s_7_a(xx_7_a)

    s_9_a = UnivariateSpline(frq_9_a, amp_9_a_filter, s = spline_factor[4])
    xx_9_a = np.arange(frq_9_a[0],frq_9_a[-1], 1)
    amp_9_a_sp = s_9_a(xx_9_a)
    
    # create array 
    frq_a_sp = [xx_1_a, xx_3_a, xx_5_a, xx_7_a, xx_9_a]
    amp_a_sp = [amp_1_a_sp, amp_3_a_sp, amp_5_a_sp, amp_7_a_sp, amp_9_a_sp]

    
    # %% VPHASE ROUTINE
    # -------------------------------------------------------------------------
    # FILTERING
    # SAVITZKY - GOLAY FILTER 
    # -------------------------------------------------------------------------
    phs_1_a_filter = 0
    phs_3_a_filter = 0
    phs_5_a_filter = 0
    phs_7_a_filter = 0
    phs_9_a_filter = 0
    
     
    # SG window size array depending on ovettone 
    sg_window_size = [Constants.SG_WINDOW_SIZE_G, 
                      Constants.SG_WINDOW_SIZE_G, 
                      Constants.SG_WINDOW_SIZE_G, 
                      Constants.SG_WINDOW_SIZE_G, 
                      Constants.SG_WINDOW_SIZE_G]
    
    # SG order 
    sg_order = [Constants.SG_order, Constants.SG_order, Constants.SG_order, Constants.SG_order, Constants.SG_order]
    
    # prototype: 
    # savitzky_golay(y, window_size, order, deriv=0, rate=1):  
    # usage: 
    # filtered_mag = self.savitzky_golay(mag_beseline_corrected, window_size = SG_window_size, order = Constants.SG_order)
    
    phs_1_a_filter = savitzky_golay(phs_1_a, window_size = sg_window_size[0], order = Constants.SG_order)
    phs_3_a_filter = savitzky_golay(phs_3_a, window_size = sg_window_size[1], order = Constants.SG_order)
    phs_5_a_filter = savitzky_golay(phs_5_a, window_size = sg_window_size[2], order = Constants.SG_order)
    phs_7_a_filter = savitzky_golay(phs_7_a, window_size = sg_window_size[3], order = Constants.SG_order)
    phs_9_a_filter = savitzky_golay(phs_9_a, window_size = sg_window_size[4], order = Constants.SG_order)
    
    # SPLINE ROUTINE 
    # -------------------------------------------------------------------------
    # init spline variable 
    phs_1_a_sp = 0
    phs_3_a_sp = 0
    phs_5_a_sp = 0
    phs_7_a_sp = 0
    phs_9_a_sp = 0
    
    spline_factor = [Constants.SPLINE_FACTOR_G,
                     Constants.SPLINE_FACTOR_G, 
                     Constants.SPLINE_FACTOR_G, 
                     Constants.SPLINE_FACTOR_G, 
                     Constants.SPLINE_FACTOR_G]
   

    # SPLINE FITTING 
    s_1_a = UnivariateSpline(frq_1_a, phs_1_a_filter, s = spline_factor[0])
    xx_1_a = np.arange(frq_1_a[0],frq_1_a[-1], 1)
    phs_1_a_sp = s_1_a(xx_1_a)

    s_3_a = UnivariateSpline(frq_3_a, phs_3_a_filter, s = spline_factor[1])
    xx_3_a = np.arange(frq_3_a[0],frq_3_a[-1], 1)
    phs_3_a_sp = s_3_a(xx_3_a)

    s_5_a = UnivariateSpline(frq_5_a, phs_5_a_filter, s = spline_factor[2])
    xx_5_a = np.arange(frq_5_a[0],frq_5_a[-1], 1)
    phs_5_a_sp = s_5_a(xx_5_a)

    s_7_a = UnivariateSpline(frq_7_a, phs_7_a_filter, s = spline_factor[3])
    xx_7_a = np.arange(frq_7_a[0],frq_7_a[-1], 1)
    phs_7_a_sp = s_7_a(xx_7_a)

    s_9_a = UnivariateSpline(frq_9_a, phs_9_a_filter, s = spline_factor[4])
    xx_9_a = np.arange(frq_9_a[0],frq_9_a[-1], 1)
    phs_9_a_sp = s_9_a(xx_9_a)
    
    # create array of phase signal filtered and spline 
    frq_a_sp = [xx_1_a, xx_3_a, xx_5_a, xx_7_a, xx_9_a]
    phs_a_sp = [phs_1_a_sp, phs_3_a_sp, phs_5_a_sp, phs_7_a_sp, phs_9_a_sp]
    
    # %% FIND MAX VMAG

    # find frequency of maximum V mag 
    frq_1_a_min = xx_1_a[np.argmin(amp_1_a_sp, axis = 0)]
    frq_1_a_max = xx_1_a[np.argmax(amp_1_a_sp, axis = 0)]

    frq_3_a_min = xx_3_a[np.argmin(amp_3_a_sp, axis = 0)]
    frq_3_a_max = xx_3_a[np.argmax(amp_3_a_sp, axis = 0)]

    frq_5_a_min = xx_5_a[np.argmin(amp_5_a_sp, axis = 0)]
    frq_5_a_max = xx_5_a[np.argmax(amp_5_a_sp, axis = 0)]

    frq_7_a_min = xx_7_a[np.argmin(amp_7_a_sp, axis = 0)]
    frq_7_a_max = xx_7_a[np.argmax(amp_7_a_sp, axis = 0)]

    frq_9_a_min = xx_9_a[np.argmin(amp_9_a_sp, axis = 0)]
    frq_9_a_max = xx_9_a[np.argmax(amp_9_a_sp, axis = 0)]


    # V mag max init 
    frq_a_max = [0,0,0,0,0]
    amp_a_sp_max = [0,0,0,0,0]
    
    # frequency of maximum V phase 
    frq_a_max = [frq_1_a_max, frq_3_a_max, frq_5_a_max, frq_7_a_max, frq_9_a_max]
    # maximum V mag 
    for i in range(len(amp_a_sp_max)):
        amp_a_sp_max[i] = amp_a_sp[i][np.argmax(amp_a_sp[i], axis = 0)]
    
    
    # %% FIND MAX VPHASE
    # find frequency of maximum V mag 
    frq_1_a_min = xx_1_a[np.argmin(phs_1_a_sp, axis = 0)]
    frq_1_a_max_p = xx_1_a[np.argmax(phs_1_a_sp, axis = 0)]

    frq_3_a_min = xx_3_a[np.argmin(phs_3_a_sp, axis = 0)]
    frq_3_a_max_p = xx_3_a[np.argmax(phs_3_a_sp, axis = 0)]

    frq_5_a_min = xx_5_a[np.argmin(phs_5_a_sp, axis = 0)]
    frq_5_a_max_p = xx_5_a[np.argmax(phs_5_a_sp, axis = 0)]

    frq_7_a_min = xx_7_a[np.argmin(phs_7_a_sp, axis = 0)]
    frq_7_a_max_p= xx_7_a[np.argmax(phs_7_a_sp, axis = 0)]

    frq_9_a_min = xx_9_a[np.argmin(phs_9_a_sp, axis = 0)]
    frq_9_a_max_p = xx_9_a[np.argmax(phs_9_a_sp, axis = 0)]


    # V mag max init 
    frq_a_max_p = [0,0,0,0,0]
    phs_a_sp_max = [0,0,0,0,0]
    
    # frequency of maximum V phase 
    frq_a_max_p = [frq_1_a_max_p, frq_3_a_max_p, frq_5_a_max_p, frq_7_a_max_p, frq_9_a_max_p]
    # maximum V phase 
    for i in range(len(phs_a_sp_max)):
        phs_a_sp_max[i] = phs_a_sp[i][np.argmax(phs_a_sp[i], axis = 0)]
    
    
    # %%PLOT RAW V MAG
    fig, axs = plt.subplots(3, 2)
    fig.tight_layout()
    
    axs[0,0].plot(frq_1_a, amp_1_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[0],  linewidth = 0)
    axs[0,0].plot(xx_1_a, amp_1_a_sp, 'k',  linewidth = 2)
    axs[0,0].plot(frq_1_a_max, amp_a_sp_max[0], 'xr', markersize = 20)
    axs[0,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,0].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "Fundamental" )

   
    axs[0,1].plot(frq_3_a, amp_3_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[1], linewidth = 0)
    axs[0,1].plot(xx_3_a, amp_3_a_sp, 'k',  linewidth = 2)
    axs[0,1].plot(frq_3_a_max, amp_a_sp_max[1], 'xr', markersize = 20)
    axs[0,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,1].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "3-rd Overtone" )

    
    axs[1,0].plot(frq_5_a, amp_5_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[2], linewidth = 0)
    axs[1,0].plot(xx_5_a, amp_5_a_sp, 'k',  linewidth = 2)
    axs[1,0].plot(frq_5_a_max, amp_a_sp_max[2], 'xr', markersize = 20)
    axs[1,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,0].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "5-th Overtone" )

   
    axs[1,1].plot(frq_7_a, amp_7_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[3], linewidth = 0)
    axs[1,1].plot(xx_7_a, amp_7_a_sp, 'k',  linewidth = 2)
    axs[1,1].plot(frq_7_a_max, amp_a_sp_max[3], 'xr', markersize = 20)
    axs[1,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,1].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "7-th Overtone" )

    
    axs[2,0].plot(frq_9_a, amp_9_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[4], linewidth = 0)
    axs[2,0].plot(xx_9_a, amp_9_a_sp, 'k',  linewidth = 2)
    axs[2,0].plot(frq_9_a_max, amp_a_sp_max[4], 'xr', markersize = 20)
    axs[2,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[2,0].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "9-th Overtone" )

    # turn off the axis of a last subplot in the grid 
    axs[-1, -1].axis('off')
    plt.title("Vmag raw and filtered")
    plt.tight_layout()
    plt.show()
    
    # Measure the difference between frequency of V max max and frequency of V phase max 
    print ("****************************************************************** ")
    print ("Frequency of maximum difference : F_Max (V mag) - F_Max (V phase")
    print ("****************************************************************** ")
    for i in range (len (frq_a_max_p)): 
        print ("Overtone = ", (2 * i + 1), "DF_max = ", frq_a_max[i] - frq_a_max_p[i])
    
    
   
    # %%PLOT RAW V MAG BASELINE
    fig, axs = plt.subplots(3, 2)
    fig.tight_layout()
    
    axs[0,0].plot(frq_1_a, amp_1_a_b, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[0],  linewidth = 0)
    axs[0,0].plot(xx_1_a, amp_1_a_sp, 'k',  linewidth = 2)
    axs[0,0].plot(frq_1_a_max, amp_a_sp_max[0], 'xr', markersize = 20)
    axs[0,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,0].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "Fundamental" )

   
    axs[0,1].plot(frq_3_a, amp_3_a_b, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[1], linewidth = 0)
    axs[0,1].plot(xx_3_a, amp_3_a_sp, 'k',  linewidth = 2)
    axs[0,1].plot(frq_3_a_max, amp_a_sp_max[1], 'xr', markersize = 20)
    axs[0,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,1].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "3-rd Overtone" )

    
    axs[1,0].plot(frq_5_a, amp_5_a_b, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[2], linewidth = 0)
    axs[1,0].plot(xx_5_a, amp_5_a_sp, 'k',  linewidth = 2)
    axs[1,0].plot(frq_5_a_max, amp_a_sp_max[2], 'xr', markersize = 20)
    axs[1,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,0].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "5-th Overtone" )

   
    axs[1,1].plot(frq_7_a, amp_7_a_b, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[3], linewidth = 0)
    axs[1,1].plot(xx_7_a, amp_7_a_sp, 'k',  linewidth = 2)
    axs[1,1].plot(frq_7_a_max, amp_a_sp_max[3], 'xr', markersize = 20)
    axs[1,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,1].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "7-th Overtone" )

    
    axs[2,0].plot(frq_9_a, amp_9_a_b, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[4], linewidth = 0)
    axs[2,0].plot(xx_9_a, amp_9_a_sp, 'k',  linewidth = 2)
    axs[2,0].plot(frq_9_a_max, amp_a_sp_max[4], 'xr', markersize = 20)
    axs[2,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[2,0].set( ylabel = "V mag (V)", xlabel = "Frequency (Hz)", title = "9-th Overtone" )

    # turn off the axis of a last subplot in the grid 
    axs[-1, -1].axis('off')
    plt.title("Vmag baseline corr and filtered")
    plt.tight_layout()
    plt.show()
   
    # %% PLOT RAW V PHASE

    fig, axs = plt.subplots(3, 2)
    fig.tight_layout()
    
    axs[0,0].plot(frq_1_a, phs_1_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[0],  linewidth = 0)
    axs[0,0].plot(xx_1_a, phs_1_a_sp, 'k',  linewidth = 2)
    axs[0,0].plot(frq_1_a_max_p, phs_a_sp_max[0], 'xr', markersize = 20)
    axs[0,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,0].set( ylabel = "V phase (V)", xlabel = "Frequency (Hz)", title = "Fundamental" )

   
    axs[0,1].plot(frq_3_a, phs_3_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[1], linewidth = 0)
    axs[0,1].plot(xx_3_a, phs_3_a_sp, 'k',  linewidth = 2)
    axs[0,1].plot(frq_3_a_max_p, phs_a_sp_max[1], 'xr', markersize = 20)
    axs[0,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,1].set( ylabel = "V phase (V)", xlabel = "Frequency (Hz)", title = "3-rd Overtone" )

    
    axs[1,0].plot(frq_5_a, phs_5_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[2], linewidth = 0)
    axs[1,0].plot(xx_5_a, phs_5_a_sp, 'k',  linewidth = 2)
    axs[1,0].plot(frq_5_a_max_p, phs_a_sp_max[2], 'xr', markersize = 20)
    axs[1,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,0].set( ylabel = "V phase (V)", xlabel = "Frequency (Hz)", title = "5-th Overtone" )

   
    axs[1,1].plot(frq_7_a, phs_7_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[3], linewidth = 0)
    axs[1,1].plot(xx_7_a, phs_7_a_sp, 'k',  linewidth = 2)
    axs[1,1].plot(frq_7_a_max_p, phs_a_sp_max[3], 'xr', markersize = 20)
    axs[1,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,1].set( ylabel = "V phase (V)", xlabel = "Frequency (Hz)", title = "7-th Overtone" )

    
    axs[2,0].plot(frq_9_a, phs_9_a, marker = 'o', markersize = 2, color = Constants.plot_color_multi_g[4], linewidth = 0)
    axs[2,0].plot(xx_9_a, phs_9_a_sp, 'k',  linewidth = 2)
    axs[2,0].plot(frq_9_a_max_p, phs_a_sp_max[4], 'xr', markersize = 20)
    axs[2,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[2,0].set( ylabel = "V phase (V)", xlabel = "Frequency (Hz)", title = "9-th Overtone" )

    # turn off the axis of a last subplot in the grid 
    plt.title("Vphase raw and filtered")
    axs[-1, -1].axis('off')
    plt.tight_layout()
    plt.show()
    

    # %% PHASE RAW 
    # CALC PHASE raw from V phase 
    
    phs_1_a_sp_p = 0
    phs_3_a_sp_p = 0
    phs_5_a_sp_p = 0
    phs_7_a_sp_p = 0
    phs_9_a_sp_p = 0
    
    # init array 
    phs_a_sp_p = [phs_1_a_sp_p, phs_3_a_sp_p, phs_5_a_sp_p, phs_7_a_sp_p, phs_9_a_sp_p]
    
    # def _phase_V_phase(Vph_var): 
    for i in (range (len(phs_a_sp))): 
        phs_a_sp_p[i] = _phase_raw_V_phase(phs_a_sp[i])
        
    # _plot("phase from V phase", "degree", frq_a_sp, phs_a_sp_p)    
    
    
    
# =============================================================================
#     # ROUTINE 
#     # PHASE CORREECTION: Because of the uncertainty around the phase maximum
#     # %% ----------------------------------------------------------------------
#     # init array 
#     phs_1_a_sp_p_corr = 0
#     phs_3_a_sp_p_corr = 0
#     phs_5_a_sp_p_corr = 0
#     phs_7_a_sp_p_corr = 0 
#     phs_9_a_sp_p_corr = 0
#     
#     phs_a_sp_p_corr = [phs_1_a_sp_p_corr, phs_3_a_sp_p_corr, phs_5_a_sp_p_corr, phs_7_a_sp_p_corr, phs_9_a_sp_p_corr]
#     
#     for i in (range (len(phs_a_sp_p))): 
#         phs_a_sp_p_corr[i] = _phase_corr(phs_a_sp_p[i])
#     
#     _plot("phase flip and shift", frq_a_sp, phs_a_sp_p_corr)    
# =============================================================================
    
    # %% MAG RAW 
    # defined as log(VINPA/VINPB)
    amp_1_a_sp_m = 0
    amp_3_a_sp_m = 0
    amp_5_a_sp_m = 0
    amp_7_a_sp_m = 0
    amp_9_a_sp_m = 0
    
    amp_a_sp_m = [amp_1_a_sp_m, amp_3_a_sp_m, amp_5_a_sp_m, amp_7_a_sp_m, amp_9_a_sp_m]
    
    for i in range (len (amp_a_sp_m)):
        amp_a_sp_m[i] = _mag_V_mag(amp_a_sp[i])
    
    # _plot("mag from V mag", "decade", frq_a_sp, amp_a_sp_m)   
    
    
    # %% FIND MIN PHASE RAW
    # find frequency of maximum V mag 
    frq_1_a_min_p = xx_1_a[np.argmin(phs_a_sp_p[0], axis = 0)]
    frq_1_a_max_p = xx_1_a[np.argmax(phs_a_sp_p[0], axis = 0)]

    frq_3_a_min_p = xx_3_a[np.argmin(phs_a_sp_p[1], axis = 0)]
    frq_3_a_max_p = xx_3_a[np.argmax(phs_a_sp_p[1], axis = 0)]

    frq_5_a_min_p = xx_5_a[np.argmin(phs_a_sp_p[2], axis = 0)]
    frq_5_a_max_p = xx_5_a[np.argmax(phs_a_sp_p[2], axis = 0)]

    frq_7_a_min_p = xx_7_a[np.argmin(phs_a_sp_p[3], axis = 0)]
    frq_7_a_max_p= xx_7_a[np.argmax(phs_a_sp_p[3], axis = 0)]

    frq_9_a_min_p = xx_9_a[np.argmin(phs_a_sp_p[4], axis = 0)]
    frq_9_a_max_p = xx_9_a[np.argmax(phs_a_sp_p[4], axis = 0)]


    # phase min init 
    frq_a_min_p = [0,0,0,0,0]
    phs_a_sp_p_min = [0,0,0,0,0]
    
    # frequency of maximum V phase 
    frq_a_min_p = [frq_1_a_min_p, frq_3_a_min_p, frq_5_a_min_p, frq_7_a_min_p, frq_9_a_min_p]
    # maximum V phase 
    for i in range(len(phs_a_sp_p_min)):
        phs_a_sp_p_min[i] = phs_a_sp_p[i][np.argmin(phs_a_sp_p[i], axis = 0)]
   
   
    # %% FIND MAX MAG RAW 
    # find frequency of maximum V mag 
    frq_1_a_min_mag = xx_1_a[np.argmin(amp_a_sp_m[0], axis = 0)]
    frq_1_a_max_mag = xx_1_a[np.argmax(amp_a_sp_m[0], axis = 0)]

    frq_3_a_min_mag = xx_3_a[np.argmin(amp_a_sp_m[1], axis = 0)]
    frq_3_a_max_mag = xx_3_a[np.argmax(amp_a_sp_m[1], axis = 0)]

    frq_5_a_min_mag = xx_5_a[np.argmin(amp_a_sp_m[2], axis = 0)]
    frq_5_a_max_mag = xx_5_a[np.argmax(amp_a_sp_m[2], axis = 0)]

    frq_7_a_min_mag = xx_7_a[np.argmin(amp_a_sp_m[3], axis = 0)]
    frq_7_a_max_mag = xx_7_a[np.argmax(amp_a_sp_m[3], axis = 0)]

    frq_9_a_min_mag = xx_9_a[np.argmin(amp_a_sp_m[4], axis = 0)]
    frq_9_a_max_mag = xx_9_a[np.argmax(amp_a_sp_m[4], axis = 0)]


    # V mag max init 
    frq_a_max_mag = [0,0,0,0,0]
    amp_a_sp_m_max = [0,0,0,0,0]
    
    # frequency of maximum V phase 
    frq_a_max_mag = [frq_1_a_max_mag, frq_3_a_max_mag, frq_5_a_max_mag, frq_7_a_max_mag, frq_9_a_max_mag]
    # maximum V mag 
    for i in range(len(amp_a_sp_max)):
        amp_a_sp_m_max[i] = amp_a_sp_m[i][np.argmax(amp_a_sp_m[i], axis = 0)]
    
    
    # Measure the difference between frequency of V max max and frequency of V phase max 
    print ("****************************************************************** ")
    print ("Frequency of maximum difference : F_Max (mag) - F_Min (phase")
    print ("****************************************************************** ")
    for i in range (len (frq_a_max_p)): 
        print ("Overtone = ", (2 * i + 1), "F_max (mag) = ", frq_a_max_mag[i])
        print ("Overtone = ", (2 * i + 1), "F_min (phase) = ",  frq_a_min_p[i])
        print ("Overtone = ", (2 * i + 1), "DF_max = ", frq_a_max_mag[i] - frq_a_min_p[i])
    
    # %% PLOT MAG and PHASE 
    
    _plot("mag from V mag", "decade", frq_a_sp, amp_a_sp_m)   
    _plot("phase from V phase", "degree", frq_a_sp, phs_a_sp_p)

   
    # %% CALC IMPEDANCE from VMAG
    
    # impedance from Vmag 
    Z_abs_0 = 0
    Z_abs_3 = 0
    Z_abs_5 = 0
    Z_abs_7 = 0
    Z_abs_9 = 0
    
    Z_abs = [Z_abs_0, Z_abs_3, Z_abs_5, Z_abs_7, Z_abs_9]
    

    # impedance from Vmag 
    # def _Zabs_Vmag(V_mag): 
    for i in range (len (amp_a_sp)): 
         Z_abs[i] = _Zabs_Vmag(amp_a_sp[i])
     
    _plot("impedance modulus ", "Z-modulus", frq_a_sp, Z_abs)

    # %% CALC CONDUCTANCE 
    
    G_0 = 0
    G_3 = 0
    G_5 = 0
    G_7 = 0
    G_9 = 0

    G = [G_0, G_3, G_5, G_7, G_9]
    
    for i in range (len (Z_abs)):
       # def _G_calc(Zabs, phase): 
       G[i] = _G_calc(Z_abs[i], phs_a_sp_p[i])
    
       
    G_mS = [0,0,0,0,0]
    for i in range (len (G_mS)): 
        G_mS[i] = G[i]*1000
    _plot("conductance ", "mS", frq_a_sp, G_mS)     
    
    
    # %% CALC FREQ AND BW
    idx = [0,0,0,0,0]
    idx_l = [0,0,0,0,0]
    F = [0,0,0,0,0]
    BW = [0,0,0,0,0]
    
    for i in range (len (G)):
        idx[i], F[i] = _Freq_G(G[i], frq_a_sp[i])
        idx_l[i], BW[i] = _half_bandwidth_G(G[i], frq_a_sp[i])
    
    
    print ("idx =", idx )
    print ("F = ", F)
    print ("idx left = ", idx_l)
    print ("BW = ", BW)
    
    
    G_shifted = [0,0,0,0,0]
    G_min = [0,0,0,0,0]
    
    for i in range (len(G_shifted)):
        # find min 
        # G_min[i] = np.nanmin(G[i])
        # TODO set the minimum as the mean of the firts 100 sample 
        G_min[i] = np.average(G[i][:100])
        # shift down
        G_shifted[i] = G[i] - G_min[i]
    
    _plot("conductance shifted", "mS", frq_a_sp, G_shifted)   
    
    # %% PLOT CONDUCTANCE MARKER 
    _plot_marker("conductance shifted", "mS", frq_a_sp, G_shifted, idx, idx_l)
    
# =============================================================================
#     # ROUTINE 
#     # MIRROR V mag 
#     # %% ----------------------------------------------------------------------
#     # amp_a_sp = [amp_1_a_sp, amp_3_a_sp, amp_5_a_sp, amp_7_a_sp, amp_9_a_sp]
#     # mirror voltage amp 
#     amp_1_a_sp_m = 0
#     amp_3_a_sp_m = 0
#     amp_5_a_sp_m = 0
#     amp_7_a_sp_m = 0
#     amp_9_a_sp_m = 0
#     
#     amp_a_sp_m = [amp_1_a_sp_m, amp_3_a_sp_m, amp_5_a_sp_m, amp_7_a_sp_m, amp_9_a_sp_m]
#     
#     # mirror 
#     for i in range (len(amp_a_sp)): 
#         amp_a_sp_m[i] = _Vmag_mirror(amp_a_sp[i])
#     
#     # plot
#     _plot("V mag mirror", frq_a_sp, amp_a_sp_m)
# =============================================================================
    
    # ROUTINE 
    # CALC IMPEDANCE  
    # %% ----------------------------------------------------------------------
    
# =============================================================================
#     # impedance from Vmag 
#     Z_abs_0 = 0
#     Z_abs_3 = 0
#     Z_abs_5 = 0
#     Z_abs_7 = 0
#     Z_abs_9 = 0
#     
#     Z_abs = [Z_abs_0, Z_abs_3, Z_abs_5, Z_abs_7, Z_abs_9]
# =============================================================================
    
# =============================================================================
#     # impedance from Vmag 
#     # def _Zabs_Vmag(V_mag): 
#     for i in range (len (amp_a_sp)): 
#         Z_abs[i] = _Zabs_Vmag(amp_a_sp_m[i])
#     
#     _plot("impedance modulus ", frq_a_sp, Z_abs)
# =============================================================================
    
    # ROUTINE 
    # CALC CONDUCTANCE 
    # %% ----------------------------------------------------------------------
    
# =============================================================================
#     G_0 = 0
#     G_3 = 0
#     G_5 = 0
#     G_7 = 0
#     G_9 = 0
# 
#     G = [G_0, G_3, G_5, G_7, G_9]
#     
#     for i in range (len (Z_abs)):
#        # def _G_calc(Zabs, phase): 
#        G[i] = _G_calc(Z_abs[i], phs_a_sp_p_corr[i])
#        
#     _plot("conductance ", frq_a_sp, G) 
# =============================================================================
    
# =============================================================================
#     G_shift = [0,0,0,0,0]    
#     # shift down the conductance 
#     for i in range (len(G)):
#         min_G = np.nanmin(G[i])
#         # shift down
#         G_shift[i] = G[i] - min_G
#     
#     _plot("conductance shifted down ", frq_a_sp, G_shift)  
# =============================================================================
    
    
    
    
    
    
    
    
    
    
    
    