from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QFormLayout, QMessageBox, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from devices.ophir_juno_controller import OphirJunoController
from pywintypes import com_error
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class OphirPowerMeterWidget(QGroupBox):

    def __init__(self, parent=None):
        super().__init__("Ophir Power Meter Control", parent)

        self.controller = None
        self.last_power = None  # keep latest value here to communicate with data class for saving

        # UI Elements
        self.scan_usb_btn = QPushButton("Scan USB")
        self.scan_usb_btn.clicked.connect(self.scan_usb)
        self.device_select_combo = QComboBox()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.device_info_label = QLabel("---")
        self.sensor_info_label = QLabel("---")


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

        info_form = QFormLayout()
        info_form.addRow("Device Info:", self.device_info_label)
        info_form.addRow("Senro Info:", self.sensor_info_label)
        layout.addLayout(info_form)

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
        try:
            self.controller = OphirJunoController()
            self.device_select_combo.addItems(self.controller.device_list)
        except com_error as e:
            logging.error(f"Failed to scan USB devices: {e}")

    

    def clear_info(self):
        self.device_info_label.setText("---")
        self.sensor_info_label.setText("---")
        self.range_select_combo.blockSignals(True)
        self.range_select_combo.clear()
        self.range_select_combo.blockSignals(False)
        self.wavelength_select_combo.blockSignals(True)
        self.wavelength_select_combo.clear()
        self.wavelength_select_combo.blockSignals(True)


    def toggle_connection(self):
        if not self.controller.connected:
            selected_device_serial = self.device_select_combo.currentText()
            if selected_device_serial == "":
                QMessageBox.warning(self, "Device Not Found", "No USB device is selected.")
                return
            self.controller.connect(selected_device_serial) # also start stream
            if self.controller.connected:
                self.device_info_label.setText(" - ".join(self.controller.device_info))
                if self.controller.is_sensor_exist:
                    self.sensor_info_label.setText(" - ".join(self.controller.sensor_info))
                    self.range_select_combo.addItems(self.controller.available_ranges)
                    self.wavelength_select_combo.addItems(self.controller.available_wavelengths)
                    self.range_select_combo.setCurrentIndex(0)
                    self.wavelength_select_combo.setCurrentIndex(0)

                self.connect_btn.setText("Disconnect")
                self.polling_thread = PowerMeterPollingThread(self.controller, interval=0.5)
                self.polling_thread.updated.connect(self.update_value_display)
                self.polling_thread.start()
        else: # controller connected
            self.polling_thread.stop()
            self.polling_thread = None
            self.controller.disconnect()
            self.connect_btn.setText("Connect")
            self.clear_info()
    

    def update_value_display(self, new_value): # check type of new_value!
        try:
            self.last_power = float(new_value)
            self.power_label.setText(f"{self.last_power:.2f}")
        except (TypeError, Exception) as e:
            logging.error(f"Failed to update value display: {e}")


    def change_range(self):
        new_index = self.range_select_combo.currentIndex()
        self.controller.range = new_index


    def change_wavelength(self):
        new_index = self.wavelength_select_combo.currentIndex()
        self.controller.wavelength = new_index


class PowerMeterPollingThread(QThread):

    updated = pyqtSignal(float)

    def __init__(self, controller, interval=0.5, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.interval = interval
        self._running = True

    
    def run(self):
        while self._running:
            try:
                if self.controller.connected:
                    data = self.controller.get_data() # return list
                    """
                    data looks like
                    [{'value': 0.0, 'timestamp': 520181089.0, 'status': 0}, {'value': 0.0, 'timestamp': 520181156.0, 'status': 0}, ...]
                    """
                    if data: # if list is not empty
                        newest_power = data[-1]["value"]
                        self.updated.emit(newest_power)
            except Exception as e:
                logging.error(f"Polling power meter data failed: {e}")
            time.sleep(self.interval)


    def stop(self):
        self._running = False
        self.wait()


    