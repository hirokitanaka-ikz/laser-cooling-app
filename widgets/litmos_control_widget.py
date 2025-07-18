from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QFormLayout,
    QDoubleSpinBox
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import pyqtgraph as pg
import csv
import yaml
from pathlib import Path
import logging
import time
import datetime
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def default_filename() -> str:
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{now}_LITMoS"


class LitmosControlPanel(QGroupBox):

    def __init__(self, parent=None):
        super().__init__("LITMoS Measurement Panel", parent)

        # UI Elements
        self.record_interval_spin = QDoubleSpinBox()
        self.record_interval_spin.setRange(0.1, 60) # sec
        self.record_interval_spin.setValue(1.0)
        self.record_interval_spin.setDecimals(1)
        self.record_interval_spin.setSuffix("sec")
        self.record_btn = QPushButton("Start Record")
        self.record_btn.clicked.connect(self.toggle_record)

        self.rotator_btn = QPushButton("Run BRF rotation")
        self.rotator_btn.clicked.connect(self.toggle_rotator)
        self.rotator_start_spin = QDoubleSpinBox()
        self.rotator_start_spin.setSuffix("°")
        self.rotator_start_spin.setRange(0, 360)
        self.rotator_start_spin.setDecimals(1)
        self.rotator_stop_spin = QDoubleSpinBox()
        self.rotator_stop_spin.setSuffix("°")
        self.rotator_stop_spin.setRange(0, 360)
        self.rotator_stop_spin.setDecimals(1)
        self.rotator_step_spin = QDoubleSpinBox()
        self.rotator_step_spin.setSuffix("°")
        self.rotator_step_spin.setRange(0.01, 90)
        self.rotator_stop_spin.setDecimals(1)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.setLabel("left", "Value")

        # layout
        record_form = QFormLayout()
        record_form.addRow("Record Interval", self.record_interval_spin)
        record_form.addWidget(self.record_btn)

        filter_rotator_form = QFormLayout()
        filter_rotator_form.addRow("Birefringent Filter Rotator", self.rotator_btn)
        filter_rotator_form.addRow("Start Angle", self.rotator_start_spin)
        filter_rotator_form.addRow("Stop Angle", self.rotator_stop_spin)
        filter_rotator_form.addRow("Step Angle", self.rotator_step_spin)

        layout = QVBoxLayout()
        layout.addLayout(record_form)
        layout.addLayout(filter_rotator_form)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    
    def toggle_record(self):
        
        folder = QFileDialog.getExistingDirectory(self, "Select Save Destination Folder")
        if not folder:
            QMessageBox.warning(self, "Cancel", "No save folder selected - measurement not starting")
            return
        
        folder_path = Path(folder)
        default_name = default_filename()
        csv_path = folder_path / f"{default_name}.csv"
        yml_path = folder_path / f"{default_name}.yml"

        # create CSV file
        with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=["timestamp", "device1", "device2"])
            writer.writeheader()

        # create YAML file
        metadata = {
            "start_time": datetime.datetime.now().isoformat()
        }
        with open(yml_path, "w", encoding="utf-8") as f_yml:
            yaml.dump(metadata, f_yml, allow_unicode=True)

        QMessageBox.information(self, "File Created", f"save path: \n{csv_path}\n{yml_path}\n\nmeasurement starting")
        
        # thread start here

    def toggle_rotator(self):
        pass


class RecordThread(QThread):

    ready = pyqtSignal(dict)

    def __init__(self, spectrometer, interval, parent=None):
        super().__init__(parent)
        # self.data_collector
        self.interval = interval
        self._running = True

    
    def run(self):
        while self._running:
            try:
                # prepare data here
                # self.ready.emit(METHOD_NAME_HERE)
                pass
            except Exception as e:
                logging.error(f"collecting data failed: {e}")
            time.sleep(self.interval)


    def stop(self):
        self._running = False
        self.wait()
