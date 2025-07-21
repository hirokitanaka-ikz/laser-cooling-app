from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QSpinBox, QFormLayout, QComboBox
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
from typing import Optional
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def average_around_center(image:np.ndarray, x:int, y:int, w:int, h:int) -> float:
        half_w = w // 2
        half_h = h // 2
        x_start = max(x - half_w, 0)
        x_end = min(x + half_w + 1, image.shape[1])
        y_start = max(y - half_h, 0)
        y_end = min(y + half_h + 1, image.shape[0])
        return np.mean(image[y_start:y_end, x_start:x_end])


class FlirCameraWidget(QGroupBox):
    """
    Control widget for FLIR thermal camera;
    Using Spinnaker SDK (python ver 3.10)
    """

    def __init__(self, parent=None, polling_interval=0.5):
        super().__init__("FLIR Camera Control", parent)
        self.controller = None
        self.polling_thread = None
        self._polling_interval = polling_interval
        self.controller = FlirCameraController()
        self.canvas = ThermalImageCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # UI Elements
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)

        self.library_version_label = QLabel(self.controller.library_version)
        self.emissivity_label = QLabel("---")

        self.stream_btn = QPushButton("Start Stream")
        self.stream_btn.clicked.connect(self.toggle_stream)
        self.stream_btn.setEnabled(False)

        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(["viridis", "plasma", "inferno", "magma", "cividis"])
        self.cmap_combo.setCurrentIndex(0)
        self.cmap_combo.currentTextChanged.connect(self.canvas.change_cmap)

        self.temperature_sample_label = QLabel("---")
        self.sample_x_spin = QSpinBox()
        self.sample_y_spin = QSpinBox()
        self.sample_w_spin = QSpinBox()
        self.sample_h_spin = QSpinBox()
        self.sample_x_spin.setRange(0, 639)
        self.sample_y_spin.setRange(0, 479)
        self.sample_w_spin.setRange(1, 100)
        self.sample_h_spin.setRange(1, 100)
        self.sample_x_spin.setValue(280)
        self.sample_y_spin.setValue(220)
        self.sample_w_spin.setValue(50)
        self.sample_h_spin.setValue(20)
        self.sample_x_spin.valueChanged.connect(self.move_rect)
        self.sample_y_spin.valueChanged.connect(self.move_rect)
        self.sample_w_spin.valueChanged.connect(self.move_rect)
        self.sample_h_spin.valueChanged.connect(self.move_rect)

        self.temperature_reference_label = QLabel("---")
        self.reference_x_spin = QSpinBox()
        self.reference_y_spin = QSpinBox()
        self.reference_w_spin = QSpinBox()
        self.reference_h_spin = QSpinBox()
        self.reference_x_spin.setRange(0, 639)
        self.reference_y_spin.setRange(0, 479)
        self.reference_w_spin.setRange(1, 100)
        self.reference_h_spin.setRange(1, 100)
        self.reference_x_spin.setValue(280)
        self.reference_y_spin.setValue(120)
        self.reference_w_spin.setValue(50)
        self.reference_h_spin.setValue(20)
        self.reference_x_spin.valueChanged.connect(self.move_rect)
        self.reference_y_spin.valueChanged.connect(self.move_rect)
        self.reference_w_spin.valueChanged.connect(self.move_rect)
        self.reference_h_spin.valueChanged.connect(self.move_rect)

        self.rect_spin_enabled(False)

        # layout
        layout = QVBoxLayout()

        liberary_version_form = QFormLayout()
        liberary_version_form.addRow("Version:", self.library_version_label)
        layout.addLayout(liberary_version_form)

        layout.addWidget(self.connect_btn)

        info_form = QFormLayout()
        info_form.addRow("Emissivity:", self.emissivity_label)
        layout.addLayout(info_form)
        
        layout.addWidget(self.stream_btn)
        layout.addWidget(self.cmap_combo)

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
                logging.error(e)
                self.controller = None
                return
        else:
            # disconnect
            self.controller.disconnect()
            self.connect_btn.setText("Connect")
            self.rect_spin_enabled(False)
            self.stream_btn.setEnabled(False)
        if self.controller.camera_connected:
            self.connect_btn.setText("Disconnect")
            self.rect_spin_enabled(True)
            self.stream_btn.setEnabled(True)
            self.emissivity_label.setText(f"{self.controller.emissivity}")
    

    def toggle_stream(self):
        if not self.controller.camera_connected:
            return
        if not self.controller.streaming:
            # start stream
            try:
                self.controller.start_stream()
                self.stream_btn.setText("Stop Stream")
                self.polling_thread = FlirCameraPollingThread(self.controller, interval=self._polling_interval)
                self.polling_thread.updated.connect(self.update)
                self.polling_thread.start()
            except Exception as e:
                logging.error(f"Failed to start stream: {e}")
        else:
            # stop stream
            try:
                if not self.polling_thread is None:
                    self.polling_thread.stop()
                    self.polling_thread = None
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


    def update(self, new_image:np.ndarray):
        self.canvas.update_image(new_image)
        self.update_average_temperature(new_image)


    def update_average_temperature(self, image):
        sample_x = self.sample_x_spin.value()
        sample_y = self.sample_y_spin.value()
        sample_w = self.sample_w_spin.value()
        sample_h = self.sample_h_spin.value()
        T_sample = average_around_center(image, sample_x, sample_y, sample_w, sample_h)
        self.temperature_sample_label.setText(f"{T_sample:.2f}°C")

        reference_x = self.reference_x_spin.value()
        reference_y = self.reference_y_spin.value()
        reference_w = self.reference_w_spin.value()
        reference_h = self.reference_h_spin.value()
        T_reference = average_around_center(image, reference_x, reference_y, reference_w, reference_h)
        self.temperature_reference_label.setText(f"{T_reference:.2f}°C")


    def move_rect(self, value):
        """
        identify which widget emits signal --> self.sender()
        sample_rect.set_width(), .set_x(), ...
        """
        if self.sender() == self.sample_x_spin:
            self.canvas.sample_rect.set_x(value)
        elif self.sender() == self.sample_y_spin:
            self.canvas.sample_rect.set_y(value)
        elif self.sender() == self.sample_w_spin:
            self.canvas.sample_rect.set_width(value)
        elif self.sender() == self.sample_h_spin:
            self.canvas.sample_rect.set_height(value)
        elif self.sender() == self.reference_x_spin:
            self.canvas.reference_rect.set_x(value)
        elif self.sender() == self.reference_y_spin:
            self.canvas.reference_rect.set_y(value)
        elif self.sender() == self.reference_w_spin:
            self.canvas.reference_rect.set_width(value)
        elif self.sender() == self.reference_h_spin:
            self.canvas.reference_rect.set_height(value)
    

    @property
    def sample_temperature(self) -> Optional[float]:
        try:
            text = self.temperature_sample_label.text()
            return float(text[:len("°C")].strip())
        except (TypeError, Exception) as e:
            logging.error(f"Failed to read sample temperature for data export: {e}")
            return None
    

    @property
    def reference_temperature(self) -> Optional[float]:
        try:
            text = self.temperature_reference_label.text()
            return float(text[:len("°C")].strip())
        except (TypeError, Exception) as e:
            logging.error(f"Failed to read reference temperature for data export: {e}")
            return None


class ThermalImageCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.axis("off")
        super().__init__(self.fig)
        self.setParent(parent)
        self.image = None
    

    def update_image(self, new_image:np.ndarray):
        if self.image is None:
            self.image = self.ax.imshow(new_image)
            self.create_rects()
        else:
            self.image.set_data(new_image)
        self.draw()
    

    def change_cmap(self, cmap:str):
        try:
            self.image.set_cmap(cmap)
            logging.info(f"cmap changed to {cmap}")
            self.draw()
        except Exception as e:
            logging.error(f"Failed to change cmap to {cmap}: {e}")
    

    def create_rects(self):
        self.sample_rect = patches.Rectangle(xy=(280, 220), width=60, height=20, linewidth=1, ls="dashed", edgecolor="c", facecolor="none")
        self.reference_rect = patches.Rectangle(xy=(280, 120), width=60, height=20, linewidth=1, ls="dashed", edgecolor="w", facecolor="none")
        self.ax.add_patch(self.sample_rect)
        self.ax.add_patch(self.reference_rect)


class FlirCameraPollingThread(QThread):
    updated = pyqtSignal(np.ndarray)

    def __init__(self, controller, interval, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.interval = interval
        self._running = True

    
    def run(self):
        while self._running:
            try:
                image = self.controller.get_image()
                if not image is None:
                    self.updated.emit(image)
            except Exception as e:
                logging.error(f"Thermal camera polling failed: {e}")
            time.sleep(self.interval)


    def stop(self):
        self._running = False
        self.wait()
