from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QFormLayout,
    QDoubleSpinBox
)
from PyQt6.QtCore import QTimer
from data_logger import DataLogger
import numpy as np
import pyqtgraph as pg
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def default_filename() -> str:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{now}_LITMoS"


class LitmosControlWidget(QGroupBox):

    def __init__(self, rotator, data_collector = None, parent=None):
        super().__init__("LITMoS Measurement Control", parent)
        self.rotator = rotator
        self.data_collector = data_collector # data collector instance should be given in main()
        self.record_timer = None
        self.rotator_timer = None
        self.angle_list = None
        self.angle_index = None
        self.plot_fields = [
            "sample_temperature",
            "reference_temperature",
            "reference_power",
            "transmitted_power",
            "peak_wavelength",
            "mean_wavelength",
            "rotator_angle"
        ]

        # UI Elements
        self.record_interval_spin = QDoubleSpinBox()
        self.record_interval_spin.setRange(0.1, 60) # sec
        self.record_interval_spin.setValue(1.0)
        self.record_interval_spin.setDecimals(1)
        self.record_interval_spin.setSuffix("sec")
        self.record_btn = QPushButton("Start Record")
        self.record_btn.clicked.connect(self.toggle_record)

        self.rotator_btn = QPushButton("Run")
        self.rotator_btn.clicked.connect(self.toggle_rotator)
        self.rotator_start_spin = QDoubleSpinBox()
        self.rotator_start_spin.setSuffix("°")
        self.rotator_start_spin.setRange(0.0, 360.0)
        self.rotator_start_spin.setDecimals(1)
        self.rotator_stop_spin = QDoubleSpinBox()
        self.rotator_stop_spin.setSuffix("°")
        self.rotator_stop_spin.setRange(0.0, 360.0)
        self.rotator_stop_spin.setDecimals(1)
        self.rotator_step_spin = QDoubleSpinBox()
        self.rotator_step_spin.setSuffix("°")
        self.rotator_step_spin.setRange(0.01, 90.0)
        self.rotator_step_spin.setDecimals(1)
        self.rotator_step_spin.setValue(0.5)
        self.rotator_time_spin = QDoubleSpinBox()
        self.rotator_time_spin.setSuffix("min")
        self.rotator_time_spin.setRange(0.01, 120.0)
        self.rotator_time_spin.setDecimals(1)

        # chart
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("bottom", "Time", units="min")
        self.plot_widget.setLabel("left", "Value")

        # layout
        record_form = QFormLayout()
        record_form.addRow("Record Interval", self.record_interval_spin)
        record_form.addWidget(self.record_btn)

        rotator_form = QFormLayout()
        rotator_form.addRow("Rotator", self.rotator_btn)
        rotator_form.addRow("Start Angle", self.rotator_start_spin)
        rotator_form.addRow("Stop Angle", self.rotator_stop_spin)
        rotator_form.addRow("Step Angle", self.rotator_step_spin)
        rotator_form.addRow("Time per Step", self.rotator_time_spin)
        

        layout = QVBoxLayout()
        layout.addLayout(record_form)
        layout.addLayout(rotator_form)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    
    def initialize_chart(self):
        self.x_data = []  # timestamp as seconds from start
        self.y_data = {field: [] for field in self.plot_fields}
        self.start_time = None

        colors = ['r', 'g', 'b', 'm', 'c', 'y', 'k']
        self.curves = {}
        for field, color in zip(self.plot_fields, colors):
            curve = self.plot_widget.plot(pen=color, name=field)
            self.curves[field] = curve
    

    def rotator_widget_enable(self, enabled: bool) -> None:
        self.rotator_start_spin.setEnabled(enabled)
        self.rotator_stop_spin.setEnabled(enabled)
        self.rotator_step_spin.setEnabled(enabled)
        self.rotator_time_spin.setEnabled(enabled)
    

    def toggle_rotator(self):
        if self.rotator_timer is None:
            # read values from double spin boxes
            start_angle = self.rotator_start_spin.value()
            stop_angle = self.rotator_stop_spin.value()
            step_angle = self.rotator_step_spin.value()
            duration = self.rotator_time_spin.value()
            
            # make a list of angles
            if start_angle < stop_angle:
                self.angle_list = np.arange(start_angle, stop_angle + step_angle, step_angle)
            elif start_angle > stop_angle:
                self.angle_list = np.arange(start_angle, stop_angle - stop_angle, -stop_angle)
            else: # start = stop
                QMessageBox.warning(self, "Invalid Inputs", "start angle = stop angle")
                return
            # create QTimer
            self.rotator_timer = QTimer(self)
            self.rotator_timer.timeout.connect(self.move_next_angle)
            self.move_next_angle() # go to start angle
            self.rotator_timer.start(int(duration * 60 * 1000)) # min to millisec
            # disable spinboxes and rename toggle button
            self.rotator_btn.setText("Stop")
            self.rotator_widget_enable(False)
        else:
            self.rotator_timer.stop()
            self.rotator_timer = None
            self.angle_list = None
            logging.info("Rotator stopped")
            self.rotator_btn.setText("Run")
            self.rotator_widget_enable(True)
    

    def __del__(self):
        try:
            self.record_timer.stop()
            self.rotator_timer.stop()
        except Exception as e:
            pass
    

    def move_next_angle(self):
        if self.angle_index is None:
            self.angle_index = 0

        if self.angle_index < len(self.angle_list):
            self.rotator.go_to(self.angle_list[self.angle_index])
            logging.info(f"Rotator moved to {self.angle_list[self.angle_index]}°")
            self.angle_index += 1
        else:
            self.angle_index = None
            self.rotator_timer.stop()
            self.rotator_timer = None
            self.angle_list = None
            logging.info("Rotator reached stop angle")
            self.rotator_btn.setText("Run")
            self.rotator_widget_enable(True)

    
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
            self.initialize_chart()
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
            logging.info("LITMoS data recording started")
            # here, write code for adding data to chart
        else:
            self.record_timer.stop()
            self.record_timer = None
            QMessageBox.information(self, "Recording Stop", f"save path: \n{self.data_logger.csv_path}\n{self.data_logger.yml_path}\n\nRecording stop")
            logging.info("LITMoS data recording stopped")
            self.record_btn.setText("Start Record")


    def save_meta_data(self) -> None:
        pass


    def write_data(self) -> None:
        data_object = self.data_collector.collect_data()
        self.data_logger.write_csv(data_object)
        try:
            timestamp = datetime.fromisoformat(data_object.timestamp)
            if self.start_time is None:
                self.start_time = timestamp
            elapsed_min = (timestamp - self.start_time).total_seconds() / 60
            self.x_data.append(elapsed_min)

            for field in self.plot_fields:
                value = data_object.to_dict().get(field, None)
                self.y_data[field].append(value if value is not None else float ("nan"))
                self.curves[field].setData(self.x_data, self.y_data[field])
            
            self.plot_widget.setXRange(max(0, elapsed_min - 60), elapsed_min) # last 60 min
        except Exception as e:
            logging.error(f"Failed to plot data: {e}")


