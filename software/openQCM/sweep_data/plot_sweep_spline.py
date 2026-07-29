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

# =============================================================================
# import matplotlib.pyplot as plt
# =============================================================================

# VER 0.1.6 use the correct Matplotlib backend for PyQt solved a visual bug of the main GUI 
# Use the correct backend: Make sure you're using the right Matplotlib backend for PyQt. 
# do this before importing any other Matplotlib module
import matplotlib
matplotlib.use('Qt5Agg') 
from matplotlib import pyplot as plt

import tkinter as Tk
import math
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import InterpolatedUnivariateSpline

from openQCM.core.constants import Constants
from openQCM.core import resonance

# SAVITZKY - GOLAY FILTER, and the band walk below it: both come from
# core/resonance.py, so this viewer draws what the instrument measured.
savitzky_golay = resonance.savitzky_golay


def foo():
    print("HELLO WORLD")


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
    (polyfitted_all, coeffs_all) = baseline_correction(freq_all, mag_all, Constants.BASELINE_POLY_ORDER)
    mag_beseline_corrected_all= mag_all-polyfitted_all

    return coeffs_all



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
    
# =============================================================================
#     # TEST 
#     foo()
# =============================================================================
    

    # get raw data sweep files
    fileName_1_a = "openQCM" + "/" + "sweep_data" + "/" + "1.txt"
    fileName_3_a = "openQCM" + "/" + "sweep_data" + "/" + "3.txt"
    fileName_5_a = "openQCM" + "/" + "sweep_data" + "/" + "5.txt"
    fileName_7_a = "openQCM" + "/" + "sweep_data" + "/" + "7.txt"
    fileName_9_a = "openQCM" + "/" + "sweep_data" + "/" + "9.txt"
    
    # 

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
    
    
    # GET the two points that delimit the dissipation band, from the same
    # function the instrument measures with: core/resonance.py.
    xx_a = [xx_1_a, xx_3_a, xx_5_a, xx_7_a, xx_9_a]

    frq_a_left = [0, 0, 0, 0, 0]
    frq_a_right = [0, 0, 0, 0, 0]
    amp_a_sp_left = [0, 0, 0, 0, 0]
    amp_a_sp_right = [0, 0, 0, 0, 0]

    for i in range(len(num)):
        band = resonance.find_peak_and_band(xx_a[i], amp_a_sp[i],
                                            Constants.THRESHOLD_DB)
        frq_a_left[i] = band.leading_frequency
        frq_a_right[i] = band.trailing_frequency
        # by definition both edges sit exactly on the threshold, so there is no
        # sample to look up: they fall between two of them
        amp_a_sp_left[i] = band.peak_value - Constants.THRESHOLD_DB
        amp_a_sp_right[i] = amp_a_sp_left[i]

    (frq_1_a_left, frq_3_a_left, frq_5_a_left,
     frq_7_a_left, frq_9_a_left) = frq_a_left
    (frq_1_a_right, frq_3_a_right, frq_5_a_right,
     frq_7_a_right, frq_9_a_right) = frq_a_right

