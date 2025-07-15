from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QFormLayout, QMessageBox, QLineEdit, QComboBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from devices.ophir_juno_controller import OphirJunoController
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class OphirPowerMeterWidget(QGroupBox):

    def __init__(self, parent=None):
        super().__init__("Ophir Power Meter Control", parent)

        # UI Elements
        self.scan_usb_btn = QPushButton("Scan USB")
        self.scan_usb_btn.clicked.connect(self.scan_usb)
        self.device_select_combo = QComboBox()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.range_select_combo = QComboBox()
        self.range_select_combo.currentIndexChanged.connect(self.change_range)

        self.wavelength_select_combo = QComboBox()
        self.wavelength_select_combo.currentIndexChanged.connect(self.change_wavelength)


        self.power_label = QLabel("0.00")
        self.power_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        unit_label = QLabel("W")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = QFont()
        font.setPointSize(48)
        font.setBold(True)
        self.power_label.setFont(font)
        self.power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_label.setFont(font)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # layout
        layout = QVBoxLayout()

        scan_usb_form = QFormLayout()
        scan_usb_form.addRow(self.scan_usb_btn)
        scan_usb_form.addRow("Device Selection:", self.device_select_combo)
        scan_usb_form.addRow(self.connect_btn)
        layout.addLayout(scan_usb_form)

        setting_form = QFormLayout()
        setting_form.addRow("Range Selection:", self.range_select_combo)
        setting_form.addRow("Wavelength Selection:", self.wavelength_select_combo)
        layout.addLayout(setting_form)

        power_hbox = QHBoxLayout()
        power_hbox.addWidget(self.power_label)
        power_hbox.addWidget(unit_label)
        layout.addLayout(power_hbox)

        self.setLayout(layout)
    

    def scan_usb(self):
        """
        get usb devices and update combo box
        """
        pass


    def toggle_connection(self):
        pass


    def change_range(self):
        pass


    def change_wavelength(self):
        pass

    
