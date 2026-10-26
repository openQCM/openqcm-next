import multiprocessing
import time
from openQCM.core.constants import Constants
from openQCM.common.fileStorage import FileStorage
from openQCM.common import sweepDump as SweepDump
# VER 0.1.6G-ADAPTIVE each peak confirmed on finer sweeps around it
from openQCM.core import peak_refine

import serial
from serial.tools import list_ports
import numpy as np
import scipy.signal

# VER 0.1.6


TAG = ""#"[Calibration]"


# Global definition and params of the peak detection algorithm 
# define the sweep minimum frequency  1 MHz for fundamental frequency detection  
freq_sweep_min = 1000000
# define the sweep maximum frequency 12 MHz for fundamental frequency detection  
freq_sweep_max = 12000000

# 6000 points corresponds to 6000 points x 500 Hz = 3 MHz
# points specifies how many points on each side of a point to use for 
# the comparison to consider the point as a relative extrema
points = 6000  

# define the half interval around the overtone 250 KHz 
freq_range_half = 250000

# 200 points corresponds to 200 points x 500 Hz = 100 KHz TODO intervallo troppo grande
# points_overtone specifies how many points on each side of a point to use for 
# the comparison to consider the point as a relative extrema

# VER 0.1.6 TODO trova il range di frequenza migliore per peak detection degli overtoni
points_overtone = 100 #200  

maximum_freq_limit = 51000000

