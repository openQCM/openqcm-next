README OPENQCM NEXT VERSION 0.1.5 
-------------------------------------------------------------------------------

python version TAG: # VER 0.1.5

General information: Improved the control of MCP9808 TEC error status, using the error register message 

MAJOR UPDATE 
- Added MCP9808 TEC controller error register table. 
The MTD415T has an internal 16 bit error register, which identifies the reason why the module enters in error state. 
More information available at paragraph 6.3 "Error Register and Safety Bitmask" of MTD415T Data Sheet Rev. 1.2

- Change the identification of the COM port connected to Teensy 4.0 
using USB VID:PID=16C0:0483  VID 0 VENDOR_ID and PID = PRODUCT_ID of USB devices to identify hardware
port[2] = hwid Technical description of serial port 

MINOR UPDATE 
- TEC controller RESET procedure, increased the waiting time to 2 seconds for the transmission of  
the command enable pin on - enable pin off for module reset  
The error register can be reset using the "c" command or by setting the Enable pin to Off and On again.
- Improved firmware update procedure. Launch firmware updater also from menu bar, only if a measurement is not running

-------------------------------------------------------------------------------

python version TAG: # VER 0.1.4a

- CALIBRATION BUG unable to get the peaks, in particular 5th overtone peak. 
Reason: Speed of calibration procedure has changed, due to the change of ADC conversion parameters in firmware. This cause a distortion of the peak signals.
Solution: Decrease the calibration frequency step, from 1000 Hz to 500 Hz, in order to increase the frequency resolution. In Constants.py line 584 and subsequent lines of code
	 
	[...]
	# VER 0.1.4a CHANGE CALIBRATION  FREQUENCY STEP to 500 Hz 
    	calib_fStep = 500 
	[...]

-------------------------------------------------------------------------------

python version TAG: # VER 0.1.4

MAJOR UPDATE 
- Frequency sampling sweep: Change the frequency sampling sweep to 1 Hz to avoid distortion of the signal 
- Frequency Measurement: Change frequency measurement as the maximum of amplitude signal, the same for fundamental and all higher overtone. Multiscan.py and Serial.py
- Dissipation measurement: Change dissipation measurement defined as bandwidth at -0.3 dB below the maximum for fundamental and overtones. Multiscan.py and Serial.py
- Software update: Added update software algorithm using webpage with release information in form of HTML table. File: mainWindow.py
- Firmware update: Added update firmware algorithm, using serial communication with the microcontroller. Introducing external application for firmware update. File mainWindow.py
- Temperature control: Temperature control is improved by monitoring both the TEC status and the value of electrical current delivered by the TEC controller. 
If the TEC is in error and the electrical current is null, then the TEC controller is in error state and must be reset. 
- Sweep algorithm: Sweep algorithm is changed using a real-time tracking scheme. Tracking algorithm: the centre of the sweep band is moved dependig on the current value of the resonance frequency  

MINOR UPDATE 
- Datalog sampling time: Added the capability to set the datalog sampling time in Multiscan mode 
Default corresponds to the minimium datalog sampling time, roughly 1.5 seconds for 5 MHz up to 9th overtone.
When datalog sampling time is different from default, a ring buffer for smoothing moving average is created.
- Pop-up QMessageBox for info, warning and critical message

BETA UPDATE 
- Log data view add-on a script to view sweep raw data 
- raw data view add-on a window for viewing and processing log data view, based on Matplotlib  

TODO
- change the sg filter parameters depending on signal 
- increase sweep right range, because the sweep box is now center on the peak of the resonance curve. Constants.py   
