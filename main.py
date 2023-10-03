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
from matplotlib.mlab import specgram, window_hanning
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import LogNorm

from getspectrum import readExcelData, convertDatatoDf


# Fade Effects Parameter
colors = [[1,1,1,0],[1,1,1,0.5],[0.8,0.8,0.8,1]]
cmap = LinearSegmentedColormap.from_list("", colors)
fade_intensity = 0.15

# Spectogram Parameters
sample_rate = 44100  # Sample rate in Hz
duration = 10  # Duration of audio recording in seconds
fft_size = 1024  # Size of the FFT (Fast Fourier Transform)
hop_size = 256   # Hop size between consecutive FFT frames
SAMPLES_PER_FRAME = 10

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
        self.figurey = Figure(figsize=(8, 6), facecolor='w', tight_layout=True)
        
        self.canvas = FigureCanvas(self.figure)
        self.canvasx = FigureCanvas(self.figurex)
        self.canvasy = FigureCanvas(self.figurey)
        
        layout.addWidget(self.canvas)
        layout.addWidget(self.canvasx)
        layout.addWidget(self.canvasy)
        
        # Initiate Variables
        # self.radius = 0
        # self.angles = np.linspace(0, np.pi, 100)
        
        # Set up for ax
        self.ax_ppi = self.figure.add_subplot(111, projection='polar', facecolor='#000000')
        self.ax_ppi.set_xlim([1/4 * np.pi ,3/4 * np.pi]) # peak of angle to show
        self.ax_ppi.set_ylim([0.0,90]) # peak of distances to show
        self.ax_ppi.set_rticks([0, 20, 30, 50, 90]) # show 5 different distances
        self.ax_ppi.tick_params(axis='both',colors='g')
        self.ax_ppi.grid(color='w',alpha=0.5) # grid color
        self._ppi_dists = [0 for i in range(5)]
        self._ppi_dist_pointer = 0
        
        self.ax_spectogram = self.figurey.add_subplot(111, facecolor='#FFFFFF')
        self.im_spec = None
        self.spectogram_frame_counter = 0
        
        self.ax_time_data = self.figurex.add_subplot(211, facecolor='#000000')
        self.ax_spectrum_data = self.figurex.add_subplot(212, facecolor='#000000')
        
        # self.scatter = self.ax.scatter(self.x1_vals, self.y1_vals, cmap=cmap, c=[], vmin=0, vmax=1)
        
        self.canvas.draw()
        self.canvasx.draw()
        
        self.show()

def spectrum_to_jarak(max_index):
    return max_index * 0.0576 + 0.7288

def most_common_dist(array):
    # Count the occurrences of each element in the array
    count = Counter(array)
    
    # Find the most common element and its count
    most_common = count.most_common(1)
    
    return most_common[0][0] if most_common else None   

def get_spectrum(time_data):
    n_sample_x = time_data[n_sample - 2]
    time_data[n_sample_x:n_sample] = 0
    time_data = time_data - (np.sum(time_data) / n_sample_x)
    time_data[n_sample_x:n_sample] = 0

    time_data = time_data * np.hamming(n_sample)

    data_f = 20 * np.log10(abs(np.fft.rfft(time_data)) / (n_sample_x) + 0.001)
    data_f = data_f * data_f / 15  
    
    return data_f

def spectrum_analyzer(spectrum):
    return spectrum_to_jarak(np.argmax(spectrum))
 