# =============================================================================
#     print (frq_a_left)
# =============================================================================
    
    #### PLOT MULTI
    # USING SUBPLOT MATPLOT LIB 
    # VER 0.1.6 modify the plot properties and restyle
    #  
    
    # Use the dark background style
    # plt.style.use('dark_background')
    
    plot_color_multi_norm = []
    const = 255
    for color in Constants.plot_color_multi:
        normalized_color = tuple(x/const for x in color)
        plot_color_multi_norm.append(normalized_color)
     
    fig, axs = plt.subplots(3, 2)
    fig.tight_layout()
    # set tite 
    # fig.suptitle('Sweep Data Raw and Processed in Multiscan Mode', color='white', fontsize=12)
    # Cambia il titolo della figura
    fig.canvas.manager.set_window_title('Raw Data View Multiscan Mode')
    
    # Set the figure background color
    fig.patch.set_facecolor((25/255, 25/255, 25/255))

    # Set the axes background color and labels/title color
    for ax in axs.flat:
        ax.set_facecolor((25/255, 25/255, 25/255))
        # Set the spine color to white
        for spine in ax.spines.values():
            spine.set_edgecolor('white')
        # set tick labels to white
        ax.tick_params(axis='both', colors='white') 
        # set x axis label color to white
        ax.xaxis.label.set_color('white')  
        # set y axis label color to white
        ax.yaxis.label.set_color('white') 
        # set title color to white
        ax.title.set_color('white')  

    axs[0,0].plot(frq_1_a, amp_1_a_baseline, marker = 'o', markersize = 2, color = plot_color_multi_norm[0],  linewidth = 0)
    axs[0,0].plot(xx_1_a, amp_1_a_sp, 'r',  linewidth = 1)
# =============================================================================
#     axs[0,0].plot(frq_1_a_min, amp_a_sp_min[0], 'xr', markersize = 20)
# =============================================================================
    axs[0,0].plot(frq_1_a_max, amp_a_sp_max[0], 'xr', markersize = 20)
    axs[0,0].plot(frq_1_a_left, amp_a_sp_left[0], 'xr', markersize = 20)
    axs[0,0].plot(frq_1_a_right, amp_a_sp_right[0], 'xr', markersize = 20)
    # print (frq_1_a_left, amp_a_sp_left[0])
    axs[0,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,0].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "Fundamental" )

   
    axs[0,1].plot(frq_3_a, amp_3_a_baseline, marker = 'o', markersize = 2, color = plot_color_multi_norm[1], linewidth = 0)
    axs[0,1].plot(xx_3_a, amp_3_a_sp, 'r',  linewidth = 1)
# =============================================================================
#     axs[0,1].plot(frq_3_a_min, amp_a_sp_min[1], 'xr', markersize = 20)
# =============================================================================
    axs[0,1].plot(frq_3_a_max, amp_a_sp_max[1], 'xr', markersize = 20)
    axs[0,1].plot(frq_3_a_left, amp_a_sp_left[1], 'xr', markersize = 20)
    axs[0,1].plot(frq_3_a_right, amp_a_sp_right[1], 'xr', markersize = 20)
    # print (frq_3_a_left, amp_a_sp_left[1])
    axs[0,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[0,1].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "3-rd Overtone" )

    
    axs[1,0].plot(frq_5_a, amp_5_a_baseline, marker = 'o', markersize = 2, color = plot_color_multi_norm[2], linewidth = 0)
    axs[1,0].plot(xx_5_a, amp_5_a_sp, 'r',  linewidth = 1)
# =============================================================================
#     axs[1,0].plot(frq_5_a_min, amp_a_sp_min[2], 'xr', markersize = 20)
# =============================================================================
    axs[1,0].plot(frq_5_a_max, amp_a_sp_max[2], 'xr', markersize = 20)
    axs[1,0].plot(frq_5_a_left, amp_a_sp_left[2], 'xr', markersize = 20)
    axs[1,0].plot(frq_5_a_right, amp_a_sp_right[2], 'xr', markersize = 20)
    # print (frq_5_a_left, amp_a_sp_left[2])
    axs[1,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,0].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "5-th Overtone" )

   
    axs[1,1].plot(frq_7_a, amp_7_a_baseline, marker = 'o', markersize = 2, color = plot_color_multi_norm[3], linewidth = 0)
    axs[1,1].plot(xx_7_a, amp_7_a_sp, 'r',  linewidth = 1)
