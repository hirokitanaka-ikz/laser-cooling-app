import numpy as np
from scipy.signal import find_peaks
import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


WAVELENGTH_MIN = 900
WAVELENGTH_MAX = 1100


class OceanSpectrometerController():

    def __init__(self) -> None:
        self._connected = False
        self._serial_number = ""
        self._model_type = ""


    def connect(self):
        try:
            self.spectrometer = Spectrometer.from_first_available()
            logging.info("Spectrometer connected")
            self._connected = True
        except (AttributeError, seabreeze.cseabreeze._wrapper.SeaBreezeError, Exception) as e:
            logging.error(f"Failed to connect to spectrometer: {e}")
            return

        
    def disconnect(self):
        if self._connected:
            self.spectrometer = None



    @property
    def serial_number(self) -> str:
        return self.


    @property
    def integration_time(self):
        pass


    

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