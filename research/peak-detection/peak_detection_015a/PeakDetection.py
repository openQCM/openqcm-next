# =============================================================================
#
# PEAK DETECTION ALGORITHM  
#
# Peak detection algorithm for openQCM Next python version 0.1.5a 
# 
# Test the script 
# 
# =============================================================================

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal


#### GLOBAL 

# calibration filename 
# Calibration_3MHz
filename = 'Calibration_3MHz.txt' # Calibration_5MHz_air.txt'

# Global definition and params of the algorithm 
# define the sweep minimum frequency  1 MHz for fundamental frequency detection  
freq_sweep_min = 1000000
# define the sweep maximum frequency 12 MHz for fundamental frequency detection  
freq_sweep_max = 12000000

# 6000 points corresponds to 6000 points x 500 Hz = 3 MHz
# points specifies how many points on each side of a point to use for 
# the comparison to consider the point as a relative extrema
points = 6000  

# define the half interval around the overtone  
freq_range_half = 250000

# 200 points corresponds to 200 points x 500 Hz = 10 KHz
# points_overtone specifies how many points on each side of a point to use for 
# the comparison to consider the point as a relative extrema
points_overtone = 200  

# Baseline estimation with Least Squares Polynomial Fit (LSP) 
def baseline_estimation( x, y, poly_order):
    # Least Squares Polynomial Fit (LSP)
    coeffs = np.polyfit(x,y,poly_order) 
    # Evaluate a polynomial at specific values
    poly_fitted = np.polyval(coeffs,x)  
    return poly_fitted, coeffs       
  
    
# Baseline correction for signal (amplidute or phase) 
def baseline_correction(freq, signal) :
    
    # input signal Amplitude
    (poly_fitted, coeffs) = baseline_estimation(freq, signal, 8)
    signal_corr = signal - poly_fitted
    
    # return the corrected signal     
    return signal_corr

# VER 0.1.5a Peak Detection QCM fundamental 
def peak_detection_qcm_fundamental (freq, mag, phase): 
    
    # peak detection of fundamental resonance frequency of QCM 
    # --------------------------------------------------------
    
    # init the numpy array frequency 
    freq_arr = np.array(freq)
    # init the numpy array magnitude 
    mag_arr = np.array(mag)
    # init the numpy array phase 
    phase_arr = np.array(phase)
    
    # define as global 
# =============================================================================
#     # define the sweep minimum frequency  1 MHz 
#     freq_sweep_min = 1000000
#     # define the sweep maximum frequency 12 MHz 
#     freq_sweep_max = 12000000
# =============================================================================
    
    # get min frequency index 
    idx_min = np.where(freq_arr == freq_sweep_min)[0][0]
    # get max frequency index
    idx_max = np.where(freq_arr == freq_sweep_max)[0][0]
            
    # array subset for detecting QCM fundamental 
    freq_arr_sub = freq_arr[idx_min : idx_max : 1]
    mag_arr_sub = mag_arr[idx_min : idx_max : 1]
    phase_arr_sub = phase_arr[idx_min : idx_max : 1]
    
    # Calculate the relative extrema of data using scipy.signal.argrelextrema
    # scipy.signal.argrelextrema(data, comparator, axis=0, order=1, mode='clip')
    # Returns: indices of the maxima in arrays of integers
    
    # define global 
# =============================================================================
#     # 6000 points corresponds to 6000 points x 500 Hz = 3 MHz
#     points = 6000  
# =============================================================================

    # find incedes of local maximum points
    idx_mag_max_arr = scipy.signal.argrelextrema( data = mag_arr_sub, comparator = np.greater, order = points)
    idx_phase_max_arr = scipy.signal.argrelextrema( data = phase_arr_sub, comparator = np.greater, order = points)
    
    # get the index of maximum amplitude
    idx_mag_max = np.argmax(mag_arr_sub[idx_mag_max_arr])
    # get the index of maximum phase
    idx_phase_max = np.argmax(phase_arr_sub[idx_phase_max_arr])
    
    # frequency of maximum amplitude  
    f_mag_max = freq_arr_sub[idx_mag_max_arr][idx_mag_max]
    # frequency of maximum phase 
    f_phase_max = freq_arr_sub[idx_phase_max_arr][idx_phase_max]
           
    print ("Peak QCM frequency fundamental (magnitude) = ", f_mag_max)
   
    # return the QCM fundamental frequency 
    return f_mag_max
    
