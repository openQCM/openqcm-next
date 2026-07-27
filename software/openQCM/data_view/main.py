from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
import pandas as pd

import random
import math

import time 

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon

from PyQt5.QtWidgets import QTextEdit

from openQCM.data_view.qt_designer_ui import Ui_MainWindow
from openQCM.core.constants import Constants

class MatplotlibWidget(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        ## Rimuovi i layout esistenti per i plot
        for i in reversed(range(self.ui.verticalLayout_5.count())): 
            self.ui.verticalLayout_5.itemAt(i).widget().setParent(None)

        # Crea due container verticali per i grafici e le loro toolbar
        self.freq_container = QVBoxLayout()
        self.diss_container = QVBoxLayout()
        
        # Configura dimensioni minime per i widget dei grafici
        self.ui.MplWidget.setMinimumHeight(250)
        self.ui.MplWidget_D.setMinimumHeight(250)
        
        # Crea e aggiungi le toolbar
        self.freq_toolbar = NavigationToolbar(self.ui.MplWidget.canvas, self)
        self.diss_toolbar = NavigationToolbar(self.ui.MplWidget_D.canvas, self)
        
        # Aggiungi toolbar e grafici ai rispettivi container
        self.freq_container.addWidget(self.freq_toolbar)
        self.freq_container.addWidget(self.ui.MplWidget)
        self.diss_container.addWidget(self.diss_toolbar)
        self.diss_container.addWidget(self.ui.MplWidget_D)
        
        # Aggiungi i container al layout verticale principale
        self.ui.verticalLayout_5.addLayout(self.freq_container)
        self.ui.verticalLayout_5.addLayout(self.diss_container)
        
        # Configure plot styles and formatting
        self.setup_plot_styles()
        
        # Connect buttons
        self.ui.getFile_btn.clicked.connect(self.openFileNameDialog)
        self.ui.process_btn.clicked.connect(self.process_data)
        
        # Initialize variables
        self.filename_csv = ""
        self.vertical_lines = []
        self.vertical_lines_D = []
        
        # Clear text output
        self.ui.textEdit.setPlainText("")
        
        # Initial plot setup
        self.init_plots()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.filename_csv, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV Data File",
            "",
            "CSV Files (*.csv);;All Files (*)",
            options=options
        )
        if self.filename_csv:
            self.get_data()
            self.update_graph()

    def get_data(self):
        try:
            # Read CSV file using pandas
            data = pd.read_csv(self.filename_csv)
            
            # Get basic data
            self.Date = data['Date'].tolist()
            self.Time = data['Time'].tolist()
            self.time_relative = np.asarray(data[['Relative_time']])
            self.temperature = np.asarray(data[['Temperature']])

            # Handle both single and multi-measurement formats
            if "Resonance_Frequency" in data.columns and "Dissipation" in data.columns:
                # Single measurement format
                self.f_0 = np.asarray(data["Resonance_Frequency"])
                self.d_0 = np.asarray(data["Dissipation"])
                length = len(self.f_0)

                # Create empty arrays for other measurements
                self.f_1 = np.full(length, np.nan)
                self.d_1 = np.full(length, np.nan)
                self.f_2 = np.full(length, np.nan)
                self.d_2 = np.full(length, np.nan)
                self.f_3 = np.full(length, np.nan)
                self.d_3 = np.full(length, np.nan)
                self.f_4 = np.full(length, np.nan)
                self.d_4 = np.full(length, np.nan)
            else:
                # Multi-measurement format
                self.f_0 = np.asarray(data[['Frequency_0']])
                self.d_0 = np.asarray(data[["Dissipation_0"]])
                self.f_1 = np.asarray(data[["Frequency_1"]])
                self.d_1 = np.asarray(data[["Dissipation_1"]])
                self.f_2 = np.asarray(data[["Frequency_2"]])
                self.d_2 = np.asarray(data[["Dissipation_2"]])
                self.f_3 = np.asarray(data[["Frequency_3"]])
                self.d_3 = np.asarray(data[["Dissipation_3"]])
                self.f_4 = np.asarray(data[["Frequency_4"]])
                self.d_4 = np.asarray(data[["Dissipation_4"]])

            # Set zero reference for frequency
            self.f_0 = self.f_0 - self.f_0[0]
            self.f_1 = self.f_1 - self.f_1[0]
            self.f_2 = self.f_2 - self.f_2[0]
            self.f_3 = self.f_3 - self.f_3[0]
            self.f_4 = self.f_4 - self.f_4[0]

            # Scale dissipation and set zero reference
            scale = 1000000
            self.d_0 = (self.d_0 - self.d_0[0]) * scale
            self.d_1 = (self.d_1 - self.d_1[0]) * scale
            self.d_2 = (self.d_2 - self.d_2[0]) * scale
            self.d_3 = (self.d_3 - self.d_3[0]) * scale
            self.d_4 = (self.d_4 - self.d_4[0]) * scale

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading data: {str(e)}")

    def setup_plot_styles(self):
        # Common style settings for both plots
        plot_bg_color = (25/255, 25/255, 25/255)
        text_color = 'white'
        
        for widget in [self.ui.MplWidget, self.ui.MplWidget_D]:
            # Configure axes background
            widget.canvas.axes.set_facecolor(plot_bg_color)
            widget.canvas.figure.set_facecolor(plot_bg_color)
            
            # Configure spines
            for spine in widget.canvas.axes.spines.values():
                spine.set_edgecolor(text_color)
            
            # Configure ticks
            widget.canvas.axes.tick_params(axis='both', colors=text_color, which='both')
            
            # Set figure margins
            widget.canvas.figure.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
            
            # Enable grid with custom style
            widget.canvas.axes.grid(True, linestyle='--', alpha=0.3, color='gray')

    def init_plots(self):
        # Initialize frequency plot
        self.ui.MplWidget.canvas.axes.clear()
        self.setup_frequency_plot()
        self.ui.MplWidget.canvas.draw()
        
        # Initialize dissipation plot
        self.ui.MplWidget_D.canvas.axes.clear()
        self.setup_dissipation_plot()
        self.ui.MplWidget_D.canvas.draw()

    def setup_frequency_plot(self):
        self.ui.MplWidget.canvas.axes.set_xlabel("Relative Time (sec)", color='white')
        self.ui.MplWidget.canvas.axes.set_ylabel("Frequency shift (Hz)", color='white')
        self.ui.MplWidget.canvas.axes.set_title("Frequency Data", color='white', pad=10)

    def setup_dissipation_plot(self):
        self.ui.MplWidget_D.canvas.axes.set_xlabel("Relative Time (sec)", color='white')
        self.ui.MplWidget_D.canvas.axes.set_ylabel("Dissipation shift", color='white')
        self.ui.MplWidget_D.canvas.axes.set_title("Dissipation Data", color='white', pad=10)

    def update_graph(self):
        if not hasattr(self, 'time_relative'):
            return

        plot_colors = []
        for color in Constants.plot_color_multi:
            normalized_color = tuple(x/255 for x in color)
            plot_colors.append(normalized_color)
        
        label_plot_F = ["F_0", "F_3", "F_5", "F_7", "F_9"]
        label_plot_D = ["D_0", "D_3", "D_5", "D_7", "D_9"]
        
        # Update frequency plot
        self.ui.MplWidget.canvas.axes.clear()
        self.setup_frequency_plot()
        
        for i, (freq, label, color) in enumerate(zip(
            [self.f_0, self.f_1, self.f_2, self.f_3, self.f_4],
            label_plot_F,
            plot_colors
        )):
            self.ui.MplWidget.canvas.axes.plot(
                self.time_relative, freq,
                color=color, label=label, linewidth=1.2
            )
        
        if np.all(~np.isnan(self.f_1)):
            legend = self.ui.MplWidget.canvas.axes.legend(
                loc='best',
                frameon=True,
                facecolor=(25/255, 25/255, 25/255),
                edgecolor='gray'
            )
            for text in legend.get_texts():
                text.set_color("white")
        
        # Update dissipation plot
        self.ui.MplWidget_D.canvas.axes.clear()
        self.setup_dissipation_plot()
        
        for i, (diss, label, color) in enumerate(zip(
            [self.d_0, self.d_1, self.d_2, self.d_3, self.d_4],
            label_plot_D,
            plot_colors
        )):
            self.ui.MplWidget_D.canvas.axes.plot(
                self.time_relative, diss,
                color=color, label=label, linewidth=1.2
            )
        
        if np.all(~np.isnan(self.d_1)):
            legend_D = self.ui.MplWidget_D.canvas.axes.legend(
                loc='best',
                frameon=True,
                facecolor=(25/255, 25/255, 25/255),
                edgecolor='gray'
            )
            for text in legend_D.get_texts():
                text.set_color("white")
        
        self.ui.MplWidget.canvas.draw()
        self.ui.MplWidget_D.canvas.draw()
        
        
    def process_data(self):
        
        
        
        print ("DATA PROCESSING")
        # Get initial times and durations
        initial_start = self.ui.time_initial.value()
        initial_duration = self.ui.time_initial_stop.value()
        
        final_start = self.ui.time_final.value()
        final_duration = self.ui.time_final_stop.value()
    
        # Calculate end points based on initial times and durations
        initial_end = initial_start + initial_duration
        final_end = final_start + final_duration
    
        # Get indices for initial segment
        for i in range(len(self.time_relative)):
            if self.time_relative[i] > initial_start:
                break
        print(f"Initial start index: {i}")
        
        for j in range(len(self.time_relative)):
            if self.time_relative[j] > initial_end:
                break
        print(f"Initial end index: {j}")
    
        # Get indices for final segment
        for k in range(len(self.time_relative)):
            if self.time_relative[k] > final_start:
                break
        print(f"Final start index: {k}")
        
        for l in range(len(self.time_relative)):
            if self.time_relative[l] > final_end:
                break
        print(f"Final end index: {l}")
    
        # Clear existing vertical lines
        for line in self.vertical_lines:
            line.remove()
        self.vertical_lines.clear()
        self.ui.MplWidget.canvas.draw()
    
        # Add new vertical lines at the segment boundaries
        times = [initial_start, initial_end, final_start, final_end]
        for t in times:
            line = self.ui.MplWidget.canvas.axes.axvline(x=t, color='red', linestyle='--')
            self.vertical_lines.append(line)
        self.ui.MplWidget.canvas.draw()
    
        # Do the same for dissipation plot
        for line_D in self.vertical_lines_D:
            line_D.remove()
        self.vertical_lines_D.clear()
        self.ui.MplWidget_D.canvas.draw()
        
        for t in times:
            line_D = self.ui.MplWidget_D.canvas.axes.axvline(x=t, color='red', linestyle='--')
            self.vertical_lines_D.append(line_D)
        self.ui.MplWidget_D.canvas.draw()
        

        # averaging frequency initial        
        f_0_average = np.average(self.f_0[i:j])
        f_1_average = np.average(self.f_1[i:j])
        f_2_average = np.average(self.f_2[i:j])
        f_3_average = np.average(self.f_3[i:j])
        f_4_average = np.average(self.f_4[i:j])
        # standard deviation frequency initial 
        f_0_std = np.std(self.f_0[i:j])
        f_1_std = np.std(self.f_1[i:j])
        f_2_std = np.std(self.f_2[i:j])
        f_3_std = np.std(self.f_3[i:j])
        f_4_std = np.std(self.f_4[i:j])

        # HADAMARD VARIANCE INITIAL STATE  
        # print the initia time interval 
        print ("INITIAL TIME INTERVAL = ", self.time_relative[j] - self.time_relative[i])

        # Hadamard variance 
        f_0_hadamard_square_sum = 0
        f_0_hadamard_square = 0
        f_0_hadamard = 0
        for nn in range (i,j):
            f_0_hadamard_square_sum += (self.f_0[nn-1] - 2 * self.f_0[nn] +  self.f_0[nn+1])**2
        f_0_hadamard_square = f_0_hadamard_square_sum / (6 * (j-i))
        f_0_hadamard = math.sqrt(f_0_hadamard_square)

        # Hadamard variance 
        f_1_hadamard_square_sum = 0
        f_1_hadamard_square = 0
        f_1_hadamard = 0
        for nn in range (i,j):
            f_1_hadamard_square_sum += (self.f_1[nn-1] - 2 * self.f_1[nn] +  self.f_1[nn+1])**2
        f_1_hadamard_square = f_1_hadamard_square_sum / (6 * (j-i))
        f_1_hadamard = math.sqrt(f_1_hadamard_square)

        # Hadamard variance 
        f_2_hadamard_square_sum = 0
        f_2_hadamard_square = 0
        f_2_hadamard = 0
        for nn in range (i,j):
            f_2_hadamard_square_sum += (self.f_2[nn-1] - 2 * self.f_2[nn] +  self.f_2[nn+1])**2
        f_2_hadamard_square = f_2_hadamard_square_sum / (6 * (j-i))
        f_2_hadamard = math.sqrt(f_2_hadamard_square)

        # Hadamard variance 
        f_3_hadamard_square_sum = 0
        f_3_hadamard_square = 0
        f_3_hadamard = 0
        for nn in range (i,j):
            f_3_hadamard_square_sum += (self.f_3[nn-1] - 2 * self.f_3[nn] +  self.f_3[nn+1])**2
        f_3_hadamard_square = f_3_hadamard_square_sum / (6 * (j-i))
        f_3_hadamard = math.sqrt(f_3_hadamard_square)

        # Hadamard variance 
        f_4_hadamard_square_sum = 0
        f_4_hadamard_square = 0
        f_4_hadamard = 0
        for nn in range (i,j):
            f_4_hadamard_square_sum += (self.f_4[nn-1] - 2 * self.f_4[nn] +  self.f_4[nn+1])**2
        f_4_hadamard_square = f_4_hadamard_square_sum / (6 * (j-i))
        f_4_hadamard = math.sqrt(f_4_hadamard_square)

        # PRINT HADAMARD VARIANCE




        # averaging dissipation initial
        d_0_average = np.average(self.d_0[i:j])
        d_1_average = np.average(self.d_1[i:j])
        d_2_average = np.average(self.d_2[i:j])
        d_3_average = np.average(self.d_3[i:j])
        d_4_average = np.average(self.d_4[i:j])
        # standard deviation dissipation initial 
        d_0_std = np.std(self.d_0[i:j])
        d_1_std= np.std(self.d_1[i:j])
        d_2_std = np.std(self.d_2[i:j])
        d_3_std = np.std(self.d_3[i:j])
        d_4_std = np.std(self.d_4[i:j])
        
        #l = k + 10
        # averaging frequency final        
        f_0_average_l = np.average(self.f_0[k:l])
        f_1_average_l = np.average(self.f_1[k:l])
        f_2_average_l = np.average(self.f_2[k:l])
        f_3_average_l = np.average(self.f_3[k:l])
        f_4_average_l = np.average(self.f_4[k:l])
        
        # standard deviation frequency final 
        f_0_std_l = np.std(self.f_0[k:l])
        f_1_std_l = np.std(self.f_1[k:l])
        f_2_std_l  = np.std(self.f_2[k:l])
        f_3_std_l = np.std(self.f_3[k:l])
        f_4_std_l = np.std(self.f_4[k:l])
        # averaging dissipation initial
        d_0_average_l = np.average(self.d_0[k:l])
        d_1_average_l = np.average(self.d_1[k:l])
        d_2_average_l = np.average(self.d_2[k:l])
        d_3_average_l = np.average(self.d_3[k:l])
        d_4_average_l = np.average(self.d_4[k:l])
        # standard deviation dissipation initial 
        d_0_std_l = np.std(self.d_0[k:l])
        d_1_std_l = np.std(self.d_1[k:l])
        d_2_std_l = np.std(self.d_2[k:l])
        d_3_std_l = np.std(self.d_3[k:l])
        d_4_std_l = np.std(self.d_4[k:l])

        # print the initia time interval 
        print ("FINAL TIME INTERVAL = ", self.time_relative[j] - self.time_relative[i])

        # Hadamard variance 
        f_0_hadamard_square_sum_l = 0
        f_0_hadamard_square_l = 0
        f_0_hadamard_l = 0
        for nn in range (k,l):
            f_0_hadamard_square_sum_l += (self.f_0[nn-1] - 2 * self.f_0[nn] +  self.f_0[nn+1])**2
        f_0_hadamard_square_l = f_0_hadamard_square_sum_l / (6 * (j-i))
        f_0_hadamard_l = math.sqrt(f_0_hadamard_square_l)

        # Hadamard variance 
        f_1_hadamard_square_sum_l = 0
        f_1_hadamard_square_l = 0
        f_1_hadamard_l = 0
        for nn in range (k,l):
            f_1_hadamard_square_sum_l += (self.f_1[nn-1] - 2 * self.f_1[nn] +  self.f_1[nn+1])**2
        f_1_hadamard_square_l = f_1_hadamard_square_sum_l / (6 * (j-i))
        f_1_hadamard_l = math.sqrt(f_1_hadamard_square_l)

        # Hadamard variance 
        f_2_hadamard_square_sum_l = 0
        f_2_hadamard_square_l = 0
        f_2_hadamard_l = 0
        for nn in range (k,l):
            f_2_hadamard_square_sum_l += (self.f_2[nn-1] - 2 * self.f_2[nn] +  self.f_2[nn+1])**2
        f_2_hadamard_square_l = f_2_hadamard_square_sum_l / (6 * (j-i))
        f_2_hadamard_l = math.sqrt(f_2_hadamard_square_l)

        # Hadamard variance 
        f_3_hadamard_square_sum_l = 0
        f_3_hadamard_square_l = 0
        f_3_hadamard_l = 0
        for nn in range (k,l):
            f_3_hadamard_square_sum_l += (self.f_3[nn-1] - 2 * self.f_3[nn] +  self.f_3[nn+1])**2
        f_3_hadamard_square_l = f_3_hadamard_square_sum_l / (6 * (j-i))
        f_3_hadamard_l = math.sqrt(f_3_hadamard_square_l)

        # Hadamard variance 
        f_4_hadamard_square_sum_l = 0
        f_4_hadamard_square_l = 0
        f_4_hadamard_l = 0
        for nn in range (k,l):
            f_4_hadamard_square_sum_l += (self.f_4[nn-1] - 2 * self.f_4[nn] +  self.f_4[nn+1])**2
        f_4_hadamard_square_l = f_4_hadamard_square_sum_l / (6 * (j-i))
        f_4_hadamard_l = math.sqrt(f_4_hadamard_square_l)



        
        print ("Frequency variation (Hz):")
        print ("Fundamental  = ", "%.2f" % (f_0_average_l - f_0_average))
        print ("3rd Overtone = ", "%.2f" % (f_1_average_l - f_1_average))
        print ("5th Overtone = ", "%.2f" % (f_2_average_l - f_2_average))
        print ("7th Overtone = ", "%.2f" % (f_3_average_l - f_3_average))
        print ("9th Overtone = ", "%.2f" % (f_4_average_l - f_4_average))
        print("")
        
        print ("Dissipation variation (ppm):")
        print ("Fundamental  = ", "%.2f" % (d_0_average_l - d_0_average))
        print ("3rd Overtone = ", "%.2f" % (d_1_average_l - d_1_average))
        print ("5th Overtone = ", "%.2f" % (d_2_average_l - d_2_average))
        print ("7th Overtone = ", "%.2f" % (d_3_average_l - d_3_average))
        print ("9th Overtone = ", "%.2f" % (d_4_average_l - d_4_average))
        
        # clear the output 
        self.ui.textEdit.setPlainText("")
        
        self.ui.textEdit.append("Frequency variation (Hz):")
        self.ui.textEdit.append("Fundamental  = " + "{:.2f}".format(f_0_average_l - f_0_average))
        self.ui.textEdit.append("3rd Overtone = " + "{:.2f}".format(f_1_average_l - f_1_average))
        self.ui.textEdit.append("5th Overtone = " + "{:.2f}".format(f_2_average_l - f_2_average))
        self.ui.textEdit.append("7th Overtone = " + "{:.2f}".format(f_3_average_l - f_3_average))
        self.ui.textEdit.append("9th Overtone = " + "{:.2f}".format(f_4_average_l - f_4_average))
        self.ui.textEdit.append("")
        
        self.ui.textEdit.append("Dissipation variation (ppm):")
        self.ui.textEdit.append("Fundamental  = " + "{:.2f}".format(d_0_average_l - d_0_average))
        self.ui.textEdit.append("3rd Overtone = " + "{:.2f}".format(d_1_average_l - d_1_average))
        self.ui.textEdit.append("5th Overtone = " + "{:.2f}".format(d_2_average_l - d_2_average))
        self.ui.textEdit.append("7th Overtone = " + "{:.2f}".format(d_3_average_l - d_3_average))
        self.ui.textEdit.append("9th Overtone = " + "{:.2f}".format(d_4_average_l - d_4_average))
        self.ui.textEdit.append("")
        
        self.ui.textEdit.append("Frequency Hadamard variance initial state (Hz): ")
        self.ui.textEdit.append("Fundamental  = " + "{:.2f}".format(f_0_hadamard))
        self.ui.textEdit.append("3rd Overtone = " + "{:.2f}".format(f_1_hadamard/3.0))
        self.ui.textEdit.append("5th Overtone = " + "{:.2f}".format(f_2_hadamard/5.0))
        self.ui.textEdit.append("7th Overtone = " + "{:.2f}".format(f_3_hadamard/7.0))
        self.ui.textEdit.append("9th Overtone = " + "{:.2f}".format(f_3_hadamard/9.0))
        self.ui.textEdit.append("")

        self.ui.textEdit.append("Frequency Hadamard variance final state (Hz): ")
        self.ui.textEdit.append("Fundamental  = " + "{:.2f}".format(f_0_hadamard_l))
        self.ui.textEdit.append("3rd Overtone = " + "{:.2f}".format(f_1_hadamard_l/3.0))
        self.ui.textEdit.append("5th Overtone = " + "{:.2f}".format(f_2_hadamard_l/5.0))
        self.ui.textEdit.append("7th Overtone = " + "{:.2f}".format(f_3_hadamard_l/7.0))
        self.ui.textEdit.append("9th Overtone = " + "{:.2f}".format(f_3_hadamard_l/9.0))
        self.ui.textEdit.append("")

    
