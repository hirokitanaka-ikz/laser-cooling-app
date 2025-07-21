from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QFormLayout,
    QDoubleSpinBox
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from data_logger import DataLogger
import pyqtgraph as pg
import random
from pathlib import Path
import logging
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def default_filename() -> str:
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{now}_LITMoS"


class LitmosControlPanel(QGroupBox):

    def __init__(self, parent=None):
        super().__init__("LITMoS Measurement Panel", parent)
        self.record_timer = None

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
        if self.record_timer is None:
            folder = QFileDialog.getExistingDirectory(self, "Select Save Destination Folder")
            if not folder:
                QMessageBox.warning(self, "Cancel", "No save folder selected - measurement not starting")
                return
            
            folder_path = Path(folder)
            default_name = default_filename()
            csv_path = folder_path / f"{default_name}.csv"
            yml_path = folder_path / f"{default_name}.yml"
            self.data_logger = DataLogger(csv_path, yml_path) # create data_logger object
            # collect meta data
            meta_data = {'meta_data1': "this is the meta info 1"} # dummy
            self.data_logger.save_meta_data(meta_data=meta_data)
            try:
                self.write_data() # write first data
            except (TypeError, Exception) as e:
                logging.error(f"Failed to write data: {e}")
                return
            self.record_timer = QTimer(self)
            self.record_timer.timeout.connect(self.write_data)
            try:
                self.record_timer.start(int(self.record_interval_spin.value() * 1000)) # sec -> millisec
            except TypeError as e:
                logging.error(f"Failed to start timer: {e}")
                self.record_timer = None
                return
            self.record_btn.setText("Stop Record")
            QMessageBox.information(self, "Recording Start", f"save path: \n{self.data_logger.csv_path}\n{self.data_logger.yml_path}\n\nRecording start")
        else:
            self.record_timer.stop()
            self.record_timer = None
            QMessageBox.information(self, "Recording Stop", f"save path: \n{self.data_logger.csv_path}\n{self.data_logger.yml_path}\n\nRecording stop")
            self.record_btn.setText("Start Record")

    
    
    def collect_data(self) -> dict:
        return {'data1': random.random(),
                'data2': random.random()
                }


    def write_data(self):
        data = self.collect_data()
        self.data_logger.write_csv(data)


    def toggle_rotator(self):
        pass

