#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
# Evaluate a polynomial at specific values based on the coefficients and frequency range
self._polyfitted = np.polyval(self._coeffs_all, self._readFREQ)

# BASELINE CORRECTION ROI (raw data)
mag_beseline_corrected = mag-self._polyfitted

# FILTERING - Savitzky-Golay
filtered_mag = self.savitzky_golay(mag_beseline_corrected, window_size = SG_window_size, order = Constants.SG_order)
'''

import numpy as np
from numpy import loadtxt
import matplotlib.pyplot as plt
import tkinter as Tk
import math
from math import factorial
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import InterpolatedUnivariateSpline

from openQCM.core.constants import Constants

def foo():
    print("HELLO WORLD")
    
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


# LOAD FREQUENIES FILE 
def load_frequencies_file():
    data  = loadtxt(Constants.cvs_peakfrequencies_path)
    peaks_mag = data[:,0]
    #peaks_phase = data[:,1] #unused at the moment
    return peaks_mag

# LOAD CALIBRATION FILE 
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
    
    # Baseline correction: input signal Amplitude (sweep all frequencies)
    (polyfitted_all, coeffs_all) = baseline_correction(freq_all, mag_all, 8)
    mag_beseline_corrected_all= mag_all-polyfitted_all

    return coeffs_all


# =============================================================================
# def get_left_index(signal, amplitude_max, index_max) :
#     PERCENT_OVERTONE = 0.95
#     INDEX_OVERTONE_LEFT = index_max
#     while signal[INDEX_OVERTONE_LEFT] > PERCENT_OVERTONE * amplitude_max:
#         if INDEX_OVERTONE_LEFT < 1:
#             print('WARNING: Left value not found in prcessing data ')
#          
#             break
#         INDEX_OVERTONE_LEFT = INDEX_OVERTONE_LEFT - 1   
#     
#     return INDEX_OVERTONE_LEFT
# =============================================================================

def get_left_index(signal, amplitude_max, index_max) :
    THRESHOLD = Constants.THRESHOLD_DB
    INDEX_OVERTONE_LEFT = index_max
    while signal[INDEX_OVERTONE_LEFT] > (amplitude_max -  THRESHOLD):
        if INDEX_OVERTONE_LEFT < 1:
            print('WARNING: LEFT value not found in prcessing data ')
         
            break
        INDEX_OVERTONE_LEFT = INDEX_OVERTONE_LEFT - 1   
    
    return INDEX_OVERTONE_LEFT

def get_right_index(signal, amplitude_max, index_max) :
    THRESHOLD = Constants.THRESHOLD_DB
    INDEX_OVERTONE_RIGHT = index_max
    while signal[INDEX_OVERTONE_RIGHT] > (amplitude_max -  THRESHOLD):
        if INDEX_OVERTONE_RIGHT > len(signal-1):
            print('WARNING: RIGHT value not found in prcessing data ')
         
            break
        INDEX_OVERTONE_RIGHT = INDEX_OVERTONE_RIGHT + 1   
    
    return INDEX_OVERTONE_RIGHT

def script():

    # DEFINITION 
    # -------------------------------------------------------------------------
    # SPLINE VARIABLE DEFINITION 
    # spline facrtor 
# =============================================================================
#     Spline_factor = 0.1 
#     # spline number of points 
#     points = 500
# =============================================================================
    # -------------------------------------------------------------------------
    
    # INIT 
    # -------------------------------------------------------------------------
    # polynomial values for baseline correction for each overtones 
    polyfitted_list = [0,0,0,0,0]
    
    # TEST 
    foo()
    
    # get raw data sweep files
    fileName_1_a = "openQCM" + "/" + "sweep_data" + "/" + "1.txt"
    fileName_3_a = "openQCM" + "/" + "sweep_data" + "/" + "3.txt"
    fileName_5_a = "openQCM" + "/" + "sweep_data" + "/" + "5.txt"
    fileName_7_a = "openQCM" + "/" + "sweep_data" + "/" + "7.txt"
    fileName_9_a = "openQCM" + "/" + "sweep_data" + "/" + "9.txt"

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

    
    # BASELINE CORRECTION ROUTINE 
    # -------------------------------------------------------------------------
    
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
    amp_1_a_baseline = 0
    amp_3_a_baseline = 0
    amp_5_a_baseline = 0
    amp_7_a_baseline = 0
    amp_9_a_baseline = 0
    
    amp_1_a_baseline = amp_1_a - polyfitted_list[0]
    amp_3_a_baseline = amp_3_a - polyfitted_list[1]
    amp_5_a_baseline = amp_5_a - polyfitted_list[2]
    amp_7_a_baseline = amp_7_a - polyfitted_list[3]
    amp_9_a_baseline = amp_9_a - polyfitted_list[4]
    
# =============================================================================
#     plt.plot(frq_1_a, amp_1_a_baseline)
#     plt.show()
#     plt.plot(frq_3_a, amp_3_a_baseline)
#     plt.show()
#     plt.plot(frq_5_a, amp_5_a_baseline)
#     plt.show()
#     plt.plot(frq_7_a, amp_7_a_baseline)
#     plt.show()
#     plt.plot(frq_9_a, amp_9_a_baseline)
#     plt.show()
# =============================================================================
    
    
    # SAVITZKY - GOLAY FILTER 
    # -------------------------------------------------------------------------
    amp_1_a_filter = 0
    amp_3_a_filter = 0
    amp_5_a_filter = 0
    amp_7_a_filter = 0
    amp_9_a_filter = 0
    
     
    # SG window size array depending on ovettone 
    sg_window_size = [Constants.SG_window_size5_fundamental, 
                      Constants.SG_window_size5_3th_overtone, 
                      Constants.SG_window_size5_5th_overtone, 
                      Constants.SG_window_size5_7th_overtone, 
                      Constants.SG_window_size5_9th_overtone]
    
    # SG order 
    sg_order = [Constants.SG_order, Constants.SG_order, Constants.SG_order, Constants.SG_order, Constants.SG_order]
    
    # prototype: 
    # savitzky_golay(y, window_size, order, deriv=0, rate=1):  
    # usage: 
    # filtered_mag = self.savitzky_golay(mag_beseline_corrected, window_size = SG_window_size, order = Constants.SG_order)
    
    amp_1_a_filter = savitzky_golay(amp_1_a_baseline, window_size = sg_window_size[0], order = Constants.SG_order)
    amp_3_a_filter = savitzky_golay(amp_3_a_baseline, window_size = sg_window_size[1], order = Constants.SG_order)
    amp_5_a_filter = savitzky_golay(amp_5_a_baseline, window_size = sg_window_size[2], order = Constants.SG_order)
    amp_7_a_filter = savitzky_golay(amp_7_a_baseline, window_size = sg_window_size[3], order = Constants.SG_order)
    amp_9_a_filter = savitzky_golay(amp_9_a_baseline, window_size = sg_window_size[4], order = Constants.SG_order)
    
# =============================================================================
#     plt.plot(frq_1_a, amp_1_a_baseline)
#     plt.plot(frq_1_a, amp_1_a_filter)
#     plt.show()
#     
#     plt.plot(frq_3_a, amp_3_a_baseline)
#     plt.plot(frq_3_a, amp_3_a_filter)
#     plt.show()
#     
#     plt.plot(frq_5_a, amp_5_a_baseline)
#     plt.plot(frq_5_a, amp_5_a_filter)
#     plt.show()
#     
#     plt.plot(frq_7_a, amp_7_a_baseline)
#     plt.plot(frq_7_a, amp_7_a_filter)
#     plt.show()
#     
#     plt.plot(frq_9_a, amp_9_a_baseline)
#     plt.plot(frq_9_a, amp_9_a_filter)
#     plt.show()
# =============================================================================

    # SPLINE ROUTINE 
    # -------------------------------------------------------------------------
    # init spline variable 
    amp_1_a_sp = 0
    amp_3_a_sp = 0
    amp_5_a_sp = 0
    amp_7_a_sp = 0
    amp_9_a_sp = 0
    
    spline_factor = [Constants.Spline_factor5_fundamental,
                     Constants.Spline_factor5_3th_overtone, 
                     Constants.Spline_factor5_5th_overtone, 
                     Constants.Spline_factor5_7th_overtone, 
                     Constants.Spline_factor5_9th_overtone]
   

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

    frq_a_sp = [xx_1_a, xx_3_a, xx_5_a, xx_7_a, xx_9_a]
    amp_a_sp = [amp_1_a_sp, amp_3_a_sp, amp_5_a_sp, amp_7_a_sp, amp_9_a_sp]


    # FIND MAXIMUM AND MINIMA for EACH OVERTONES 
    # -----------------------------------------------------------------------------

    # find max and min initial frequency value
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


    # find max and min initial and final amplitude spline fitting 
    amp_a_sp_min = [0,0,0,0,0]
    amp_a_sp_max = [0,0,0,0,0]

    for i in range (len(amp_a_sp_min)): 
        amp_a_sp_min[i] = amp_a_sp[i][np.argmin(amp_a_sp[i], axis = 0)]

    for i in range(len(amp_a_sp_max)):
        amp_a_sp_max[i] = amp_a_sp[i][np.argmax(amp_a_sp[i], axis = 0)]
        
    num = [1, 3, 5, 7, 9]
    
    
    # GET the left point for dissipation 
    # prototype 
    # index_left = get_left_index(signal, amplitude_max, index_max)
    index_left_array_1 = 0
    index_left_array_3 = 0
    index_left_array_5 = 0
    index_left_array_7 = 0
    index_left_array_9 = 0
    
    index_left_array = [index_left_array_1, index_left_array_3, index_left_array_5, index_left_array_7, index_left_array_7]
    
    for i in range(len(num)):
        index_left_array[i] = get_left_index( amp_a_sp[i], amp_a_sp_max[i], np.argmax(amp_a_sp[i], axis = 0) )
        
    print (index_left_array)


    amp_a_sp_left = [0,0,0,0,0]
    
    for i in range(len(num)):
        amp_a_sp_left[i] = amp_a_sp[i][index_left_array[i]]
        
# =============================================================================
#     print (amp_a_sp_left)
# =============================================================================
        
    # get frequency left 
    frq_1_a_left = xx_1_a[index_left_array[0]]
    frq_3_a_left = xx_3_a[index_left_array[1]]
    frq_5_a_left = xx_5_a[index_left_array[2]]
    frq_7_a_left = xx_7_a[index_left_array[3]]
    frq_9_a_left = xx_9_a[index_left_array[4]]
    
    frq_a_left = [frq_1_a_left, frq_3_a_left, frq_5_a_left, frq_7_a_left, frq_9_a_left ]
    
    # GET the right point for dissipation 
    # prototype 
    # index_right = get_right_index(signal, amplitude_max, index_max)
    index_right_array_1 = 0
    index_right_array_3 = 0
    index_right_array_5 = 0
    index_right_array_7 = 0
    index_right_array_9 = 0
    
    index_right_array = [index_right_array_1, index_right_array_3, index_right_array_5, index_right_array_7, index_right_array_7]
    
    for i in range(len(num)):
        index_right_array[i] = get_right_index( amp_a_sp[i], amp_a_sp_max[i], np.argmax(amp_a_sp[i], axis = 0) )
        
    print (index_right_array)


    amp_a_sp_right = [0,0,0,0,0]
    
    for i in range(len(num)):
        amp_a_sp_right[i] = amp_a_sp[i][index_right_array[i]]
        
# =============================================================================
#     print (amp_a_sp_right)
# =============================================================================
        
    # get frequency right 
    frq_1_a_right = xx_1_a[index_right_array[0]]
    frq_3_a_right = xx_3_a[index_right_array[1]]
    frq_5_a_right = xx_5_a[index_right_array[2]]
    frq_7_a_right = xx_7_a[index_right_array[3]]
    frq_9_a_right = xx_9_a[index_right_array[4]]
    
    frq_a_right = [frq_1_a_right, frq_3_a_right, frq_5_a_right, frq_7_a_right, frq_9_a_right ]
    
# =============================================================================
#     print (frq_a_left)
# =============================================================================

    # USING SUBPLOT MATPLOT LIB 
    fig, axs = plt.subplots(3, 2)
    fig.tight_layout()
    
    axs[0,0].plot(frq_1_a, amp_1_a_baseline, marker = 'o', markersize = 2, color = Constants.plot_color_multi[0],  linewidth = 0)
    axs[0,0].plot(xx_1_a, amp_1_a_sp, 'k',  linewidth = 2)
# =============================================================================
#     axs[0,0].plot(frq_1_a_min, amp_a_sp_min[0], 'xr', markersize = 20)
# =============================================================================
    axs[0,0].plot(frq_1_a_max, amp_a_sp_max[0], 'xr', markersize = 20)
    axs[0,0].plot(frq_1_a_left, amp_a_sp_left[0], 'xr', markersize = 20)
    axs[0,0].plot(frq_1_a_right, amp_a_sp_right[0], 'xr', markersize = 20)
    print (frq_1_a_left, amp_a_sp_left[0])
    axs[0,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,0].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "Fundamental" )

   
    axs[0,1].plot(frq_3_a, amp_3_a_baseline, marker = 'o', markersize = 2, color = Constants.plot_color_multi[1], linewidth = 0)
    axs[0,1].plot(xx_3_a, amp_3_a_sp, 'k',  linewidth = 2)
# =============================================================================
#     axs[0,1].plot(frq_3_a_min, amp_a_sp_min[1], 'xr', markersize = 20)
# =============================================================================
    axs[0,1].plot(frq_3_a_max, amp_a_sp_max[1], 'xr', markersize = 20)
    axs[0,1].plot(frq_3_a_left, amp_a_sp_left[1], 'xr', markersize = 20)
    axs[0,1].plot(frq_3_a_right, amp_a_sp_right[1], 'xr', markersize = 20)
    print (frq_3_a_left, amp_a_sp_left[1])
    axs[0,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,1].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "3-rd Overtone" )

    
    axs[1,0].plot(frq_5_a, amp_5_a_baseline, marker = 'o', markersize = 2, color = Constants.plot_color_multi[2], linewidth = 0)
    axs[1,0].plot(xx_5_a, amp_5_a_sp, 'k',  linewidth = 2)
# =============================================================================
#     axs[1,0].plot(frq_5_a_min, amp_a_sp_min[2], 'xr', markersize = 20)
# =============================================================================
    axs[1,0].plot(frq_5_a_max, amp_a_sp_max[2], 'xr', markersize = 20)
    axs[1,0].plot(frq_5_a_left, amp_a_sp_left[2], 'xr', markersize = 20)
    axs[1,0].plot(frq_5_a_right, amp_a_sp_right[2], 'xr', markersize = 20)
    print (frq_5_a_left, amp_a_sp_left[2])
    axs[1,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,0].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "5-th Overtone" )

   
    axs[1,1].plot(frq_7_a, amp_7_a_baseline, marker = 'o', markersize = 2, color = Constants.plot_color_multi[3], linewidth = 0)
    axs[1,1].plot(xx_7_a, amp_7_a_sp, 'k',  linewidth = 2)
# =============================================================================
#     axs[1,1].plot(frq_7_a_min, amp_a_sp_min[3], 'xr', markersize = 20)
# =============================================================================
    axs[1,1].plot(frq_7_a_max, amp_a_sp_max[3], 'xr', markersize = 20)
    axs[1,1].plot(frq_7_a_left, amp_a_sp_left[3], 'xr', markersize = 20)
    axs[1,1].plot(frq_7_a_right, amp_a_sp_right[3], 'xr', markersize = 20)
    print (frq_7_a_left, amp_a_sp_left[3])
    axs[1,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,1].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "7-th Overtone" )

    
    axs[2,0].plot(frq_9_a, amp_9_a_baseline, marker = 'o', markersize = 2, color = Constants.plot_color_multi[4], linewidth = 0)
    axs[2,0].plot(xx_9_a, amp_9_a_sp, 'k',  linewidth = 2)
# =============================================================================
#     axs[2,0].plot(frq_9_a_min, amp_a_sp_min[4], 'xr', markersize = 20)
# =============================================================================
    axs[2,0].plot(frq_9_a_max, amp_a_sp_max[4], 'xr', markersize = 20)
    
    axs[2,0].plot(frq_9_a_left, amp_a_sp_left[4], 'xr', markersize = 20)
    axs[2,0].plot(frq_9_a_right, amp_a_sp_right[4], 'xr', markersize = 20)
    print (frq_9_a_left, amp_a_sp_left[4])
    axs[2,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )

    axs[2,0].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "9-th Overtone" )

    # turn off the axis of a last subplot in the grid 
    axs[-1, -1].axis('off')
    plt.tight_layout()
    plt.show()