# =============================================================================
#     axs[1,1].plot(frq_7_a_min, amp_a_sp_min[3], 'xr', markersize = 20)
# =============================================================================
    axs[1,1].plot(frq_7_a_max, amp_a_sp_max[3], 'xr', markersize = 20)
    axs[1,1].plot(frq_7_a_left, amp_a_sp_left[3], 'xr', markersize = 20)
    axs[1,1].plot(frq_7_a_right, amp_a_sp_right[3], 'xr', markersize = 20)
    # print (frq_7_a_left, amp_a_sp_left[3])
    axs[1,1].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )
    axs[1,1].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "7-th Overtone" )

    
    axs[2,0].plot(frq_9_a, amp_9_a_baseline, marker = 'o', markersize = 2, color = plot_color_multi_norm[4], linewidth = 0)
    axs[2,0].plot(xx_9_a, amp_9_a_sp, 'r',  linewidth = 1)
# =============================================================================
#     axs[2,0].plot(frq_9_a_min, amp_a_sp_min[4], 'xr', markersize = 20)
# =============================================================================
    axs[2,0].plot(frq_9_a_max, amp_a_sp_max[4], 'xr', markersize = 20)
    
    axs[2,0].plot(frq_9_a_left, amp_a_sp_left[4], 'xr', markersize = 20)
    axs[2,0].plot(frq_9_a_right, amp_a_sp_right[4], 'xr', markersize = 20)
    # print (frq_9_a_left, amp_a_sp_left[4])
    axs[2,0].ticklabel_format(axis="x" ,useOffset=False, style='scientific', useMathText = True )

    axs[2,0].set( ylabel = "Amplitude (dB)", xlabel = "Frequency (Hz)", title = "9-th Overtone" )

    # turn off the axis of a last subplot in the grid 
    axs[-1, -1].axis('off')
    
    
    # VER 0.1.6 just a DUMMY trick to turn off the plot depending on the number fo peaks detected
    # TODO get the number of overtones here 
    # get peak 
    data  = loadtxt(Constants.cvs_peakfrequencies_path)
    # debug get the number of peaks 
    num_peaks = len(data)
    
# =============================================================================
#     print ("DEBUG len of peaks = ", num_peaks)
# =============================================================================
    # turn off the axis 
    # Turn off unused axes
    for idx in range(len(data), 6):
        i, j = divmod(idx, 2)
        axs[i, j].set_visible(False)
    
    plt.tight_layout()
    # plt.style.use('dark_background')
    plt.show()

# VER 0.1.6 plot raw data view in single mode  
# nn is the overtone number    
def script_single(nn): 
# =============================================================================
#     print ("TODO plot raw data view in single mode")
#     print ("the overtone number is = ", nn)
# =============================================================================
    
    # get raw data sweep files
    fileName_n_a = "openQCM" + "/" + "sweep_data" + "/" + str( 2*nn + 1 ) + ".txt"
# =============================================================================
#     print ("the filename is : ", fileName_n_a)
# =============================================================================
    
    # get all raw data from files
    dataAll_n_a = loadtxt(fileName_n_a)
    
    # get frequency amplitude and phase data for each overtone
    frq_n_a = dataAll_n_a[:, 0]
    amp_n_a = dataAll_n_a[:, 1]
    phs_n_a = dataAll_n_a[:, 2]
    
    # BASELINE CORRECTION ROUTINE 
    # -------------------------------------------------------------------------
    
    # get the coefficient of the calibration polinomial 
    coeffs_all = baseline_coeffs()
    
    polyfitted_list = np.polyval(coeffs_all, frq_n_a) 
    
    # init amplitude baseline corrected 
    amp_1_n_baseline = 0
    
    amp_n_a_baseline = amp_n_a - polyfitted_list
    
    # SAVITZKY - GOLAY FILTER 
    # -------------------------------------------------------------------------
    
    amp_n_a_filter = 0
    
    # SG window size array depending on overtone 
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
    
    amp_n_a_filter = savitzky_golay(amp_n_a_baseline, window_size = sg_window_size[nn], order = Constants.SG_order)
    
    # SPLINE ROUTINE 
    # -------------------------------------------------------------------------
    # init spline variable 
    amp_n_a_sp = 0
    
    spline_factor = [Constants.Spline_factor5_fundamental,
                     Constants.Spline_factor5_3th_overtone, 
                     Constants.Spline_factor5_5th_overtone, 
                     Constants.Spline_factor5_7th_overtone, 
                     Constants.Spline_factor5_9th_overtone]
    
    # SPLINE FITTING 
    s_n_a = UnivariateSpline(frq_n_a, amp_n_a_filter, s = spline_factor[nn])
    xx_n_a = np.arange(frq_n_a[0],frq_n_a[-1], 1)
    amp_n_a_sp = s_n_a(xx_n_a)
    
    # FIND MAXIMUM AND MINIMA for EACH OVERTONES 
    # -------------------------------------------------------------------------
    # find max and min initial frequency value
    frq_n_a_min = xx_n_a[np.argmin(amp_n_a_sp, axis = 0)]
    frq_n_a_max = xx_n_a[np.argmax(amp_n_a_sp, axis = 0)]
    
    # find max and min initial and final amplitude spline fitting 
    amp_n_sp_min = 0
    amp_n_sp_max = 0
    
    amp_n_sp_min = amp_n_a_sp[np.argmin(amp_n_a_sp, axis = 0)]
    amp_n_sp_max = amp_n_a_sp[np.argmax(amp_n_a_sp, axis = 0)]
    