# =============================================================================
#         self.output_text.appendPlainText(str("Fundamental  =  \n"))
# =============================================================================
        
        
        print ("FREQUENCY average values and standard deviation (Hz):")
        print ("INITIAL ")
        print ("F_0 = ", "%.2f" % f_0_average, "±", "%.2f" % f_0_std)
        print ("F_3 = ", "%.2f" % f_1_average, "±", "%.2f" % f_1_std)
        print ("F_5 = ", "%.2f" % f_2_average, "±", "%.2f" % f_2_std)
        print ("F_7 = ", "%.2f" % f_3_average, "±", "%.2f" % f_3_std)
        print ("F_9 = ", "%.2f" % f_4_average, "±", "%.2f" % f_4_std)
        print("")
        
        print ("FINAL ")
        print ("F_0 = ", "%.2f" % f_0_average_l, "±", "%.2f" % f_0_std_l)
        print ("F_3 = ", "%.2f" % f_1_average_l, "±", "%.2f" % f_1_std_l)
        print ("F_5 = ", "%.2f" % f_2_average_l, "±", "%.2f" % f_2_std_l)
        print ("F_7 = ", "%.2f" % f_3_average_l, "±", "%.2f" % f_3_std_l)
        print ("F_9 = ", "%.2f" % f_4_average_l, "±", "%.2f" % f_4_std_l)
        print("")
        print("----------------------------------------------------------------")
        
        print ("DISSIPATION average values and standard deviation (ppm):")
        print ("INITIAL ")
        print ("D_0 = ", "%.2f" % d_0_average, "±", "%.2f" % d_0_std)
        print ("D_3 = ", "%.2f" % d_1_average, "±", "%.2f" % d_1_std)
        print ("D_5 = ", "%.2f" % d_2_average, "±", "%.2f" % d_2_std)
        print ("D_7 = ", "%.2f" % d_3_average, "±", "%.2f" % d_3_std)
        print ("D_9 = ", "%.2f" % d_4_average, "±", "%.2f" % d_4_std)
        
        print ("FINAL")
        print ("D_0 = ", "%.2f" % d_0_average_l, "±", "%.2f" % d_0_std_l)
        print ("D_3 = ", "%.2f" % d_1_average_l, "±", "%.2f" % d_1_std_l)
        print ("D_5 = ", "%.2f" % d_2_average_l, "±", "%.2f" % d_2_std_l)
        print ("D_7 = ", "%.2f" % d_3_average_l, "±", "%.2f" % d_3_std_l)
        print ("D_9 = ", "%.2f" % d_4_average_l, "±", "%.2f" % d_4_std_l)
        print("")
        print("----------------------------------------------------------------")
        
        print("")
        print ("Frequency variation (Hz):")
        print ("Fundamental  = ", "%.2f" % (f_0_average_l - f_0_average))
        print ("3rd Overtone = ", "%.2f" % (f_1_average_l - f_1_average))
        print ("5th Overtone = ", "%.2f" % (f_2_average_l - f_2_average))
        print ("7th Overtone = ", "%.2f" % (f_3_average_l - f_3_average))
        print ("9th Overtone = ", "%.2f" % (f_4_average_l - f_4_average))
        print("")
        
        print ("Dissipation variation (ppm):")
        print ("Fundamental  = ", "%.2f" % (d_0_average_l - d_0_average))
        print ("3rd Overtone = ", "%.2f" % (d_1_average_l - d_1_average))
        print ("5th Overtone = ", "%.2f" % (d_2_average_l - d_2_average))
        print ("7th Overtone = ", "%.2f" % (d_3_average_l - d_3_average))
        print ("9th Overtone = ", "%.2f" % (d_4_average_l - d_4_average))
        print("----------------------------------------------------------------")

        
# -------------------------


# =============================================================================
# if __name__ == '__main__':
#         import sys
#         if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#             QtGui.QApplication.instance().exec_()
# 
# =============================================================================


# =============================================================================
# app = QApplication([])
# # =============================================================================
# # window = MatplotlibWidget()
# # window.show()
# # =============================================================================
# app.exec_()
# =============================================================================


if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        app = QApplication([])
        app.instance().exec_()