import sys
import random

import numpy as np
from PyQt6.QtWidgets import *
from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import *
from PyQt6.QtCore import *

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap

from getspectrum import readExcelData, convertDatatoDf


colors = [[1,1,1,0],[1,1,1,0.5],[0.8,0.8,0.8,1]]
cmap = LinearSegmentedColormap.from_list("", colors)

n_sample = 1024
fade_intensity = 0.15

class MainWindow(QMainWindow):
    def __init__(self):
        global cmap
        super().__init__()
        #self.setWindowTitle("PPI")
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        layout = QHBoxLayout(self.main_widget)

        # Create the Matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6), facecolor='w', tight_layout=True)
        self.figurex = Figure(figsize=(8, 6), facecolor='w', tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvasx = FigureCanvas(self.figurex)
        layout.addWidget(self.canvas)
        layout.addWidget(self.canvasx)
        
        # Initiate Variables
        # self.radius = 0
        # self.angles = np.linspace(0, np.pi, 100)
        
        # Set up for ax
        self.ax = self.figure.add_subplot(111, projection='polar', facecolor='#000000')
        # self.ax.set_position([-0.05,-0.05,1.1,1.05])
        self.ax.set_xlim([0.0,2 * np.pi]) # peak of angle to show
        self.ax.set_ylim([0.0,5]) # peak of distances to show
        self.ax.set_rticks([0, 20, 40, 60, 80, 100]) # show 5 different distances
        self.ax.tick_params(axis='both',colors='g')
        self.ax.grid(color='w',alpha=0.5) # grid color
        # self.ax.text(0.5, -0.01, "Jarak: 0", size=12, ha='center', c='w', transform=self.ax.transAxes)
        self.x1_vals = []
        self.y1_vals = []
        self.intensity = []
        self.annot = None
        self.scatter = self.ax.scatter(self.x1_vals, self.y1_vals, cmap=cmap, c=[], vmin=0, vmax=1)
        
        self.canvas.draw()
        self.canvasx.draw()
        
        self.show()

def spectrum_to_jarak(max_index):
    return max_index * 0.0576 + 0.7288
     
def spectrum_analyzer(time_data):
    n_sample_x = time_data[n_sample - 2]
    time_data[n_sample_x:n_sample] = 0
    time_data = time_data - (np.sum(time_data) / n_sample_x)
    time_data[n_sample_x:n_sample] = 0

    time_data = time_data * np.hamming(n_sample)

    data_f = 20 * np.log10(abs(np.fft.rfft(time_data)) / (n_sample_x) + 0.001)
    data_f = data_f * data_f / 15  
    
    max_idx = np.argmax(data_f)
    return spectrum_to_jarak(max_idx)

def data_updater(data):
    counter = 0
    def data_source():
        nonlocal counter
        data_now = data.iloc[counter].values
        dist = spectrum_analyzer(data_now)
        
        if counter > len(data):
            return [], []
        
        counter += 1
        return [random.uniform(0, np.pi)], [dist]
    
    return data_source

def get_updater(plot, get_new_vals):
    global fade_intensity
    def update():
        # Get intermediate points
        new_xvals, new_yvals = get_new_vals()
        
        if len(new_xvals) == 0:
            new_xvals, new_yvals = [0], [0]
            print("Done")
            
        plot.x1_vals.extend(new_xvals)
        plot.y1_vals.extend(new_yvals)

        # Put new values in your plot
        plot.scatter.set_offsets(np.c_[plot.x1_vals,plot.y1_vals])
        
        if plot.annot != None:
            plot.annot.remove()
            
        plot.annot = plot.ax.annotate("{:.2f} m".format(new_yvals[0]), (new_xvals[0], new_yvals[0]), c="w")
        
        #calculate new color values
        plot.intensity = np.concatenate((np.array(plot.intensity) * fade_intensity, np.ones(len(new_xvals))))
        plot.scatter.set_array(plot.intensity)
        plot.canvas.draw()
        
    return update

if __name__ == '__main__':
    app = QApplication([])
    plot = MainWindow()
    timer = QtCore.QTimer()
    
    raw_data = readExcelData('dataradarspectr_new.xlsx')
    raw_data = convertDatatoDf(raw_data)
    
    raw_source = data_updater(raw_data)
    
    try:
            timer.timeout.connect(get_updater(plot, raw_source))
            timer.start(1000)
            
            app.instance().exec()
    except KeyboardInterrupt:
            app.quit() 
            sys.exit()