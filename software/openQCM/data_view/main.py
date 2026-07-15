# ------------------------------------------------------
# ---------------------- main.py -----------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import*
from PyQt5.uic import loadUi

from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)

import numpy as np
import random
import math

from numpy import loadtxt
import pandas as pd
import time 

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon

from PyQt5.QtWidgets import QTextEdit

from openQCM.data_view.qt_designer_ui import Ui_MainWindow

# =============================================================================
# from openQCM.data_view.mplwidget import MplWidget
# =============================================================================
# from openQCM.data_view.mplwidget import MplWidget
     
class MatplotlibWidget(QMainWindow):
    
    
    def __init__(self):
        
        QMainWindow.__init__(self)
      
        # loadUi("openQCM/data_view/qt_designer.ui",self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # self.setWindowTitle("PyQt5 & Matplotlib Example GUI")

        self.ui.pushButton.clicked.connect(self.update_graph)
        self.ui.getFile_btn.clicked.connect(self.openFileNameDialog)
        self.ui.process_btn.clicked.connect(self.process_data)

        self.addToolBar(NavigationToolbar(self.ui.MplWidget.canvas, self))
        self.addToolBar(NavigationToolbar(self.ui.MplWidget_D.canvas, self))
        
        self.filename_csv = ""
        self.ui.textEdit.setPlainText("")
        

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.filename_csv, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","CSV File (*.csv);;All Files (*)", options=options)
        if self.filename_csv:
            print(self.filename_csv)
            self.get_data()
            self.update_graph()
            
    
    
    def get_data(self):
        # filename = "2022-Feb-17_11-42-19_multi_.csv"
        
        # use pandas to analyze data https://pandas.pydata.org/docs/index.html
        data = pd.read_csv(self.filename_csv)
        # get raw data
        self.Date = data['Date'].tolist() # TODO why list ?
        self.Time = data['Time'].tolist() # TODO why list ?
        self.time_relative = np.asarray( data[['Relative_time']] )
        self.temperature = np.asarray( data[['Temperature']] )

        self.f_0 = np.asarray( data[ ['Frequency_0'] ] )
        self.d_0 = np.asarray( data[ ["Dissipation_0"] ] )
             
        self.f_1 = np.asarray( data[ ["Frequency_1"] ] )
        self.d_1 = np.asarray( data[ ["Dissipation_1"] ] )
            
        self.f_2 = np.asarray( data[ ["Frequency_2"] ] )
        self.d_2 = np.asarray( data[ ["Dissipation_2"] ] )

        self.f_3 = np.asarray( data[ ["Frequency_3"] ] )
        self.d_3 = np.asarray( data[ ["Dissipation_3"] ] )

        self.f_4 = np.asarray( data[ ["Frequency_4"] ] )
        self.d_4 = np.asarray( data[ ["Dissipation_4"] ] )
        
        # frequency set zero 
        self.f_0 = self.f_0 - self.f_0[0]
        self.f_1 = self.f_1 - self.f_1[0]
        self.f_2 = self.f_2 - self.f_2[0]
        self.f_3 = self.f_3 - self.f_3[0]
        self.f_4 = self.f_4 - self.f_4[0]
        
        # dissipation set zero and scale 
        scale = 1000000
        self.d_0 = (self.d_0 - self.d_0[0]) * scale
        self.d_1 = (self.d_1 - self.d_1[0]) * scale
        self.d_2 = (self.d_2 - self.d_2[0]) * scale
        self.d_3 = (self.d_3 - self.d_3[0]) * scale
        self.d_4 = (self.d_4 - self.d_4[0]) * scale
        

    def update_graph(self):
        
        
        plot_colors = ['#DF0101','#3C3C3C','#01DF01', '#01A9DB', '#7401DF'] 
        label_plot_F = ["F_0", "F_3", "F_5", "F_7", "F_9"]
        label_plot_D = ["D_0", "D_3", "D_5", "D_7", "D_9"]

        self.get_data()
        
        # PLOT FREQUENCY 
        # clear frequency chart 
        self.ui.MplWidget.canvas.axes.clear()
        self.ui.MplWidget.canvas.axes.plot(self.time_relative, self.f_0, color = plot_colors[0], label = label_plot_F[0], linewidth = 0.8)
        self.ui.MplWidget.canvas.axes.plot(self.time_relative, self.f_1, color = plot_colors[1], label = label_plot_F[1], linewidth = 0.8)
        self.ui.MplWidget.canvas.axes.plot(self.time_relative, self.f_2, color = plot_colors[2], label = label_plot_F[2], linewidth = 0.8)
        self.ui.MplWidget.canvas.axes.plot(self.time_relative, self.f_3, color = plot_colors[3], label = label_plot_F[3], linewidth = 0.8)
        self.ui.MplWidget.canvas.axes.plot(self.time_relative, self.f_4, color = plot_colors[4], label = label_plot_F[4], linewidth = 0.8)
        
        # self.ui.MplWidget.canvas.axes.plot(t, sinus_signal)
        # self.ui.MplWidget.canvas.axes.legend(('cosinus', 'sinus'),loc='upper right')
        # self.ui.MplWidget.canvas.axes.set_title('Cosinus - Sinus Signal')
        self.ui.MplWidget.canvas.axes.set_xlabel("Relative Time (sec)")
        self.ui.MplWidget.canvas.axes.set_ylabel("Frequency shift (Hz)")
        self.ui.MplWidget.canvas.axes.set_title("Frequency Data")
        # legend text comes from the plot's label parameter.
        self.ui.MplWidget.canvas.axes.legend(loc = 'best')
        self.ui.MplWidget.canvas.draw()
        
        
        # DISSIPATION  
        # clear dissipation chart 
        self.ui.MplWidget_D.canvas.axes.clear()
        self.ui.MplWidget_D.canvas.axes.plot(self.time_relative, self.d_0, color = plot_colors[0], label = label_plot_D[0], linewidth = 0.8)
        self.ui.MplWidget_D.canvas.axes.plot(self.time_relative, self.d_1, color = plot_colors[1], label = label_plot_D[1], linewidth = 0.8)
        self.ui.MplWidget_D.canvas.axes.plot(self.time_relative, self.d_2, color = plot_colors[2], label = label_plot_D[2], linewidth = 0.8)
        self.ui.MplWidget_D.canvas.axes.plot(self.time_relative, self.d_3, color = plot_colors[3], label = label_plot_D[3], linewidth = 0.8)
        self.ui.MplWidget_D.canvas.axes.plot(self.time_relative, self.d_4, color = plot_colors[4], label = label_plot_D[4], linewidth = 0.8)
        
        # self.ui.MplWidget_D.canvas.axes.plot(t, sinus_signal)
        # self.ui.MplWidget_D.canvas.axes.legend(('cosinus', 'sinus'),loc='upper right')
        # self.ui.MplWidget_D.canvas.axes.set_title('Cosinus - Sinus Signal')
        self.ui.MplWidget_D.canvas.axes.set_xlabel("Relative Time (sec)")
        self.ui.MplWidget_D.canvas.axes.set_ylabel("Dissipation shift")
        self.ui.MplWidget_D.canvas.axes.set_title("Dissipation Data")
        # legend text comes from the plot's label parameter.
        self.ui.MplWidget_D.canvas.axes.legend(loc = 'best')
        self.ui.MplWidget_D.canvas.draw()
        
        
    def process_data(self):
        
        
        
        print ("DATA PROCESSING")
        print (self.ui.time_initial.value())
        print (self.ui.time_final.value())
        
        # DATA PROCESSING: RAW DATA NO REFERENCE TO INITIAL VALUES 
        print("----------------------------------------------------------------")
        print ("DATA PROCESSING: RAW DATA NO REFERENCE TO INITIAL VALUES")
        print("")
        