def update_spectrogram(data, plot):
    """
        https://github.com/ayared/Live-Specgram
    """
    
    # Compute the spectrogram
    arr2D, freqs, bins = specgram(data, window=window_hanning, NFFT=fft_size, Fs=sample_rate, noverlap=hop_size)
    
    if plot.im_spec == None:
        # extent = (bins[0],bins[-1]*SAMPLES_PER_FRAME,freqs[-1],freqs[0])
        plot.im_spec = plot.ax_spectogram.imshow(arr2D,aspect='auto',interpolation="none",
                    norm = LogNorm(vmin=.01,vmax=1))
        return
    
    im_data = plot.im_spec.get_array()

    if plot.spectogram_frame_counter < SAMPLES_PER_FRAME:
        im_data = np.hstack((im_data,arr2D))
        plot.im_spec.set_array(im_data)
    else:
        keep_block = arr2D.shape[1]*(SAMPLES_PER_FRAME - 1)
        im_data = np.delete(im_data,np.s_[:-keep_block],1)
        im_data = np.hstack((im_data,arr2D))
        plot.im_spec.set_array(im_data)
        
    plot.canvasy.draw()
    plot.spectogram_frame_counter += 1

def update_time_data(data, plot):
    plot.ax_time_data.cla()
    plot.ax_time_data.plot(data)
    plot.canvasx.draw()

def update_spectrum(data, plot):
    plot.ax_spectrum_data.cla()
    plot.ax_spectrum_data.plot(data)
    plot.canvasx.draw()

def update_ppi(plot, new_xvals, new_yvals):
    plot.ax_ppi.clear()
    plot.ax_ppi.set_xlim([1/4 * np.pi ,3/4 * np.pi]) # peak of angle to show
    plot.ax_ppi.set_ylim([0.0,90]) # peak of distances to show
    plot.ax_ppi.set_rticks([0, 20, 30, 50, 90]) # show 5 different distances
    
    plot.annot = plot.ax_ppi.annotate("{:.2f} m".format(new_yvals[0]), (new_xvals[0], new_yvals[0]), c="w")
    
    dt = 1/18 * np.pi
    t1, t0 = min(new_xvals[0] + dt,3/4 * np.pi), max(new_xvals[0] - dt, 0)
    a = np.linspace(1/4 * np.pi ,3/4 * np.pi, 50)
    plot.ax_ppi.fill_between(a, new_yvals[0], 0, color = 'g', where = ((a < t1) & (a > t0)))
    plot.canvas.draw()
        
def get_updater(plot, data_gen):
    global fade_intensity
    def update():
        # Get intermediate points
        # new_xvals, new_yvals, raw_data, n = get_new_vals()
        raw_data = data_gen()
       
        if len(raw_data) == 0:
            print("Done!")
            sys.exit(0)
        
        update_spectrogram(raw_data, plot)
        update_time_data(raw_data[:raw_data[n_sample - 2]], plot)
        
        spectrum = get_spectrum(raw_data)
        
        update_spectrum(spectrum, plot)
        
        dist = spectrum_analyzer(spectrum=spectrum)
        
        plot._ppi_dists[plot._ppi_dist_pointer] = dist
        plot._ppi_dist_pointer += 1
    
        if plot._ppi_dist_pointer < 5:
            return 
        
        common_dist = most_common_dist(plot._ppi_dists)
        plot._ppi_dist_pointer = 0
        new_xvals, new_yvals = [random.uniform(1/4 * np.pi, 5/4 * np.pi)], [common_dist]
            
        update_ppi(plot, new_xvals, new_yvals)
        
        
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
        from serial import Serial
        print("Using serial in port {}".format(SERIAL_PORT))
        ser = Serial(port=SERIAL_PORT, baudrate=20000000, timeout=1)
        data_gen = serial_data_gen(ser) # serial interface
    
    else:
        print("Serial mode is disabled. Using data from excel.\nIf you want to use serial, please use -h or --help for more details")
        raw_data = readExcelData('dataradarspectr_new.xlsx')
        raw_data = convertDatatoDf(raw_data)
        data_gen = excel_data_gen(raw_data)   
    
    t = 1 if USE_SERIAL else 1000
    
    try:
        while True:
            if USE_SERIAL:
                ser.flushInput()
                ser.flushOutput()
                 
            timer.timeout.connect(get_updater(plot, data_gen))
            timer.start(t)
            
            app.instance().exec()
    except KeyboardInterrupt:
            app.quit() 
            sys.exit()