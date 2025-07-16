from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QDoubleSpinBox, QMessageBox, QLineEdit, QFormLayout
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class OceanSpectrometerWidget(GroupBox):

    def __init__(self, parent=None):
        super().__init__("Ocean Optics Spectrometer Control", parent)

        self.spectrometer = Spectrometer()