# =============================================================================
#         initial_start = int(input())
#         print ("Enter #1 stop time: ")
#         initial_stop = int(input())
#         
#         print ("Enter #2 start time: ")
#         final_start = int(input())
#         print ("Enter #2 stop time: ")
#         final_stop = int(input())
# =============================================================================
        
        initial_start = self.ui.time_initial.value()
        initial_stop = self.ui.time_initial_stop.value()
        
        final_stop = self.ui.time_final.value()
        final_stop_stop = self.ui.time_final_stop.value()

        # get initial start index 
        for i in range(len(self.time_relative)):
            if self.time_relative[i] > initial_start:
                break
        print (i)
        # get final start index
        for j in range(len(self.time_relative)):
             if self.time_relative[j] > initial_stop:
                 break
        print (j)

        # get final start index 
        for k in range(len(self.time_relative)):
            if self.time_relative[k] > final_stop:
                break
        print (k)
        # get final start index 
        for l in range(len(self.time_relative)):
            if self.time_relative[l] > final_stop_stop:
                break
        print (l)

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
        
        self.ui.textEdit.setPlainText("")


        self.ui.textEdit.append("Frequency Hadamard variance initial state  ")
        self.ui.textEdit.append("Fundamental  = " + "{:.2f}".format(f_0_hadamard))
        self.ui.textEdit.append("3rd Overtone = " + "{:.2f}".format(f_1_hadamard/3.0))
        self.ui.textEdit.append("5th Overtone = " + "{:.2f}".format(f_2_hadamard/5.0))
        self.ui.textEdit.append("7th Overtone = " + "{:.2f}".format(f_3_hadamard/7.0))
        self.ui.textEdit.append("9th Overtone = " + "{:.2f}".format(f_3_hadamard/9.0))

        self.ui.textEdit.append("Frequency Hadamard variance final state  ")
        self.ui.textEdit.append("Fundamental  = " + "{:.2f}".format(f_0_hadamard_l))
        self.ui.textEdit.append("3rd Overtone = " + "{:.2f}".format(f_1_hadamard_l/3.0))
        self.ui.textEdit.append("5th Overtone = " + "{:.2f}".format(f_2_hadamard_l/5.0))
        self.ui.textEdit.append("7th Overtone = " + "{:.2f}".format(f_3_hadamard_l/7.0))
        self.ui.textEdit.append("9th Overtone = " + "{:.2f}".format(f_3_hadamard_l/9.0))


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