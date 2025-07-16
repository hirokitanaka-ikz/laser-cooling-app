from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QSpinBox, QMessageBox, QLineEdit, QFormLayout
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import numpy as np
import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class OceanSpectrometerWidget(QGroupBox):

    def __init__(self, parent=None):
        super().__init__("Ocean Optics Spectrometer Control", parent)

        self.spectrometer = None
        self.polling_thread = None
        self.wavelength = np.array([])
        self.intensity = np.array([])
        self.dark = np.array([])

        # UI Elements
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)

        self.model_type_label = QLabel("---")
        self.serial_number_label = QLabel("---")

        self.integration_time_spin = QSpinBox()
        self.integration_time_spin.setSuffix(" us")
        self.integration_time_spin.setSingleStep(10)
        self.integration_time_spin.valueChanged.connect(self.set_integration_time)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start)

        self.dark_btn = QPushButton("Capture Dark")
        self.dark_btn.clicked.connect(self.capture_dark)

        # layout
        layout = QVBoxLayout()

        layout.addWidget(self.connect_btn)

        info_form = QFormLayout()
        info_form.addRow("Model Type:", self.model_type_label)
        info_form.addRow("Serial Number:", self.serial_number_label)
        layout.addLayout(info_form)

        parameter_from = QFormLayout()
        parameter_from.addRow("Integration Time:", self.integration_time_spin)
        layout.addLayout(parameter_from)

        layout.addWidget(self.start_btn)

        self.setLayout(layout)


    def toggle_connect(self):
        if self.spectrometer is None:
            try:
                self.spectrometer = Spectrometer()
                self.spectrometer.from_first_available()
                self.model_type_label.setText(self.spectrometer.model)
                self.serial_number_label.setText(self.spectrometer.serial_number)
                self.integration_time_spin.setRange(self.spectrometer.integration_time_micros_limits)
                self.connect_btn.setText("Disconnect")
                self.wavelength = self.spectrometer.wavelengths()
                self.intensity = np.zeros_like(self.wavelength)
                self.dark = np.zeros_like(self.wavelength)
                logging.info("Spectrometer connected")
            except (TimeoutError, RuntimeError, OSError) as e:
                logging.error(f"Failed to connect spectrometer: {e}")
                return
        else:
            if not self.polling_thread is None:
                self.polling_thread.stop()
                self.polling_thread = None
            self.spectrometer = None
            self.model_type_label.setText("---")
            self.serial_number_label.setText("---")
            self.connect_btn.setText("Connect")
            logging.info("Spectrometer disconnected")
    

    def __del__(self):
        self.disconnect()
    

    def set_integration_time(self, new_value:int):
        self.spectrometer.integration_time_micros = new_value
        logging.info(f"Integration Time changed to {new_value} us")
    

    def capture_dark(self):
        self.dark = self.intensity
    

    def start(self):
        if self.polling_thread is None:
            self.polling_thread = SpectrometerPollingThread(self.spectrometer, interval=0.5)
            self.polling_thread.updated.connect(self.update_spectrum)
            self.polling_thread.start()
            self.start_btn.setText("Stop")
        else:
            self.polling_thread.stop()
            self.polling_thread = None
            self.start_btn.setText("Start")
    

    def update_spectrum(self, intensity_array):
        self.intensity = intensity_array



class SpectrometerPollingThread(QThread):
    
    updated = pyqtSignal(dict)

    def __init__(self, spectrometer, interval=0.5, parent=None):
        super().__init__(parent)
        self.spectrometer = spectrometer
        self.interval = interval
        self._running = True

    
    def run(self):
        while self._running:
            try:
                intensity_array = self.spectrometer.intensities()
                self.updated.emit(intensity_array)
            except Exception as e:
                logging.error(f"Polling spectrum failed: {e}")
            time.sleep(self.interval)


    def stop(self):
        self._running = False
        self.wait()