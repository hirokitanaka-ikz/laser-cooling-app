from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QDoubleSpinBox, QMessageBox, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer

from devices.ipg_ylr_laser_controller import IPGYLRLaserController


class LaserControlWidget(QGroupBox):
    
    def __init__(self, parent=None):
        super().__init__("IPG Fiber Laser Control", parent)

        self.controller = None
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_status)

        # Connection input fields
        self.ip_edit = QLineEdit("192.168.0.100")
        self.port_edit = QLineEdit("10000")
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
        self.setpoint_spin.setSuffix(" A")
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
        ip = self.ip_edit.text().strip()
        try:
            port = int(self.port_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Port must be an integer.")
            return

        if self.controller is None:
            # Attempt to connect
            try:
                self.controller = IPGYLRLaserController(ip=ip, port=port)
                self.controller.connect()
                self.connect_btn.setText("Disconnect")
                self.status_label.setText("Connected")
                self.set_controls_enabled(True)
                self.timer.start()
                self.update_status()
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))
                self.controller = None
        else:
            # Disconnect
            self.timer.stop()
            try:
                self.controller.disconnect()
            except Exception:
                pass
            self.controller = None
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
        state = self.controller.is_laser_on()
        if state:
            self.controller.laser_off()
        else:
            self.controller.laser_on()
        self.update_status()


    def toggle_guide(self):
        if not self.controller:
            return
        state = self.controller.is_guide_on()
        if state:
            self.controller.guide_off()
        else:
            self.controller.guide_on()
        self.update_status()


    def update_setpoint(self, value):
        if self.controller:
            self.controller.set_current_setpoint(value)


    def update_status(self):
        if not self.controller:
            return
        try:
            self.setpoint_spin.setValue(self.controller.get_current_setpoint())
            self.temp_label.setText(f"Temp: {self.controller.get_temperature():.2f} °C")

            laser_on = self.controller.is_laser_on()
            guide_on = self.controller.is_guide_on()

            self.laser_btn.setText("Turn Laser OFF" if laser_on else "Turn Laser ON")
            self.guide_btn.setText("Turn Guide OFF" if guide_on else "Turn Guide ON")

            status_bits = self.controller.get_laser_status()
            self.laser_status_display.setText("Laser Status: " + self.interpret_status(status_bits))
        except Exception as e:
            self.status_label.setText(f"Error: {e}")


    def clear_status_display(self):
        self.setpoint_spin.setValue(0)
        self.temp_label.setText("Temp: --- °C")
        self.laser_status_display.setText("Laser Status: ---")
        self.laser_btn.setText("Turn Laser ON")
        self.guide_btn.setText("Turn Guide ON")


    def interpret_status(self, status: int) -> str:
        messages = []
        if status & 0x01:
            messages.append("Laser ON")
        if status & 0x02:
            messages.append("Guide ON")
        if status & 0x04:
            messages.append("Over Temp")
        if status & 0x08:
            messages.append("Interlock Open")
        if status & 0x10:
            messages.append("Error")
        return ", ".join(messages) if messages else "Idle"