# =============================================================================
#     print (amp_n_sp_min, amp_n_sp_max)
# =============================================================================
    
    # GET the two points that delimit the dissipation band, from the same
    # function the instrument measures with: core/resonance.py.
    band_n = resonance.find_peak_and_band(xx_n_a, amp_n_a_sp,
                                          Constants.THRESHOLD_DB)
    frq_n_a_left = band_n.leading_frequency
    frq_n_a_right = band_n.trailing_frequency
    # both edges sit exactly on the threshold, between two samples
    amp_a_sp_left_n = band_n.peak_value - Constants.THRESHOLD_DB
    amp_a_sp_right_n = amp_a_sp_left_n

    ####PLOT  SINGLE
    plot_color_multi_norm = []
    const = 255
    for color in Constants.plot_color_multi:
        normalized_color = tuple(x/const for x in color)
        plot_color_multi_norm.append(normalized_color)
    
    # Create a single plot
    fig, ax = plt.subplots()
    # Set the figure background color
    fig.patch.set_facecolor((25/255, 25/255, 25/255))
    
    # Adding the title here
    # ax.set_title('Sweep Data: Raw & Processed in Single Mode', color='white', fontsize=12)    
    fig.canvas.manager.set_window_title('Raw Data in Single Mode')

    # Plotting data on the single axis (ax)
    ax.plot(frq_n_a, amp_n_a_baseline, marker='o', markersize=2, color=plot_color_multi_norm[0], linewidth=0)
    ax.plot(xx_n_a, amp_n_a_sp, 'r', linewidth=1)
    # Commented out as in your original code:
    # ax.plot(frq_n_a_min, amp_a_sp_min[0], 'xr', markersize=20)
    ax.plot(frq_n_a_max, amp_n_sp_max, 'xr', markersize=20)
    ax.plot(frq_n_a_left, amp_a_sp_left_n, 'xr', markersize=20)
    ax.plot(frq_n_a_right, amp_a_sp_right_n, 'xr', markersize=20)
    
    # Set the axes background color and labels/title color for dark theme
    ax.set_facecolor((25/255, 25/255, 25/255))
    for spine in ax.spines.values():
        spine.set_edgecolor('white')
    ax.tick_params(axis='both', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    
    # Formatting the axis
    ax.ticklabel_format(axis="x", useOffset=False, style='scientific', useMathText=True)
    ax.set(ylabel="Amplitude (dB)", xlabel="Frequency (Hz)", title="")
    
    plt.tight_layout()
    # plt.style.use('dark_background')  # Uncomment if you want a dark background
    plt.show()
