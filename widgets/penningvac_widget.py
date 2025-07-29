from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QFormLayout, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from devices.penningvac_controller import PenningvacController
from widgets.base_polling_thread import BasePollingThread
import serial.tools.list_ports
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PenningVacWidget(QGroupBox):
    def __init__(self, controller: PenningvacController, parent=None, polling_interval=10.0):
        super().__init__("PenningVac", parent)
        self.controller = None
        self.polling_thread = None
        self.polling_interval = polling_interval

        # UI elements
        self.scan_port_btn = QPushButton("Scan COM Port")
        self.scan_port_btn.clicked.connect(self.scan_com_port)
        self.ports_combo = QComboBox()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)
        self.pressure_label = QLabel("---")
        self.pressure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unit_label = QLabel("[-]")

        
        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.scan_port_btn)
        layout.addWidget(self.ports_combo)
        layout.addWidget(self.connect_btn)

        display_form = QFormLayout()
        display_form.addRow("Pressure:", self.pressure_label, self.unit_label)
        layout.addLayout(display_form)

        self.setLayout(layout)

    
    def scan_com_port(self):
        self.ports_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ports_combo.addItem(f"{port.description}", port.device)
    

    def toggle_connect(self):
        if self.controller is None:
            # connect
            port = self.ports_combo.currentData()
            if port is None:
                QMessageBox.warning(self, "Error", "No COM port selected.")
                return
            try:
                self.controller = PenningvacController()
                self.controller.connect(port)
                self.connect_btn.setText("Disconnect")
                self.polling_thread = PressurePollingThread(self.controller, interval=self.polling_interval)
                self.polling_thread.updated.connect(self.update_pressure)
                self.polling_thread.start()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create controller: {e}")
                return
        else:
            # disconnect
            self.controller.disconnect()
            self.controller = None
            self.connect_btn.setText("Connect")
            if self.polling_thread is not None:
                self.polling_thread.stop()
                self.polling_thread = None
            self.pressure_label.setText("---")
            self.unit_label.setText("[-]")
    

    def update_pressure(self):
        if self.controller is not None and self.controller.is_connected:
            try:
                pressure, unit = self.controller.pressure
                self.pressure_label.setText(f"{pressure:.2e}")
                self.unit_label.setText(unit)
            except Exception as e:
                logging.error(f"Failed to update pressure: {e}")
                QMessageBox.critical(self, "Error", f"Failed to update pressure: {e}")
        else:
            self.pressure_label.setText("---")
            self.unit_label.setText("[-]")
    

class PressurePollingThread(BasePollingThread):
    updated = pyqtSignal(tuple[float, str])
    
    def get_data(self) -> tuple[float, str]:
        pressure, unit = self.controller.get_data()
        return pressure, unit

    def emit_data(self, data: tuple[float, str]) -> None:
        return super().emit_data(data)