# VER 0.1.5a Peak Detection QCM overtones 
def peak_detection_qcm_overtones (freq, mag, phase, freq_fundamental): 
 
    # the n odd overtones array 
    overtones_n = [3, 5, 7, 9]
    # as numpy array 
    np.asarray(overtones_n)
    # the overtones frequency array 
    overtones_f = np.array(overtones_n) * freq_fundamental
    
    # delete the overtones exceeding the maximum frequency limit 
    # TODO define the maximum frequency limit and modify to 5.1e6
    # SOLVED the maximum limit frequency should be the last value in the frequency array 
    # i will put now manually 
    maximum_freq_limit = 51000000
    overtones_f = np.delete(overtones_f, np.argwhere(overtones_f > maximum_freq_limit))
    
    # define as global
# =============================================================================
#    
#     # init the half frequency range for peak detection around the overtones 
#     freq_range_half = 250000  # 500000 
# =============================================================================
    
    # init the numpy array frequency 
    freq_arr = np.array(freq)
    # init the numpy array magnitude 
    mag_arr = np.array(mag)
    # init the numpy array phase 
    phase_arr = np.array(phase)
    
    # init the frequency overtones numpy array
    frequency_overtones = np.zeros(len(overtones_f))
    
    # cycle on overtones to get the frequency  
    for i in range (len(overtones_f)):

        # get min frequency index 
        idx_min = np.abs(freq_arr - (overtones_f[i] - freq_range_half)).argmin()
        # get max frequency index
        idx_max = np.abs(freq_arr - (overtones_f[i] + freq_range_half)).argmin()
        
        # array subset 
        freq_arr_sub = freq_arr [ idx_min: idx_max : 1]
        mag_arr_sub = mag_arr  [ idx_min: idx_max : 1]
        # phase_arr_sub[i] = phase_arr[idx_min : idx_max : 1]
        
        # OPTION 1 
        # -----------------------------------------------------------------
# =============================================================================
#             # get the index of maximum amplitude
#             idx_mag_max = np.argmax(mag_arr_sub) 
#             # get the frequency of maximum aplitude 
#             frequency_overtones[i] = freq_arr_sub[idx_mag_max]
# =============================================================================
        
        # OPTION 2
        # -----------------------------------------------------------------
        
        # get indexes of magnitude maximum using scipy.signal.argrelextrema
        idx_mag_max_arr = scipy.signal.argrelextrema( data = mag_arr_sub, comparator = np.greater, order = points_overtone)
        
        # get the index of maximum amplitude
        idx_mag_max = np.argmax(mag_arr_sub[idx_mag_max_arr])
        
        # the arry of frequency of maximum amplitude 
        f_mag_max_arr = freq_arr_sub[idx_mag_max_arr]
        
        # frequency of maximum amplitude  
        f_mag_max = freq_arr_sub[idx_mag_max_arr][idx_mag_max]
       
        # DEBUG print index of extreme and frequency of maximum amplitude 
# =============================================================================
#         print ("DEBUG: ")
#         print ("index of extrema", idx_mag_max_arr)
#         print ("index of maximum amplitude", idx_mag_max)
#         print ("frequency array of extrema", f_mag_max_arr)
#         print ("frequency of maximum amplitude", f_mag_max)
# =============================================================================
            
        try:
            # get the frequency correspondig to the maximum amplitude 
            frequency_overtones[i] = f_mag_max
            
        except: 
            print ("unable to access the index of the tuple")
            pass
        
    # return the QCM overtones 
    return (frequency_overtones)


#### SCRIPT
# =============================================================================
# Reading the calibration file
data = np.loadtxt(filename)  # Adjust the delimiter if necessary

# Extract columns
frequency = data[:, 0]
gain = data[:, 1]
phase = data[:, 2]


# Plotting frequency vs gain raw data 
plt.plot(frequency, gain, 'r-')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Gain (dB)')
plt.title('Frequency - Gain Raw Data')
plt.tight_layout()
plt.show()


