import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fftshift, fft2

def readExcelData(excel: str, nSample=1024):
    """
    menerima masukan berupa nama file dan keluaran berupa 
    numpy array 2D
    
    """
    file = pd.read_excel(excel, index_col=0) #get raw data
    df = pd.DataFrame(file) #get dataframe
    data = np.array(df[0:nSample]) #jadiin array
    
    return data

def convertDatatoDf(array: list[int]):
    """
    menerima masukan berupa numpy array 2D
    dan keluaran berupa dataframe
    
    """
    df = pd.DataFrame(array)
    df.index = [f'Nilai ke-{i+1}' for i in range(len(df))]
    
    return df 

def convertDatatoExcel(array: list[int], excel: str):
    """
    menerima masukan berupa numpy array 2D dan judul excel
    dan keluaran berupa file excel
    """
    df = convertDatatoDf(array)
    df.to_excel(f'{excel}.xlsx')
    
def fastFourierTransform(array: list[int]):
    """
    menerima masukan berupa list array dan keluaran berupa 
    hasil fft, magnituda dan fasa
    
    """
    s_fft = np.fft.rfft(array)
    s_mag = np.abs(s_fft)  # magnitude spectrum
    s_phase = np.angle(s_fft, deg=True) #phase spectrum
    
    return s_fft, s_mag, s_phase

def rangeDopplerMatrix(array: list[int], nSample=1024, nSampleX=400):
    array = signal.detrend(array) #kurangi sama nilai rata-rata
    array[nSampleX:nSample] = 0 #set remaining values to zero
    array = array*np.hanning(nSample) #windowing using hanning
    range_doppler_matrix = fftshift(fft2(array))
    
    return range_doppler_matrix

def powerSpectralDensity(array: list[int], nSample=1024, nSampleX=400):
    """
    menerima masukan berupa list array dan keluaran berupa 
    Power Spectral Density (PSD) terhadap mean
    
    """
    array = signal.detrend(array) #kurangi sama nilai rata-rata
    array[nSampleX:nSample] = 0 #set remaining values to zero
    array = array*np.hanning(nSample) #windowing using hanning
    s_fft, s_mag, s_phase = fastFourierTransform(array) #fft
    sdB = 20*np.log10(s_mag/(nSampleX) + 0.001) #bikin ke skala logaritma
    sdB = sdB*sdB/15 #meningkatkan kontras
    
    return sdB

"""
if __name__ == '__main__':
    data = readExcelData('dataradar_new.xlsx')
    #psd = powerSpectralDensity(data)
    #df = convertDatatoExcel(psd)
"""