import sys
from sys import argv
import getopt
import random
from collections import Counter

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


# Fade Effects Parameter
colors = [[1,1,1,0],[1,1,1,0.5],[0.8,0.8,0.8,1]]
cmap = LinearSegmentedColormap.from_list("", colors)
fade_intensity = 0.15

# serial interface
# import serial

n_sample = 1024
SENTINEL = []

USE_SERIAL = False
SERIAL_PORT = None

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
        
        self.ax.set_xlim([1/4 * np.pi ,3/4 * np.pi]) # peak of angle to show
        self.ax.set_ylim([0.0,90]) # peak of distances to show
        self.ax.set_rticks([0, 20, 30, 50, 90]) # show 5 different distances
        
        self.ax.tick_params(axis='both',colors='g')
        self.ax.grid(color='w',alpha=0.5) # grid color
        
        # self.scatter = self.ax.scatter(self.x1_vals, self.y1_vals, cmap=cmap, c=[], vmin=0, vmax=1)
        
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

def process():
    NotImplemented

def most_common_dist(array):
    # Count the occurrences of each element in the array
    count = Counter(array)
    
    # Find the most common element and its count
    most_common = count.most_common(1)
    
    return most_common[0][0] if most_common else None
    
def data_updater(data_gen):
    dists = [0 for i in range(5)]
    k = 0
    def data_source():
        nonlocal dists, k
        data_now = data_gen()
        
        if len(data_now) == 0:
            return [], []
        
        dist = spectrum_analyzer(data_now)
        
        if k == 5:
            common_dist = most_common_dist(dists)
            print(common_dist)
            k = k * 0
            return [random.uniform(1/4 * np.pi, 5/4 * np.pi)], [common_dist]
            
        dists[k] = dist
        k += 1
        
        return [], []
        
    
    return data_source

def get_updater(plot, get_new_vals):
    global fade_intensity
    def update():
        # Get intermediate points
        new_xvals, new_yvals = get_new_vals()
        
        if len(new_xvals) == 0:
            return
                
        plot.ax.clear()
        plot.ax.set_xlim([1/4 * np.pi ,3/4 * np.pi]) # peak of angle to show
        plot.ax.set_ylim([0.0,90]) # peak of distances to show
        plot.ax.set_rticks([0, 20, 30, 50, 90]) # show 5 different distances
        
        plot.annot = plot.ax.annotate("{:.2f} m".format(new_yvals[0]), (new_xvals[0], new_yvals[0]), c="w")
        
        dt = 1/18 * np.pi
        t1, t0 = min(new_xvals[0] + dt,3/4 * np.pi), max(new_xvals[0] - dt, 0)
        a = np.linspace(1/4 * np.pi ,3/4 * np.pi, 50)
        plot.ax.fill_between(a, new_yvals[0], 0, color = 'g', where = ((a < t1) & (a > t0)))
        plot.canvas.draw()
        
    return update

def excel_data_gen(excel_data):
    counter = 0
    
    def data_gen():
        nonlocal counter
        if counter >= len(excel_data):
            return SENTINEL
        
        _ = excel_data.iloc[counter].values
        counter += 1
        return _
    
    return data_gen
    
def serial_data_gen(ser):
    def data_gen():
        dat1 = ser.read(n_sample*2) # Read ser data from serial
        dat2 = np.frombuffer(dat1, dtype='int16', offset=0) # Convert to int16
        s = np.array(dat2[0:n_sample]) # Make np array
    
        return s
    
    return data_gen

def show_help():
    print("""-h or --help : Show help screen
          -s : use serial data generator. When use this options, serial port must be specified using --port. When this is not used, data from "dataradarspectr_new.xlsx" will be used as data gen. 
          --port : serial port that are used when -s is specified. Usage : --port  [COMx]. Example : --port=COM6  
          """)
    
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(argv[1:], shortopts="sh", longopts=["port=", "help"])
    except getopt.GetoptError as err:
        print(err)
        print("Error : Invalid Argument")
        show_help()
        exit(1)
        
    for opt, arg in opts:
        if opt == "-h":
            show_help()
            exit(0)
            
        if opt == "-s":
            USE_SERIAL = True
        
        if opt == "--port":
            SERIAL_PORT = arg
    
    if USE_SERIAL and SERIAL_PORT == None:
        print("Please specify serial port when running this with -s enabled")
        exit(1)
        
    app = QApplication([])
    plot = MainWindow()
    timer = QtCore.QTimer()
    
    

    if USE_SERIAL:
        import serial
        print("Using serial in port {}".format(SERIAL_PORT))
        ser = serial.Serial(port=SERIAL_PORT, baudrate=20000000, timeout=1)
        data_gen = serial_data_gen(ser) # serial interface
    
    else:
        print("Using data from excel")
        raw_data = readExcelData('dataradarspectr_new.xlsx')
        raw_data = convertDatatoDf(raw_data)
        data_gen = excel_data_gen(raw_data)   

    raw_source = data_updater(data_gen=data_gen)
    
    t = 1 if USE_SERIAL else 1000
    
    try:
        while True:
            if USE_SERIAL:
                ser.flushInput()
                ser.flushOutput()
                 
            timer.timeout.connect(get_updater(plot, raw_source))
            timer.start(t)
            
            app.instance().exec()
    except KeyboardInterrupt:
            app.quit() 
            sys.exit()