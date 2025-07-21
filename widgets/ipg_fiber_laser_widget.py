from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QDoubleSpinBox, QMessageBox, QLineEdit, QFormLayout
)
from PyQt6.QtCore import QThread, pyqtSignal
from devices.ipg_ylr_laser_controller import IPGYLRLaserController, LaserStatus
from typing import Optional
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


IP = "10.10.10.20"
PORT = "10001"


class LaserControlWidget(QGroupBox):
    
    def __init__(self, parent=None, polling_interval=0.5):
        super().__init__("IPG Fiber Laser Control", parent)

        self.controller = IPGYLRLaserController()
        self.polling_thread = None
        self._polling_interval = polling_interval
        
        # Connection input fields
        self.ip_edit = QLineEdit(IP)
        self.port_edit = QLineEdit(PORT)
        self.port_edit.setMaximumWidth(100)

        # --- UI Elements ---
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.status_label = QLabel("Disconnected")

        self.laser_btn = QPushButton("Turn Laser ON")
        self.laser_btn.clicked.connect(self.toggle_laser)
        self.laser_btn.setEnabled(False)

        self.guide_btn = QPushButton("Turn Guide ON")
        self.guide_btn.clicked.connect(self.toggle_guide)
        self.guide_btn.setEnabled(False)

        self.setpoint_spin = QDoubleSpinBox()
        self.setpoint_spin.setSuffix(" %")
        self.setpoint_spin.setDecimals(2)
        self.setpoint_spin.setRange(0.0, 100.0)
        self.setpoint_spin.setSingleStep(0.5)
        self.setpoint_spin.valueChanged.connect(self.update_setpoint)
        self.setpoint_spin.setEnabled(False)

        self.power_label = QLabel("Output Power: --- W")
        self.temp_label = QLabel("Temp: --- °C")
        self.laser_status_display = QLabel("Laser Status: ---")

        # --- Layout ---
        layout = QVBoxLayout()

        # Connection form layout
        conn_form = QFormLayout()
        conn_form.addRow("IP Address:", self.ip_edit)
        conn_form.addRow("Port:", self.port_edit)
        layout.addLayout(conn_form)

        layout.addWidget(self.connect_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(self.laser_btn)
        layout.addWidget(self.guide_btn)

        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Setpoint:"))
        hlayout.addWidget(self.setpoint_spin)
        layout.addLayout(hlayout)
        layout.addWidget(self.power_label)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.laser_status_display)

        self.setLayout(layout)


    def toggle_connection(self):
        try:
            ip = self.ip_edit.text().strip()
            port = int(self.port_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid IP or Port", "check IP or Port")
            return
        if not self.controller.connected:
            # Attempt to connect
            try:
                self.controller.connect(ip=ip, port=port)
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", f"{e}")
            if self.controller.connected:
                self.connect_btn.setText("Disconnect")
                self.status_label.setText("Connected")
                self.set_controls_enabled(True)
                # self.timer.start()
                # self.update_status()
                self.polling_thread = LaserPollingThread(self.controller, interval=self._polling_interval)
                self.polling_thread.status_updated.connect(self.update_status_display) # emit polling_thread.status_updated -> execute self.update_status_display
                self.polling_thread.start()
                self.ip_edit.setEnabled(False)
                self.port_edit.setEnabled(False)
        else:
            # Disconnect
            # self.timer.stop()
            self.polling_thread.stop()
            self.polling_thread = None
            try:
                self.controller.disconnect()
            except Exception:
                pass
            self.ip_edit.setEnabled(True)
            self.port_edit.setEnabled(True)
            self.connect_btn.setText("Connect")
            self.status_label.setText("Disconnected")
            self.set_controls_enabled(False)
            self.clear_status_display()


    def set_controls_enabled(self, enabled: bool):
        self.laser_btn.setEnabled(enabled)
        self.guide_btn.setEnabled(enabled)
        self.setpoint_spin.setEnabled(enabled)


    def toggle_laser(self):
        if not self.controller:
            return
        if self.controller.status.emission_on:
            self.controller.laser_off()
        else:
            self.controller.laser_on()


    def toggle_guide(self):
        if not self.controller:
            return
        if self.controller.status.guide_laser_on:
            self.controller.guide_off()
        else:
            self.controller.guide_on()


    def update_setpoint(self, value):
        if self.controller:
            try:
                self.controller.setpoint = float(value)
            except (ValueError, TypeError) as e:
                logging.error(f"Set point value is in wrong format: {e}")
    

    def update_status_display(self, new_status: dict):
        """
        this method doesn't manipulate controller to avoid freezing of GUI.
        Instead, this receives status dictionary (new_status) from polling thread and update UIs. 
        """
        try:
            self.setpoint_spin.blockSignals(True)   # avoid triggering valueChanged signal
            self.setpoint_spin.setValue(new_status["setpoint"])
            self.setpoint_spin.blockSignals(False)
            self.power_label.setText(f"Output Power: {new_status['output_power']:.1f} W")
            self.temp_label.setText(f"Temp: {new_status['temperature']:.1f} °C")
            self.laser_btn.setText("Turn Laser OFF" if new_status["laser_on"] else "Turn Laser ON")
            self.guide_btn.setText("Turn Guide OFF" if new_status["guide_on"] else "Turn Guide ON")
            self.laser_status_display.setText("Status:\n\t" + new_status["messages"])
        except (TypeError, Exception) as e:
            self.status_label.setText(f"Error: {e}")


    def clear_status_display(self):
        self.setpoint_spin.blockSignals(True) 
        self.setpoint_spin.setValue(0)
        self.setpoint_spin.blockSignals(False) 
        self.power_label.setText("Output Power: --- W")
        self.temp_label.setText("Temp: --- °C")
        self.laser_status_display.setText("Laser Status: ---")
        self.laser_btn.setText("Turn Laser ON")
        self.guide_btn.setText("Turn Guide ON")

    
    @property
    def laser_power(self) -> Optional[float]:
        try:
            text = self.power_label.text()
            return float(text.split(": ")[1][:-len("W")].strip())
        except (TypeError, Exception) as e:
            return None


class LaserPollingThread(QThread):
    
    status_updated = pyqtSignal(dict) # dict type data is given to LaserControlWidget

    def __init__(self, controller, interval, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.interval = interval
        self._running = True
    

    def run(self):
        while self._running:
            try:
                setpoint = self.controller.setpoint # Optional[float]
                output_power = self.controller.output_power # Optional[float]
                temperature = self.controller.temperature   # Optional[float]
                status = self.controller.status #LaserStatus
                laser_on = status.emission_on # bool
                guide_on = status.guide_laser_on # bool
                messages = self.format_status_message(status) # str
                new_status = {
                    "setpoint": setpoint,
                    'output_power': output_power,
                    "temperature": temperature,
                    "laser_on": laser_on,
                    "guide_on": guide_on,
                    "messages": messages
                }
                self.status_updated.emit(new_status)
            except Exception as e:
                logging.error(f"Polling laser status failed: {e}")
            time.sleep(self.interval)
    
    def stop(self):
        self._running = False
        self.wait()
    

    def format_status_message(self, status: LaserStatus) -> str:
        message_list = []
        if status.command_buffer_overload:
            message_list.append("Command Buffer Overload")
        if status.overheat:
            message_list.append("Overheat")
        if status.emission_on:
            message_list.append("Laser ON")
        if status.high_back_reflection:
            message_list.append("High Back Reflection Level")
        if status.guide_laser_on:
            message_list.append("Guide ON")
        if status.power_supply_off:
            message_list.append("Power Supply Off")
        if status.emission_startup:
            message_list.append("Emission in 3 sec Start-up State")
        if status.power_supply_failure:
            message_list.append("Power Supply Failure")
        if status.front_panel_locked:
            message_list.append("Front Panel Display Locked")
        if status.keyswitch_in_REM:
            message_list.append("Keyswitch in REM Position")
        if status.low_temperature:
            message_list.append("Low Temperature")
        if status.power_supply_alarm:
            message_list.append("Power Supply Alarm")
        if status.critical_error:
            message_list.append("Critial Error")
        if status.fiber_interlock_active:
            message_list.append("Fiber Interlock Active")
        if status.high_average_power:
            message_list.append("High Average Power")
        return "\n\t".join(message_list) if message_list else "Idle"
