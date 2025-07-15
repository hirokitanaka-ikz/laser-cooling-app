from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QDoubleSpinBox, QMessageBox, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer
from devices.ipg_ylr_laser_controller import IPGYLRLaserController, LaserStatus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


IP = "10.10.10.20"
PORT = "10001"


class LaserControlWidget(QGroupBox):
    
    def __init__(self, parent=None):
        super().__init__("IPG Fiber Laser Control", parent)

        self.controller = IPGYLRLaserController()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_status)

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
        self.setpoint_spin.setSingleStep(0.1)
        self.setpoint_spin.valueChanged.connect(self.update_setpoint)
        self.setpoint_spin.setEnabled(False)

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
                QMessageBox.critical(self, "Connection Error", e)
            self.connect_btn.setText("Disconnect")
            self.status_label.setText("Connected")
            self.set_controls_enabled(True)
            self.timer.start()
            self.update_status()
            self.ip_edit.setEnabled(False)
            self.port_edit.setEnabled(False)
        else:
            # Disconnect
            self.timer.stop()
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


    def update_status(self):
        if not self.controller:
            return
        try:
            self.setpoint_spin.setValue(self.controller.setpoint)
            self.temp_label.setText(f"Temp: {self.controller.temperature:.1f} °C")

            current_status = self.controller.status

            self.laser_btn.setText("Turn Laser OFF" if current_status.emission_on else "Turn Laser ON")
            self.guide_btn.setText("Turn Guide OFF" if current_status.guide_laser_on else "Turn Guide ON")
            self.laser_status_display.setText("Laser Status:\n" + self.interpret_status(current_status))
        except Exception as e:
            self.status_label.setText(f"Error: {e}")


    def clear_status_display(self):
        self.setpoint_spin.setValue(0)
        self.temp_label.setText("Temp: --- °C")
        self.laser_status_display.setText("Laser Status: ---")
        self.laser_btn.setText("Turn Laser ON")
        self.guide_btn.setText("Turn Guide ON")


    def interpret_status(self, status: LaserStatus) -> str:
        messages = []
        if status.emission_on:
            messages.append("Laser ON")
        if status.guide_laser_on:
            messages.append("Guide ON")
        if status.emission_startup:
            messages.append("Laser Starting...")
        if status.overheat:
            messages.append("Over Temperature")
        if status.low_temperature:
            messages.append("Low Temperature")
        if status.power_supply_off:
            messages.append("Power Supply OFF")
        return "\n".join(messages) if messages else "Idle"