# =============================================================================
# # Plotting frequency vs phase raw data 
# plt.subplot(2, 1, 2)
# plt.plot(frequency, phase, 'b-')
# plt.xlabel('Frequency')
# plt.ylabel('Phase (degree)')
# plt.title('Frequency - Phase Raw Data')
# 
# plt.tight_layout()
# plt.show()
# =============================================================================

#### BASELINE CORR 
# Baseline esrtimation and correction using polynomial interpolation
gain_baseline_corr = baseline_correction(frequency, gain)
phase_baseline_corr = baseline_correction(frequency, phase)

plt.plot(frequency, gain, 'r-', label = "Gain signal raw")
plt.plot(frequency, gain_baseline_corr, 'k-', label = "Gain signal corrected")
plt.xlabel('Frequency (Hz)')
plt.ylabel('Gain (dB)')
plt.title('Frequency - Gain Baseline correction')

plt.tight_layout()
plt.legend()
plt.show()

# =============================================================================
# plt.plot(frequency, phase, 'b-')
# plt.plot(frequency, phase_baseline_corr, 'k-')
# plt.xlabel('Frequency')
# plt.ylabel('Phase (degree)')
# plt.title('Frequency - Phase Baseline correction')
# plt.tight_layout()
# plt.show()
# =============================================================================


#### PEAK DETECTION 
# Fundamental QCM frequncy 
fundamental_baseline_corr = peak_detection_qcm_fundamental(frequency, gain_baseline_corr, phase_baseline_corr)
# Overtones QCM frequencies 
overtones_baseline_corr = peak_detection_qcm_overtones(frequency, gain_baseline_corr, phase_baseline_corr, fundamental_baseline_corr)

# create the array of resonances
max_freq_mag =  np.zeros(len(overtones_baseline_corr) + 1) 
for i in range( len(overtones_baseline_corr) + 1) :
    if (i == 0):
        max_freq_mag[i] = fundamental_baseline_corr
    else:
        max_freq_mag[i] = overtones_baseline_corr[i - 1]
print ("QCM peak detection at frequencies = ", max_freq_mag)

#### PLOT PEAKS RAW DATA

plt.plot(frequency, gain_baseline_corr, 'k-', label = "Gain signal corrected")
plt.plot(frequency, gain, 'r-', label = "Gain signal raw")

# Highlight the peaks on the plot:
for i, peak in enumerate(max_freq_mag): 
    # Find the index of the nearest matching frequency
    idx = (np.abs(frequency - peak)).argmin()
    plt.scatter(frequency[idx], gain_baseline_corr[idx], color='red', s=50)  # Highlight the peak with a red dot (chilly peppers)
    if i == 0:
        plt.scatter(frequency[idx], gain_baseline_corr[idx], color='red', s=50, label='Peak Frequencies')  # Highlight the peak with a red dot (chilly peppers)
    else:
        plt.scatter(frequency[idx], gain_baseline_corr[idx], color='red', s=50)  # Highlight the peak with a red dot (chilly peppers)

plt.xlabel('Frequency')
plt.ylabel('Gain (dB)')
plt.title('Frequency - Gain Baseline correction')
plt.legend()
plt.tight_layout()
plt.show()


#### PLOT PEAKS

plt.plot(frequency, gain_baseline_corr, 'k-', label = "Gain signal corrected")

# Highlight the peaks on the plot:
for i, peak in enumerate(max_freq_mag): 
    # Find the index of the nearest matching frequency
    idx = (np.abs(frequency - peak)).argmin()
    if i == 0:
        plt.scatter(frequency[idx], gain_baseline_corr[idx], color='red', s=50, label='Peak Frequencies')  # Highlight the peak with a red dot (chilly peppers)
    else:
        plt.scatter(frequency[idx], gain_baseline_corr[idx], color='red', s=50)  # Highlight the peak with a red dot (chilly peppers)

plt.xlabel('Frequency (Hz)')
plt.ylabel('Gain (dB)')
plt.title('Frequency - Gain Baseline corrected')
plt.legend()
plt.tight_layout()
plt.show()
