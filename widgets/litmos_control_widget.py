from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QFormLayout,
    QDoubleSpinBox
)
from PyQt6.QtCore import QTimer
from data_logger import DataLogger
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def default_filename() -> str:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{now}_LITMoS"


class LitmosControlWidget(QGroupBox):

    def __init__(self, data_collector = None, parent=None):
        super().__init__("LITMoS Measurement Control", parent)
        self.data_collector = data_collector # data collector instance should be given in main()
        self.record_timer = None
        self.plot_fields = [
            "sample_temperature",
            "reference_temperature",
            "laser_power1",
            "laser_power2",
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

        # chart
        self.layout_widget = pg.GraphicsLayoutWidget()
        self.layout_widget.setBackground("w")
        
        # plot 1 (temperature)
        self.plot1 = self.layout_widget.addPlot(row=0, col=0)
        self.plot1.showGrid(x=True, y=True)
        self.plot1.setLabel('bottom', 'Time', units='min')
        self.plot1.setLabel('left', 'Temperature', units='°C')

        self.plot1.showAxis('right')
        self.plot1.getAxis('right').setLabel('Relative Temperature', units='°C')
        self.rel_temp_vb = pg.ViewBox()
        self.plot1.scene().addItem(self.rel_temp_vb)
        self.plot1.getAxis('right').linkToView(self.rel_temp_vb)
        self.rel_temp_vb.setXLink(self.plot1)

        def _update_views():
            self.rel_temp_vb.setGeometry(self.plot1.getViewBox().sceneBoundingRect())
            self.rel_temp_vb.linkedViewChanged(self.plot1.getViewBox(), self.rel_temp_vb.XAxis)

        self.plot1.getViewBox().sigResized.connect(_update_views)
        _update_views()
        

        # plot 2 (laser power)
        self.plot2 = self.layout_widget.addPlot(row=1, col=0)
        self.plot2.showGrid(x=True, y=True)
        self.plot2.setLabel('bottom', 'Time', units='min')
        self.plot2.setLabel('left', 'Laser Power', units='W')

        # plot 3 (wavelength)
        self.plot3 = self.layout_widget.addPlot(row=2, col=0)
        self.plot3.showGrid(x=True, y=True)
        self.plot3.setLabel('bottom', 'Time', units='min')
        self.plot3.setLabel('left', 'Wavelength', units='nm')

        # layout
        record_form = QFormLayout()
        record_form.addRow("Record Interval", self.record_interval_spin)
        record_form.addWidget(self.record_btn)
        
        layout = QVBoxLayout()
        layout.addLayout(record_form)
        layout.addWidget(self.layout_widget)
        self.setLayout(layout)


    def initialize_chart(self):
        # Prepare data buffers
        self.x_data = []
        self.Tsample = []
        self.Tref = []
        self.Pref = []
        self.Ptrans = []
        self.peakWL = []
        self.meanWL = []
        self.rotator = []
        self.start_time = None

        self.curve_Tsample = self.plot1.plot(pen='r', name='Sample Temperature')
        self.curve_Tref = self.plot1.plot(pen='b', name='Reference Temperature')
        self.curve_Pref = self.plot2.plot(pen='r', name='Reference Power')
        self.curve_Ptrans = self.plot2.plot(pen='b', name='Transmitted Power')
        self.curve_peakWL = self.plot3.plot(pen='r', name='Peak Wavelength')
        self.curve_meanWL = self.plot3.plot(pen='b', name='Mean Wavelength')
        self.relTemp = []                        # data buffer
        self.curve_relTemp = pg.PlotCurveItem(pen='g')
        self.rel_temp_vb.addItem(self.curve_relTemp)
        try:
            self.record_timer.stop()
        except Exception:
            pass

    
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
            meta_data = {'meta_data1': "this is the meta info 1"} # dummy meta data
            self.data_logger.save_meta_data(meta_data=meta_data)
            self.initialize_chart()
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
            self.Tsample.append(data_object.sample_temperature if data_object.sample_temperature is not None else np.nan)
            self.Tref.append(data_object.reference_temperature if data_object.reference_temperature is not None else np.nan)
            self.Pref.append(data_object.reference_power if data_object.reference_power is not None else np.nan)
            self.Ptrans.append(data_object.transmitted_power if data_object.transmitted_power is not None else np.nan)
            self.peakWL.append(data_object.peak_wavelength if data_object.peak_wavelength is not None else np.nan)
            self.meanWL.append(data_object.mean_wavelength if data_object.mean_wavelength is not None else np.nan)
            self.relTemp.append((data_object.sample_temperature - data_object.reference_temperature) if (data_object.sample_temperature is not None and data_object.reference_temperature is not None) else np.nan)
            self.update()
            
        except Exception as e:
            logging.error(f"Failed to plot data: {e}")
    

    def update(self):
        self.curve_Tsample.setData(self.x_data, self.Tsample)
        self.curve_Tref.setData(self.x_data, self.Tref)
        self.curve_relTemp.setData(self.x_data, self.relTemp)
        self.curve_Pref.setData(self.x_data, self.Pref)
        self.curve_Ptrans.setData(self.x_data, self.Ptrans)
        self.curve_peakWL.setData(self.x_data, self.peakWL)
        self.curve_meanWL.setData(self.x_data, self.meanWL)
        


