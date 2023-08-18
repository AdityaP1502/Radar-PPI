# importing libraries
from PyQt6.QtWidgets import *
from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pyqtgraph as pg
import sys
from getspectrum import readExcelData, convertDatatoDf
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from collections import Counter
from scipy import signal
import random
#######################################################################

nSample = 1024


colors = [[1,1,1,0],[1,1,1,0.5],[0.8,0.8,0.8,1]]
cmap = LinearSegmentedColormap.from_list("", colors)

class MainWindow(QMainWindow):
    def __init__(self):
        global cmap
        super().__init__()
        #self.setWindowTitle("PPI")
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        layout = QHBoxLayout(self.main_widget)

        # Create the Matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6), facecolor='k', tight_layout=True)
        self.figurex = Figure(figsize=(8, 6), facecolor='k', tight_layout=True)
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
        self.ax.set_xlim([0.0,np.pi]) # peak of angle to show
        self.ax.set_ylim([0.0,10]) # peak of distances to show
        self.ax.set_rticks([0, 1, 2, 4, 8]) # show 5 different distances
        self.ax.tick_params(axis='both',colors='w')
        self.ax.grid(color='w',alpha=0.5) # grid color
        self.ax.text(0.5, -0.01, "Jarak: 0", size=12, ha='center', c='w', transform=self.ax.transAxes)
        self.x1_vals = []
        self.y1_vals = []
        self.intensity = []
        self.scatter = self.ax.scatter(self.x1_vals, self.y1_vals, cmap=cmap, c=[], vmin=0, vmax=1)
        self.canvas.draw()
        
        # Set up for ax2
        self.ax2 = self.figurex.add_subplot(211, facecolor='#000000')
        self.ax2.set_title('Spectrum', c='w')
        self.ax2.tick_params(axis='both',colors='w')
        self.ax2.spines['bottom'].set_color('w')
        self.ax2.spines['left'].set_color('w')
        self.canvas.draw()
        
        self.ax3 = self.figurex.add_subplot(212, facecolor='#000000')
        self.ax3.set_title('Raw Data', c='w')
        self.ax3.tick_params(axis='both',colors='w')
        self.ax3.spines['bottom'].set_color('w')
        self.ax3.spines['left'].set_color('w')
        
        plt.tight_layout()
        self.canvas.draw()
        self.canvasx.draw()
        
        self.show()
        
    def update_dot(self, peak):
        
        self.ax.clear()
        # self.ax.set_position([-0.05,-0.05,1.1,1.05])
        self.ax.set_xlim([0.0,np.pi])
        self.ax.set_ylim([0.0,10]) # peak of distances to show
        self.ax.set_rticks([0, 1, 2, 4, 8]) # show 5 different distances
        self.ax.tick_params(axis='both',colors='w')
        self.ax.grid(color='w',alpha=0.5) # grid color
        
        random_theta = random.uniform(0, np.pi)
        
        new_xvals = [random_theta]
        new_yvals = [peak]
        
        self.x1_vals.extend(new_xvals)
        self.y1_vals.extend(new_yvals)

        # Put new values in your self
        self.scatter.set_offsets(np.c_[self.x1_vals,self.y1_vals])

        #calculate new color values
        self.intensity = np.concatenate((np.array(self.intensity)*0.15, np.ones(len(new_xvals))))
        self.scatter.set_array(self.intensity)
        
        # random_theta = np.pi/2
        # self.radius = 0
        # Plot the polar data
        
        # intensity = np.concatenate((np.array(intensity)*0.96, np.ones(1)))
        # self.scatter.set_array(intensity)
        
        self.ax.text(0.5, -0.01, f"Jarak: {peak} m", size=12, ha='center', c='w', transform=self.ax.transAxes)
        self.canvas.draw()
    
    def update_rawdata(self, data):
        self.ax2.clear()
        self.ax2.set_title('Raw Data', c='w')
        self.ax2.plot(data, c='y')
        # self.ax2.set_xlim([0, 500])
        self.canvasx.draw()
    
    def update_spectrum(self, data):
        self.ax3.clear()
        self.ax3.set_title('Spektrum', c='w')
        self.ax3.plot(data, c='y')
        self.canvasx.draw()
        
if __name__ == '__main__':
    app = QApplication([])
    plot = MainWindow()
    raw_data = readExcelData('dataradarspectr_new.xlsx')
    raw_data = convertDatatoDf(raw_data)
    done = []
    temp_spect = []
    
    timer = QtCore.QTimer()
    
    def getPeak(array: list[int], height=0):
        # peaks, _ = signal.find_peaks(array, height=height)
        peak = np.argmax(array[:100])
        return peak

    def most_common_peak(array):
        # Count the occurrences of each element in the array
        count = Counter(array)
        
        # Find the most common element and its count
        most_common = count.most_common(1)
        
        return most_common[0][0] if most_common else None
    
    def update():
        global temp_spect
        
        if len(done) < raw_data.shape[0]:
            row_data = raw_data.iloc[len(done)].values
            done.append(row_data)
            
            s = row_data
            nSampleX = s[nSample-2]
            fs = s[nSample-3]
            prf = s[nSample-4]
            
            s[nSampleX:nSample] = 0
            s = s - np.sum(s)/nSampleX
            s[nSampleX:nSample] = 0
            s = s*np.hamming(nSample)
            
            raw = s
            plot.update_rawdata(raw)
            spectrum = 20*np.log10(abs(np.fft.rfft(s))/(nSampleX) + 0.001) #bikin ke skala logaritma
            spectrum = spectrum*spectrum/15 #meningkatkan kontras
            
            temp_spect.append(spectrum[:100])
            plot.update_spectrum(spectrum[:100])
            # peak = getPeak(spectrum[:100])
            # plot.update_dot(peak)
            
            process()
                
    def process():
        global temp_spect
        peaks = []
        if len(temp_spect) == 5:
            for i in range(5):
                peak = getPeak(temp_spect[i])
                peaks.append(peak)
            cpeak = most_common_peak(peaks)
            plot.update_dot(cpeak)
        elif len(temp_spect) > 5: 
            temp_spect = []
                     
    try:
        timer.timeout.connect(update)
        timer.start(1000)
        
        app.instance().exec()
    except KeyboardInterrupt:
        app.quit() 
        sys.exit()

