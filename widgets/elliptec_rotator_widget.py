from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout,
    QComboBox, QDoubleSpinBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import elliptec
from widgets.base_polling_thread import BasePollingThread
import serial.tools.list_ports
import logging
from typing import Optional
import time
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ElliptecRotatorWidget(QGroupBox):
    """
    Control Widget for Thorlabs Elliptec Rotator ELL14;
    use elliptec library https://github.com/roesel/elliptec
    """

    def __init__(self, parent=None, polling_interval=0.5):
        super().__init__("Elliptec Rotator Control", parent)
        self.controller = None
        self.rotator = None
        self.polling_thread = None
        self.timer = None
        self.angle_list = None
        self.angle_index = None
        self._polling_interval = polling_interval

        # UI Elements
        self.scan_port_btn = QPushButton("Scan COM Port")
        self.scan_port_btn.clicked.connect(self.scan_com_port)
        self.ports_combo = QComboBox()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)

        self.home_btn = QPushButton("Homing")
        self.home_btn.setEnabled(False)
        self.home_btn.clicked.connect(self.home)
        
        # manual move UIs
        self.target_angle_spin = QDoubleSpinBox()
        self.target_angle_spin.setSuffix("°")
        self.target_angle_spin.setSingleStep(0.1)
        self.target_angle_spin.setDecimals(2)
        self.target_angle_spin.setRange(0.0, 360.0) # not sure if this is correct
        self.target_angle_spin.setEnabled(False)
        self.target_angle_spin.editingFinished.connect(self.go_to_target) # too much communication with valueChanged. editingFinished signal doesn't emit a value!
        self.angle_label = QLabel("---")
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        self.angle_label.setFont(font)

        # automatic move UIs
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self.toggle_auto_move)
        self.run_btn.setEnabled(False)
        self.start_angle_spin = QDoubleSpinBox()
        self.start_angle_spin.setSuffix("°")
        self.start_angle_spin.setRange(0.0, 360.0)
        self.start_angle_spin.setDecimals(1)
        self.start_angle_spin.setEnabled(False)
        self.stop_angle_spin = QDoubleSpinBox()
        self.stop_angle_spin.setSuffix("°")
        self.stop_angle_spin.setRange(0.0, 360.0)
        self.stop_angle_spin.setDecimals(1)
        self.stop_angle_spin.setEnabled(False)
        self.step_angle_spin = QDoubleSpinBox()
        self.step_angle_spin.setSuffix("°")
        self.step_angle_spin.setRange(0.01, 90.0)
        self.step_angle_spin.setDecimals(1)
        self.step_angle_spin.setValue(0.5)
        self.step_angle_spin.setEnabled(False)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setSuffix("min")
        self.interval_spin.setRange(0.1, 120.0)
        self.interval_spin.setDecimals(1)
        self.interval_spin.setEnabled(False)

        #layout
        layout = QVBoxLayout()
        layout.addWidget(self.scan_port_btn)
        layout.addWidget(self.ports_combo)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.home_btn)

        manual_form = QFormLayout()
        manual_form.addRow(self.target_angle_spin)
        manual_form.addRow("Angle:", self.angle_label)
        layout.addLayout(manual_form)

        auto_form = QFormLayout()
        auto_form.addRow("Auto Move", self.run_btn)
        auto_form.addRow("Start Angle:", self.start_angle_spin)
        auto_form.addRow("Stop Angle:", self.stop_angle_spin)
        auto_form.addRow("Step Angle:", self.step_angle_spin)
        auto_form.addRow("Interval:", self.interval_spin)
        layout.addLayout(auto_form)

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
            if port == "":
                QMessageBox.warning(self, "Device Not Found", "No COM port is selected.")
                return
            try:
                self.controller = elliptec.Controller(port, debug=False)
            except Exception as e:
                logging.error(f"Failed to connect to Elliptec controller device: {e}")
                return
            try:
                self.rotator = elliptec.Rotator(self.controller, debug=False)
            except Exception as e:
                self.controller = None
                logging.error(f"Failed to connect Elliptec rotator: {e}")
                return
            logging.info("Elliptec device connected")
            self.connect_btn.setText("Disconnect")
            self.enable_control_uis(enable=True)
            self.target_angle_spin.setValue(self.rotator.get_angle())
            self.polling_thread = RotatorPollingThread(self.rotator, interval=self._polling_interval)
            self.polling_thread.updated.connect(self.update_angle_display) # emit polling_thread.status_updated -> execute self.update_status_display
            self.polling_thread.start()
        else:
            # disconnect
            if not self.polling_thread is None:
                try:
                    self.polling_thread.stop()
                except Exception as e:
                    logging.error(f"Failed to stop polling: {e}")
            self.polling_thread = None
            self.rotator = None
            self.controller = None
            logging.info("Elliptec device disconnected")
            self.connect_btn.setText("Connect")
            self.enable_control_uis(enable=False)
    

    def toggle_auto_move(self):
        if self.timer is None:
            # read values from UIs
            start_angle = self.start_angle_spin.value()
            stop_angle = self.stop_angle_spin.value()
            step_angle = self.step_angle_spin.value()
            interval = self.interval_spin.value()
            # make a list of angles
            if start_angle < stop_angle:
                self.angle_list = np.arange(start_angle, stop_angle + step_angle, step_angle)
            elif start_angle > stop_angle:
                self.angle_list = np.arange(start_angle, stop_angle - stop_angle, -stop_angle)
            else: # start = stop
                QMessageBox.warning(self, "Invalid Inputs", "start angle = stop angle")
                return
            # create timer
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.move_next_angle)
            self.move_next_angle() # call once to go to start angle
            self.timer.start(int(interval * 60 * 1000)) # min to ms
            # disable spinboxes and rename toggle button
            self.run_btn.setText("Stop")
            self.start_angle_spin.setEnabled(False)
            self.stop_angle_spin.setEnabled(False)
            self.step_angle_spin.setEnabled(False)
            self.interval_spin.setEnabled(False)
            self.target_angle_spin.setEnabled(False)
        else:
            # stop timer, clear timer and angle list
            self.timer.stop()
            self.timer = None
            self.angle_list = None
            self.angle_index = None


    def move_next_angle(self):
        if self.angle_index is None:
            self.angle_index = 0
        if self.angle_index < len(self.angle_list):
            self.go_to(self.angle_list[self.angle_index])
            logging.info(f"Rotator moved to {self.angle_list[self.angle_index]}°")
            self.angle_index += 1
        else:
            self.angle_index = None
            self.rotator_timer.stop()
            self.rotator_timer = None
            self.angle_list = None
            logging.info("Rotator reached stop angle")
            self.run_btn.setText("Run")
            self.start_angle_spin.setEnabled(True)
            self.stop_angle_spin.setEnabled(True)
            self.step_angle_spin.setEnabled(True)
            self.interval_spin.setEnabled(True)
            self.target_angle_spin.setEnabled(True)
    

    def enable_control_uis(self, enable:bool):
        self.home_btn.setEnabled(enable)
        self.target_angle_spin.setEnabled(enable)
        self.ports_combo.setEnabled(not enable)
        self.start_angle_spin.setEnabled(enable)
        self.stop_angle_spin.setEnabled(enable)
        self.step_angle_spin.setEnabled(enable)
        self.interval_spin.setEnabled(enable)


    def home(self):
        if self.rotator is None:
            return
        try:
            self.rotator.home()
            self.target_angle_spin.setValue(self.rotator.get_angle())
        except Exception as e:
            logging.error(f"Failed to move to home: {e}")
    

    def go_to(self, target_angle:float):
        if self.rotator is None:
            return
        try:
            self.rotator.set_angle(target_angle)
        except Exception as e:
            logging.error(f"Failed to move to {target_angle} deg: {e}")
    

    def go_to_target(self):
        if self.rotator is None:
            return
        try:
            target_angle = self.target_angle_spin.value()
            self.rotator.set_angle(target_angle)
        except Exception as e:
            logging.error(f"Failed to move to {target_angle} deg: {e}")
    

    def update_angle_display(self, current_angle:float):
        self.angle_label.setText(f"{current_angle:.2f}°")
    

    @property
    def angle(self) -> Optional[float]:
        try:
            return float(self.angle_label.text())
        except (TypeError, Exception) as e:
            # logging.error(f"Failed to read rotator angle for data export: {e}")
            return None
    

    def __del__(self):
        try:
            self.timer.stop()
        except Exception as e:
            pass


class RotatorPollingThread(BasePollingThread):
    updated = pyqtSignal(float)

    def get_data(self) -> float:
        return self.controller.get_angle()
    

    def emit_data(self, data:float) -> None:
        self.updated.emit(data)
    
    