###############################################################################
# Process for the serial package and the communication with the serial port
# Processes incoming data and calculates outgoing data by the algorithms
###############################################################################
class CalibrationProcess(multiprocessing.Process):
    
    
    ###########################################################################
    # BASELINE ESTIMATION
    # Estimates Baseline with Least Squares Polynomial Fit (LSP)
    ###########################################################################
    def baseline_estimation(self,x,y,poly_order):
        # Least Squares Polynomial Fit (LSP)
        coeffs = np.polyfit(x,y,poly_order) 
        # Evaluate a polynomial at specific values
        poly_fitted = np.polyval(coeffs,x) 
        return poly_fitted,coeffs       
      
        
    ###########################################################################
    # BASELINE CORRECTION
    # estimates signal-baseline for amplitude and phase
    ###########################################################################
    def baseline_correction(self,readFREQ,data_mag,data_ph):
        
        # input signal Amplitude
        (self._polyfitted_all,self._coeffs_all) = self.baseline_estimation(readFREQ,data_mag,Constants.BASELINE_POLY_ORDER)
        self._mag_beseline_corrected_all = data_mag-self._polyfitted_all
        
        # input signal Phase
        (self._polyfitted_all_phase,self._coeffs_all_phase) = self.baseline_estimation(readFREQ,data_ph,Constants.BASELINE_POLY_ORDER)
        self._phase_beseline_corrected_all = data_ph - self._polyfitted_all_phase 
        return self._mag_beseline_corrected_all, self._phase_beseline_corrected_all
    
    
    # VER 0.1.6 Peak Detection QCM fundamental 
    def peak_detection_qcm_fundamental (self, freq, mag, phase): 
        # peak detection of fundamental resonance frequency of QCM 
        
        # init the numpy array frequency 
        freq_arr = np.array(freq)
        # init the numpy array magnitude 
        mag_arr = np.array(mag)
        # init the numpy array phase 
        phase_arr = np.array(phase)
           
        # get min frequency index 
        idx_min = np.where(freq_arr == freq_sweep_min)[0][0]
        # get max frequency index
        idx_max = np.where(freq_arr == freq_sweep_max)[0][0]
                
        # array subset 
        freq_arr_sub = freq_arr[idx_min : idx_max : 1]
        mag_arr_sub = mag_arr[idx_min : idx_max : 1]
        phase_arr_sub = phase_arr[idx_min : idx_max : 1]
        
        # Calculate the relative extrema of data using scipy.signal.argrelextrema
        # scipy.signal.argrelextrema(data, comparator, axis=0, order=1, mode='clip')
        # Returns: indices of the maxima in arrays of integers
        
        # find the local maximum points
        idx_mag_max_arr = scipy.signal.argrelextrema( data = mag_arr_sub, comparator = np.greater, order = points)
        idx_phase_max_arr = scipy.signal.argrelextrema( data = phase_arr_sub, comparator = np.greater, order = points)
        
        # get the index of maximum amplitude
        idx_mag_max = np.argmax(mag_arr_sub[idx_mag_max_arr])
        # get the index of maximum phase
        idx_phase_max = np.argmax(phase_arr_sub[idx_phase_max_arr])
        
        # frequency of maximum amplitude  
        f_mag_max = freq_arr_sub[idx_mag_max_arr][idx_mag_max]
        # frequency of maximum phase: not used, but kept with the phase argmax above, which raises
        # on a sweep with no phase maximum and so stops Peak Detection, as it always has
        f_phase_max = freq_arr_sub[idx_phase_max_arr][idx_phase_max]
                       
        # return the QCM fundamental frequency 
        return f_mag_max
        
    # VER 0.1.6 Peak Detection QCM overtones 
    # VER 0.1.6 TODO prova a migliorare il peak detection degli overtoni, per verificare se quello che trovo è proprio una risonanza 
    def peak_detection_qcm_overtones (self, freq, mag, phase, freq_fundamental):
        
        # the n odd overtones array 
        overtones_n = [3, 5, 7, 9]
        # as numpy array 
        np.asarray(overtones_n)
        # the overtones frequency array 
        overtones_f = np.array(overtones_n) * freq_fundamental
        
        # delete the overtones exceeding the maximum frequency limit 
        overtones_f = np.delete(overtones_f, np.argwhere(overtones_f > maximum_freq_limit))
         
        # init the numpy array frequency 
        freq_arr = np.array(freq)
        # init the numpy array magnitude 
        mag_arr = np.array(mag)
        # init the numpy array phase 
        phase_arr = np.array(phase)
        
        # init the frequency overtones numpy array
        frequency_overtones = np.zeros(len(overtones_f))
        # Array to hold frequency differences
        freq_diff_arr = np.zeros(len(overtones_f))  
        # array to hold phase maximum values 
        phase_max_arr = np. zeros(len(overtones_f))
   
        # cycle on overtones to get the frequency  
        for i in range (len(overtones_f)):

 
            # get min and max frequency index
            idx_min = np.abs(freq_arr - (overtones_f[i] - freq_range_half)).argmin()
            idx_max = np.abs(freq_arr - (overtones_f[i] + freq_range_half)).argmin()
            

            # array subset 
            freq_arr_sub = freq_arr[ idx_min : idx_max : 1]
            mag_arr_sub = mag_arr[ idx_min : idx_max : 1]
            phase_arr_sub = phase_arr[ idx_min : idx_max : 1]
            
            
            # OPTION 1 
            # -----------------------------------------------------------------
            
            # OPTION 2
            # -----------------------------------------------------------------
            
            # find the local maximum points for magnitude and phase
            idx_mag_max_arr = scipy.signal.argrelextrema( data = mag_arr_sub, comparator = np.greater, order = points_overtone)
            idx_phase_max_arr = scipy.signal.argrelextrema(data=phase_arr_sub, comparator=np.greater, order=points_overtone)[0]
            
            # get the index of maximum amplitude and phase
            if len(idx_mag_max_arr) > 0:
                idx_mag_max = np.argmax(mag_arr_sub[idx_mag_max_arr])
                f_mag_max = freq_arr_sub[idx_mag_max_arr][idx_mag_max]
            else:
                f_mag_max = None
            
            if len(idx_phase_max_arr) > 0:
                idx_phase_max = np.argmax(phase_arr_sub[idx_phase_max_arr])
                f_phase_max = freq_arr_sub[idx_phase_max_arr][idx_phase_max]
                # index of maximum phase in global array idx_phase_max_arr
                idx_phase_max_global = idx_phase_max_arr[idx_phase_max]
                # store the value of phase maximim value for i-index
                phase_max_arr[i] = phase_arr_sub[idx_phase_max_global]

            else:
                f_phase_max = None
            
            # Store the frequency of maximum amplitude
            if f_mag_max is not None:
                frequency_overtones[i] = f_mag_max
           
            # Calculate and store the frequency difference if both maxima are found
            if f_mag_max is not None and f_phase_max is not None:
                freq_diff_arr[i] = np.abs(f_mag_max - f_phase_max)
            else:
                freq_diff_arr[i] = None  # or np.nan to indicate unavailable comparison
        
        # Frequency difference threshold
        diff_threshold = (Constants.calib_fStep * points_overtone)/4    
        
        # Define the phase threshold in degrees TODO make it global 
        phase_threshold = 10
        
        # Array to track indices of frequencies to discard
        indices_to_discard = []
        
        # Loop through frequency differences to check against the diff_threshold
        for i, diff in enumerate(freq_diff_arr):
            if diff is not None and diff > diff_threshold:
                print(f"Frequency difference at overtone {i} exceeds threshold ({diff_threshold}): {diff}. It will be discarded.")
                indices_to_discard.append(i)
                
        # Adding check for phase values that do not exceed the threshold
        for i, phase_max in enumerate(phase_max_arr):
            if phase_max <= phase_threshold:
                print(f"Phase maximum at overtone {i} does not exceed threshold ({phase_threshold} degrees): {phase_max}. It will be discarded.")
                if i not in indices_to_discard:  # Avoid duplicates
                    indices_to_discard.append(i)
            
        
        # VER 0.1.6G-ADAPTIVE every candidate, rejected here or not: the fine
        # sweeps around them decide (_refine_peaks). This sweep's 500 Hz step is
        # wider than a line in air, so its phase check rejected real overtones.
        self._overtone_candidates = (list(overtones_n[:len(overtones_f)]), frequency_overtones.copy())
        
        # discard the corresponding frequencies from your measurements:
        frequency_overtones_filtered = np.delete(frequency_overtones, indices_to_discard)
         
        # return the QCM overtones 
        # return (frequency_overtones)
        # return the QCM overtones filtered
        return (frequency_overtones_filtered)

    ###########################################################################
    # VER 0.1.6G-ADAPTIVE PEAKS CONFIRMED ON FINER SWEEPS (core/peak_refine.py)
    ###########################################################################
    def _refine_peaks(self, f0):
        """The fundamental f0 and every overtone candidate of the wide sweep,
        each swept again around it (+-25 kHz at 50 Hz, then +-5 kHz at 10 Hz):
        (fundamental, confirmed overtones). The fundamental is refined but never
        rejected here (it was found on the magnitude alone, as before); an
        overtone the fine sweep rejects is left out, as the wide sweep's check
        left it out. Each decision is printed with its numbers."""
        mag_coeffs, phase_coeffs = self._coeffs_all, self._coeffs_all_phase
        r = peak_refine.confirm(f0, self._sweep_section, mag_coeffs, phase_coeffs)
        print(TAG, peak_refine.describe("F1 (fundamental)", f0, r))
        if r.frequency is not None:
            f0 = r.frequency
        else:
            print(TAG, "Peak F1: the wide sweep's value is kept")
        confirmed = []
        harmonics, candidates = self._overtone_candidates
        for n, f in zip(harmonics, candidates):
            if not f > 0:
                print(TAG, "Peak F%d: no candidate on the wide sweep" % n)
                continue
            r = peak_refine.confirm(float(f), self._sweep_section, mag_coeffs, phase_coeffs)
            print(TAG, peak_refine.describe("F%d" % n, float(f), r))
            if r.frequency is not None:
                confirmed.append(r.frequency)
        return f0, np.array(confirmed)

    def _sweep_section(self, start, stop, step):
        """One plain sweep of whole hertz: (freq, mag dB, phase deg), converted as
        the wide sweep converts them. A Stop sends 'Q' and raises
        peak_refine.Cancelled; a timeout or a malformed reply raises RuntimeError."""
        start, stop, step = int(start), int(stop), int(step)
        points = (stop - start) // step + 1
        self._serial.write(("%d;%d;%d\n" % (start, stop, step)).encode())
        buffer = ''
        t0 = time.time()
        while True:
            if self._exit.is_set():
                self._serial.write(Constants.serial_stop_sweep)
                raise peak_refine.Cancelled()
            if time.time() - t0 > Constants.REFINE_TIMEOUT:
                self._serial.write(Constants.serial_stop_sweep)
                raise RuntimeError("refining sweep %d;%d;%d timed out" % (start, stop, step))
            waiting = self._serial.inWaiting()
            if waiting == 0:
                time.sleep(0.001)
                continue
            chunk = self._serial.read(waiting).decode()
            buffer += chunk
            # only the end-of-sweep line carries an 's'
            if 's' in chunk:
                break
        lines = [line for line in buffer.split('\n') if line.strip()][:-1]
        data = np.array([[float(x) for x in line.split(';')[:2]] for line in lines])
        if data.ndim != 2 or len(data) != points:
            raise RuntimeError("refining sweep: %d points, expected %d" % (len(data), points))
        adc_to_volt = 3.3 / 4096
        mag = (data[:, 0] * adc_to_volt / 2 - 0.9) / 0.03
        phase = (data[:, 1] * adc_to_volt / 1.5 - 0.9) / 0.01
        return start + np.arange(points) * float(step), mag, phase

     
    ###########################################################################
    # Initializing values for process
    ###########################################################################
    def __init__(self, parser_process):
        """
        :param parser_process: Reference to a ParserProcess instance.
        :type parser_process: ParserProcess.
        """
        multiprocessing.Process.__init__(self)
        self._exit = multiprocessing.Event()
        
        # Instantiate a ParserProcess class for each communication channels
        self._parser1 = parser_process
        self._parser2 = parser_process
        self._parser5 = parser_process
        self._parser6 = parser_process
        self._serial = serial.Serial()
        
    ###########################################################################
    # Opens a specified serial port
    ###########################################################################    
    def open(self, port, 
                   speed = Constants.serial_default_QCS, 
                   timeout = Constants.serial_timeout_ms, 
                   writeTimeout = Constants.serial_writetimeout_ms):
        """
        :param port: Serial port name :type port: str.
        :param speed: Baud rate, in bps, to connect to port :type speed: int.
        :param timeout: Sets current read timeout :type timeout: float (seconds).
        :param writetTimeout: Sets current write timeout :type writeTimeout: float (seconds).
        :return: True if the port is available :rtype: bool.
        """
        self._serial.port = port
        self._serial.baudrate = Constants.serial_default_speed #115200
        self._serial.stopbits = serial.STOPBITS_ONE
        self._serial.bytesize = serial.EIGHTBITS
        self._serial.timeout = timeout
        self._serial.writetimeout = writeTimeout
        self._QCStype = speed
        
        
        
        print(TAG, "Selected Quartz Crystal Sensor:",self._QCStype)
        return self._is_port_available(self._serial.port)
    
    ###########################################################################
    # Reads the serial port,processes and adds all the data to internal queues
    ###########################################################################
    def run(self):
        """
        The expected format is a buffer (sweep) and a new buffer as a new sweep. 
        The method parses data, converts each value to float and adds to a queue. 
        If incoming data can't be converted to float,the data will be discarded.
        """  
        # initializations
        self._polyfitted_all = None
        self._coeffs_all = None
        self._polyfitted_all_phase = None
        self._coeffs_all_phase = None
        self._mag_beseline_corrected_all = None
        self._phase_beseline_corrected_all = None
        self._flag = 0
        self._flag2 = 0
        
        # Checks if the serial port is currently connected
        if self._is_port_available(self._serial.port):
            
            # Sets start, stop, step and range frequencies 
            readFREQ  = Constants.calibration_readFREQ
            # Gets the state of the serial port
            if not self._serial.isOpen():
                # Opens the serial port
                self._serial.open()
                # VER 0.1.6 responsive cancellation (ported from openQCM Q-1 v3.0):
                # use a short read timeout so the sweep-read loop can poll
                # self._exit instead of blocking for serial_timeout_ms (4 s).
                self._serial.timeout = 0.1
                self._serial.flushInput()
                self._serial.flushOutput()
                # VER 0.1.6 drain any bytes left over from a previously
                # interrupted peak detection so a fresh run starts clean: a
                # mid-sweep Stop can leave the Teensy mid-transmission.
                drain_deadline = time.time() + 5.0
                while time.time() < drain_deadline:
                    stale = self._serial.read(self._serial.inWaiting())
                    if not stale:
                        time.sleep(0.1)
                        stale = self._serial.read(self._serial.inWaiting())
                        if not stale:
                            break
                self._serial.flushInput()
                self._serial.flushOutput()
                # Initializes the sweep counter
                k=0
                print(TAG,'Peak Detection Started')
                print(TAG,'The operation might take just a while to complete. Please wait.')
                
                #### SWEEPS LOOP
                #----------------------------------------------------------
                temp1=[]
                temp2=[]
                #----------------------------------------------------------
                while not self._exit.is_set():
                    # Boolean variable to process exceptions
                    self._flag = 0
                    self._flag2 = 0
                    fStep = Constants.calib_fStep #1000
                    
                    # Sets start, stop, step and range frequencies 
                    startFreq = Constants.calibration_frequency_start + k * Constants.calib_fRange   #5000000/10000000
                    stopFreq  = startFreq + Constants.calib_fRange #5000000
                    
                    samples   = Constants.calib_samples #5001/10001
                    # data reset for new sweep
                    data_mag = np.linspace(0,0,samples)   
                    data_ph  = np.linspace(0,0,samples)
                    
                    
                    try:
                        # amplitude/phase convert bit to dB/Deg parameters
                        vmax = 3.3
                        bitmax = 4096 
                        ADCtoVolt = vmax / bitmax
                        VCP = 0.9
                        
                        # WRITES encoded command to the serial port
                        cmd = str(startFreq) + ';' + str(stopFreq) + ';' + str(int(fStep)) + '\n'
                        self._serial.write(cmd.encode())
                        
                        # Initializes buffer and strs
                        buffer = ''
                        strs = ["" for x in range(samples + 2)]
                        
                        #################################################################################
                        # CHANGED v2.0
                        # INCREASED maxval=1000000 TO AVOID bar.update(len.buffer) BREAKS THE CALIBRATION  
                        #################################################################################
                        # READS and decodes sweep from the serial port
                        # VER 0.1.6 poll self._exit so a Stop pressed mid-sweep
                        # breaks out promptly (responsive cancellation, Q-1 v3.0).
                        while not self._exit.is_set():
                            waiting = self._serial.inWaiting()
                            # Nothing waiting: yield for a millisecond. read(0)
                            # returns at once, so without this the loop held a
                            # core at 100 % for the whole of the peak detection.
                            if waiting == 0:
                                time.sleep(0.001)
                                continue
                            chunk = self._serial.read(waiting).decode() #Constants.app_encoding
                            buffer += chunk
                            # only the end-of-sweep line carries an 's': test the
                            # chunk just read, not the whole growing buffer
                            if 's' in chunk:
                                 break
                        # If cancelled before the end-of-message marker arrived,
                        # abandon this section and let the outer sweep loop exit.
                        if self._exit.is_set() and 's' not in buffer:
                            print(TAG, "Peak Detection interrupted by user")
                            break
                        #################################################################################
                        # CHANGED v2.0
                        # PRINT LEN BUFFER WHEN THE EOM is RECEIVED
                        #################################################################################    
                        
                        # from a full buffer to a list of string
                        data_raw = buffer.split('\n')
                        length = len(data_raw)
                        
                        # PERFORMS split with the semicolon delimiter
                        for i in range (length):
                            strs[i] = data_raw[i].split(';')

                        # CONVERTS the sweep samples before adding to queue
                        for i in range (length - 1):
                            data_mag[i] = float(strs[i][0]) * ADCtoVolt / 2
                            data_mag[i] = (data_mag[i]-VCP) / 0.03
                            data_ph[i] = float(strs[i][1]) * ADCtoVolt  / 1.5
                            data_ph[i] = (data_ph[i]-VCP) / 0.01
                        
                        
                        #------------------------------
                        if k>0:
                            data_mag=data_mag[1:]
                            data_ph=data_ph[1:]
                        temp1=np.append(temp1,data_mag)
                        temp2=np.append(temp2,data_ph)
                        #------------------------------
                        print(TAG,"signal section #{}/{} acquired successfully\n".format(k+1,Constants.calib_sections), end='\r') #10
                            
                    # specify handlers for different exceptions        
                    except ValueError:
                        print(TAG, "WARNING: ValueError during signal acquisition")
                        print(TAG, "Please, repeat the calibration") 
                        self._flag = 1
                        #Log.w(TAG, "Warning: ValueError during calibration!"))

                        #################################################################################
                        # CHANGED v2.0
                        # SERIAL FLUSH INPUT OUTPUT if an EXCEPTION OCCURR  
                        #################################################################################    
                        self._serial.flushInput()
                        self._serial.flushOutput()
                        self._serial.close()
                        self.stop()

                    except:
                        print(TAG, "WARNING: generic error during signal acquisition")
                        print(TAG, "Please, repeat the calibration") 
                        self._flag = 1
                        
                        #################################################################################
                        # CHANGED v2.0
                        # SERIAL FLUSH INPUT OUTPUT if an EXCEPTION OCCURR  
                        #################################################################################    
                        self._serial.flushInput()
                        self._serial.flushOutput()
                        self._serial.close()
                        self.stop()
                    
                    #--------------------------------
                    ## ADDS new serial data to internal queue
                    self._parser1.add1(temp1)
                    self._parser2.add2(temp2)
                    #--------------------------------
                    
                    
                    # VER 0.1.4
                    # add None to the queue for the overtone number and TEC status variable 
                    self._parser6.add6([self._flag, self._flag2, self._flag2, k, None, None])
                    
                    
                    k+=1                    
                    # STOPS acquiring data
                    if k==Constants.calib_sections: #10/5
                        # VER 0.1.6G-ADAPTIVE self.stop() moved to the end of run(): the
                        # refining sweeps that follow read _exit as the user's Stop
                        break
                #### END SWEEPS LOOP

                # VER 0.1.6 user cancellation (ported from openQCM Q-1 v3.0):
                # the sweep loop exited early because Stop set self._exit while
                # still mid-run (k < calib_sections) and no acquisition error
                # occurred (_flag == 0). Normal completion calls self.stop() too,
                # but only once k == calib_sections, so it is excluded here.
                # Signal the cancellation on parser5 (-1 sentinel) and skip the
                # peak-detection / file-storage stage entirely.
                if self._exit.is_set() and k < Constants.calib_sections and self._flag == 0:
                    print(TAG, "Peak Detection interrupted by user at section {}/{}".format(
                        k, Constants.calib_sections))
                    self._parser5.add5([-1, 0])
                    if self._serial.isOpen():
                        self._serial.close()
                    return

                '''
                # CALLS baseline_correction method
                (data_mag_baseline, data_ph_baseline) = self.baseline_correction(readFREQ,temp1,temp2)
                ## ADDS serial data (baseline corrected) to internal queue
                self._parser1.add1(data_mag_baseline)
                self._parser2.add2(data_ph_baseline)
                '''
                #### STORING DATA TO FILE
                # CHECKS QCM Sensor type for saving calibration
                    
                
                # CHECKS the exceptions
                if self._flag == 0:
                   # Dev-only: the raw 1-51 MHz sweep, before any
                   # peak logic has judged it.
                   #
                   # ⚠️ Calibration_5MHz.txt is written only when the first
                   # peak looks like a 5 MHz fundamental. Right for the
                   # instrument, useless for characterising the electronics:
                   # an open, a short and a 50 ohm load have no resonance by
                   # construction, so they produce no file at all. Enabled by
                   # OPENQCM_CAL_DUMP=<label>, which also names the file so
                   # three runs cannot overwrite one another.
                   _cal = SweepDump.save_calibration_sweep(readFREQ, temp1, temp2)
                   if _cal:
                       print(TAG, "Calibration sweep dumped as {}.txt "
                             "({} points)".format(_cal, len(readFREQ)))

                   # CALLS baseline_correction method
                   print(TAG,"Baseline Correction Process Started")
                   
                   
                   # baseline correction  
                   (data_mag_baseline, data_ph_baseline) = self.baseline_correction(readFREQ,temp1,temp2)
                   ## ADDS serial data (baseline corrected) to internal queue
                   
                   self._parser1.add1(data_mag_baseline)
                   self._parser2.add2(data_ph_baseline)
                   print(TAG,"Baseline Correction Process Completed")
                   print(TAG,"Peak Detection Process Started")
                   print(TAG, "Finding peaks in acquired signals...")
                   
                   
                   # VER 0.1.6 Peak detection get the QCM Fundamental frequency and overtones 
                   
                   
                   
                   # get the QCM Fundamental frequency 
                   fundamental_baseline_corr = self.peak_detection_qcm_fundamental(readFREQ, data_mag_baseline, data_ph_baseline)
                   
                   
                   
                   
                   
                   # get the QCM overtones frequency 
                   overtones_baseline_corr = self.peak_detection_qcm_overtones(readFREQ, data_mag_baseline, data_ph_baseline, fundamental_baseline_corr)
                   
                   try:
                       # VER 0.1.6G-ADAPTIVE each peak confirmed on finer sweeps around
                       # it, so the stored peaks are where the resonances are (the wide
                       # sweep's peaks lag them by kHz) and an overtone is judged on its line
                       (fundamental_baseline_corr,
                        overtones_baseline_corr) = self._refine_peaks(fundamental_baseline_corr)
                       
                       # VER 0.1.6 peak detection  
                       
                          
                       max_freq_mag =  np.zeros(len(overtones_baseline_corr) + 1) 
                       
                       for i in range( len(overtones_baseline_corr) + 1) :
                           if (i == 0):
                               max_freq_mag[i] = fundamental_baseline_corr
                           else:
                               max_freq_mag[i] = overtones_baseline_corr[i - 1]
                       
                       print(TAG, "{} peaks were found at frequencies: {} Hz\n".format(len(max_freq_mag),max_freq_mag))
                       
                       
                         
                       # VER 0.1.6 PEAK DETECTION 
                     
                       
                       
                       # VER 0.1.6 Peak detection automatic finding the resonance frequency 
                       # 
                       if ((max_freq_mag[0]>4e+06 and max_freq_mag[0]<6e+06)):
                           
                          # set the global variable 
                          self._QCStype = '@5MHz_QCM'
                          path = Constants.cvs_peakfrequencies_path
                          path_calib = Constants.csv_calibration_path
                          filename_calib = Constants.csv_calibration_filename
                           
                          # SAVES independently of the state of the export box
                          print(TAG,"Saving data in file...")
                          np.savetxt(path, np.column_stack([max_freq_mag, max_freq_mag]))
                          path_RT = Constants.cvs_peakfrequencies_RT_path
                          np.savetxt(path_RT, np.column_stack([max_freq_mag, max_freq_mag]))
                                                                        
                          print(TAG, "Peak frequencies for {} saved in: {}".format(self._QCStype,path))
                          FileStorage.TXT_sweeps_save(filename_calib, Constants.csv_calibration_export_path, readFREQ, temp1, temp2)
                          print(TAG, "Peak frequencies for {} saved in: {}".format(self._QCStype,path_calib))
                          
                          
                       elif (max_freq_mag[0]>9e+06 and max_freq_mag[0]<11e+06): 
                          # set the global variable 
                          self._QCStype = '@10MHz_QCM'
                          path = Constants.cvs_peakfrequencies_path
                          path_calib = Constants.csv_calibration_path10
                          filename_calib = Constants.csv_calibration_filename10
                             
                          # SAVES independently of the state of the export box
                          print(TAG,"Saving data in file...")
                          np.savetxt(path, np.column_stack([max_freq_mag, max_freq_mag]))
                          path_RT = Constants.cvs_peakfrequencies_RT_path
                          np.savetxt(path_RT, np.column_stack([max_freq_mag, max_freq_mag]))
                                                                          
                          print(TAG, "Peak frequencies for {} saved in: {}".format(self._QCStype,path))
                          FileStorage.TXT_sweeps_save(filename_calib, Constants.csv_calibration_export_path, readFREQ, temp1, temp2)
                          print(TAG, "Calibration for {} saved in: {}".format(self._QCStype,path_calib))
                          
                          
                       else:
                           print(TAG, "WARNING: unable to identify fundamental peak")
                           print(TAG, "Please, repeat the calibration!")
                           self._flag2 = 1
                             
                   except peak_refine.Cancelled:
                     # Stop during the refining sweeps: as a Stop during the wide sweep,
                     # nothing saved
                     print(TAG, "Peak Detection interrupted by user while confirming the peaks")
                     self._parser5.add5([-1, 0])
                     self._serial.reset_input_buffer()
                     self._serial.close()
                     return
                   except:
                     print(TAG, "WARNING: unable to apply peak detection algorithm")
                     print(TAG, "Please, repeat the calibration!") 
                     self._flag2 = 1
                     
                if self._flag == 0 and self._flag2 == 0:
                     print(TAG, 'Peak detection completed')
                # ADDS error flags to internal queue
                self._parser5.add5([self._flag,self._flag2])    
                
                #### CLOSES serial port
                self._serial.close()
                self.stop()
                
          
    ###########################################################################
    # Stops acquiring data
    ###########################################################################
    def stop(self):
        # Signals the process to stop acquiring data.
        self._exit.set()
        
        
    ###########################################################################    
    # Automatically selects the serial ports for Teensy (macox/windows)
    ###########################################################################
    @staticmethod
    def get_ports(): 
        from openQCM.common.architecture import Architecture,OSType
        if Architecture.get_os() is OSType.macosx:
            import glob
            return glob.glob("/dev/tty.usbmodem*") 
        elif Architecture.get_os() is OSType.linux:
            import glob
            return glob.glob("/dev/ttyACM*")
        else:
            found_ports = []
            port_connected = []
            found = False
            ports_avaiable = list(list_ports.comports())
            
            # VER 0.1.5 change the iedntification of the COM port connected to Teensy 4.0 
            # using USB VID:PID=16C0:0483  VID 0 VENDOR_ID and PID = PRODUCT_ID of USB devices to identify hardware
            # port[2] = hwid Technical description of serial port 
            for port in ports_avaiable:
                if port[2].startswith("USB VID:PID=16C0:0483"):
                    found = True
                    port_connected.append(port[0])
            if found:
               found_ports = port_connected 
            return found_ports


    ###########################################################################
    # Gets a list of the common serial baud rates, in bps (only 115200 used)
    ###############################################()############################
    @staticmethod
    def get_speeds():
        #:return: List of the common baud rates, in bps :rtype: str list.
        
        # return [str(v) for v in ['@10MHz_QCM', '@5MHz_QCM']]#[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]]
        # VER 0.1.2
        return [str(v) for v in ['@5MHz_QCM', '@10MHz_QCM']]

    ###########################################################################
    # Checks if the serial port is currently connected
    ###########################################################################
    def _is_port_available(self, port):
        """
        :param port: Port name to be verified.
        :return: True if the port is connected to the host :rtype: bool.
        """
        for p in self.get_ports():
            if p == port:
                return True
        return False
    
    


