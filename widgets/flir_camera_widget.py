from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QSpinBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from devices.flir_camera_controller import FlirCameraController
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib import patches
from matplotlib.figure import Figure
import numpy as np
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FlirCameraWidget(QGroupBox):
    """
    Control widget for FLIR thermal camera;
    Using Spinnaker SDK (python ver 3.10)
    """

    def __init__(self, parent=None):
        super().__init__("FLIR Camera Control", parent)
        self.controller = None
        self.polling_thread = None
        self.controller = FlirCameraController()


        # UI Elements
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)

        self.library_version_label = QLabel(self.controller.library_version)
        self.emissivity_label = QLabel("---")

        self.stream_btn = QPushButton("Start Stream")
        self.stream_btn.clicked.connect(self.toggle_stream)


        self.temperature_sample_label = QLabel("---")
        self.sample_x_spin = QSpinBox()
        self.sample_y_spin = QSpinBox()
        self.sample_w_spin = QSpinBox()
        self.sample_h_spin = QSpinBox()

        self.temperature_reference_label = QLabel("---")
        self.reference_x_spin = QSpinBox()
        self.reference_y_spin = QSpinBox()
        self.reference_w_spin = QSpinBox()
        self.reference_h_spin = QSpinBox()

        self.rect_spin_enabled(False)

        self.canvas = ThermalImageCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)


        # layout
        layout = QVBoxLayout()

        liberary_version_form = QFormLayout()
        liberary_version_form.addRow("Version:", self.library_version_label)
        layout.addLayout(liberary_version_form)

        layout.addWidget(self.connect_btn)

        info_form = QFormLayout()
        info_form.addRow("Emissivity:", self.emissivity_label)
        layout.addLayout(info_form)

        sample_form = QFormLayout()
        sample_form.addRow("Sample Temperature:", self.temperature_sample_label)
        sample_form.addRow("X:", self.sample_x_spin)
        sample_form.addRow("Y:", self.sample_y_spin)
        sample_form.addRow("Width:", self.sample_w_spin)
        sample_form.addRow("Height:", self.sample_h_spin)

        reference_form = QFormLayout()
        reference_form.addRow("Reference Temperature:", self.temperature_reference_label)
        reference_form.addRow("X:", self.reference_x_spin)
        reference_form.addRow("Y:", self.reference_y_spin)
        reference_form.addRow("Width:", self.reference_w_spin)
        reference_form.addRow("Height:", self.reference_h_spin)

        hbox = QHBoxLayout()
        hbox.addLayout(sample_form)
        hbox.addLayout(reference_form)

        layout.addLayout(hbox)
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)
    

    def toggle_connect(self):
        if not self.controller.camera_connected:
            # connect
            try:
                self.controller.connect()
            except Exception as e:
                self.controller = None
                return
            if self.controller.camera_connected:
                self.connect_btn.setText("Disconnect")
                self.rect_spin_enabled(True)
                self.version_label.setText(self.controller.library_version)
                self.emissivity_label.setText(self.controller.emissivity)
        else:
            # disconnect
            self.controller.disconnect()
            self.controller = None
            self.connect_btn.setText("Connect")
            self.rect_spin_enabled(False)
    

    def toggle_stream(self):
        if self.controller is None:
            return
        if not self.streaming:
            # start stream
            try:
                self.controller.start_stream()
                self.stream_btn.setText("Stop Stream")
            except Exception as e:
                logging.error(f"Failed to start stream: {e}")
        else:
            # stop stream
            try:
                self.controller.stop_stream()
                self.stream_btn.setText("Start Stream")
            except Exception as e:
                logging.error(f"Failed to stop stream: {e}")
    

    def clear_uis(self):
        pass


    def rect_spin_enabled(self, enabled:bool):
        self.sample_x_spin.setEnabled(enabled)
        self.sample_y_spin.setEnabled(enabled)
        self.sample_w_spin.setEnabled(enabled)
        self.sample_h_spin.setEnabled(enabled)
        self.reference_x_spin.setEnabled(enabled)
        self.reference_y_spin.setEnabled(enabled)
        self.reference_w_spin.setEnabled(enabled)
        self.reference_h_spin.setEnabled(enabled)


    def update_image(self):
        pass

    def update_average_temperature(self):
        pass


    def move_rect(self):
        """
        identify which widget emits signal --> self.sender()
        sample_rect.set_width(), .set_x(), ...
        """
        pass


class ThermalImageCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(4, 3))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self.image = None
    

    def update_image(self, new_image:np.ndarray):
        self.ax.clear()
        self.image = self.ax.imshow(new_image, cmap="hot")
        self.ax.axis("off")
        self.draw()
    

    def create_rect(self):
        self.sample_rect = patches.Rectangle(xy=(280, 220), width=60, height=20, linewidth=1, ls="dashed", edgecolor="c", facecolor="none")
        self.reference_rect = patches.Rectangle(xy=(280, 120), width=60, height=20, linewidth=1, ls="dashed", edgecolor="w", facecolor="none")
        self.ax.add_patch(self.sample_rect)
        self.ax.add_patch(self.reference_rect)


"""
1. Polling start
2. get image from camera and updated signal emits
3. update image method -> Widget class transfers new_image to Canvas
4. calculate average temperature using rect info
"""

class FlirCameraPollingThread(QThread):
    updated = pyqtSignal(np.ndarray)

    def __init__(self, controller, interval=0.5, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.interval = interval
        self._running = True

    
    def run(self):
        while self._running:
            try:
                image = self.controller.get_image() # ??
                if not image is None: # empty array?
                    self.updated.emit(image)
            except Exception as e:
                logging.error(f"Thermal camera polling failed: {e}")
            time.sleep(self.interval)


    def stop(self):
        self._running = False
        self.wait()
