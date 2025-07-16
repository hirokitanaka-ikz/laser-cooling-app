import numpy as np
from scipy.signal import find_peaks
import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer

WAVELENGTH_MIN = 900
WAVELENGTH_MAX = 1100


class OceanSpectrometerController():

    def __init__(self) -> None:
        self._wavelengths = []
        self._intensity = []
        self._background = []
        self._is_connected = False
        self._exposure_time = 100 # ms
        self._wavelength_min = WAVELENGTH_MIN
        self._wavelength_max = WAVELENGTH_MAX
        # self.isRecording = False
    

    def connect(self):
        try:
            self.spectrometer = Spectrometer.from_first_available()
        except AttributeError:
            return False
        except seabreeze.cseabreeze._wrapper.SeaBreezeError:
            return False
        self.spectrometer.integration_time_micros(self.exposure_time)
        self.background = self.spectrometer.intensities()
        self.isConnected = True
        print('Ocean Optics spectrometer connected')
        return True
    

    def get_serial_number(self):
        return self.spectrometer.serial_number
    

    def get_model(self):
        return self.spectrometer.model
    

    def start_recording(self):
        self.isRecording = True
        print("Ocean Optics spectrometer start recording")
    

    def stop_recording(self):
        self.isRecording = False
        print("Ocean Optics spectrometer stop recording")

    
    def is_connected(self):
        return self.isConnected
    

    def is_recording(self):
        return self.isRecording


    def set_exposure_time(self, microsec):
        self.exposure_time = microsec
        self.spectrometer.integration_time_micros(self.exposure_time)
    

    def set_wavelength_min(self, wl_min):
        self.wavelength_min = wl_min
    

    def set_wavelength_max(self, wl_max):
        self.wavelength_max = wl_max


    def get_exposure_time(self):
        return self.exposure_time
    

    def get_wavelength_min(self):
        return self.wavelength_min
    

    def get_wavelength_max(self):
        return self.wavelength_max


    def get_peak_wavelength(self):
        peaks, _ = find_peaks(self.intensity, height=100)
        if len(peaks) != 0:
            peakWavelength = self.wavelengths[np.where(self.intensity == max(self.intensity[peaks]))][0]
        else:
            peakWavelength = 0
        return peakWavelength
    

    def get_spectrum(self):
        self.wavelengths = self.spectrometer.wavelengths()
        self.intensity = self.spectrometer.intensities() - self.background
        # self.intensities = self.intensities / max(self.intensities)
        return self.wavelengths, self.intensity
    

    def take_new_background(self):
        self.background = self.spectrometer.intensities()