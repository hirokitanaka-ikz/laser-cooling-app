from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from PyQt6.QtCore import QLocale
from widgets.ophir_powermeter_widget import OphirPowerMeterWidget
from widgets.ocean_spectrometer_widget import OceanSpectrometerWidget
from widgets.elliptec_rotator_widget import ElliptecRotatorWidget
from widgets.flir_camera_widget import FlirCameraWidget
from widgets.penningvac_widget import PenningVacWidget
from widgets.litmos_control_widget import LitmosControlWidget
from litmos_measurement import LITMoSMeasurementCollector


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("Laser Cooling App")
    win.resize(800, 800)
    main_layout = QHBoxLayout()
    layout_left = QVBoxLayout()
    layout_center = QVBoxLayout()
    layout_right = QVBoxLayout()
    tab_widget = QTabWidget()

    polling_interval = 0.5 # sec

    flir_cam_widget = FlirCameraWidget(polling_interval=polling_interval)
    power_meter_widget1 = OphirPowerMeterWidget(polling_interval=polling_interval)
    power_meter_widget2 = OphirPowerMeterWidget(polling_interval=polling_interval)
    spectrometer_widget = OceanSpectrometerWidget(polling_interval=polling_interval)
    rotator_widget = ElliptecRotatorWidget(polling_interval=polling_interval)
    penningvac_widget = PenningVacWidget(polling_interval=10.0)
    
    data_collector = LITMoSMeasurementCollector(flir_cam_widget, power_meter_widget1, power_meter_widget2, spectrometer_widget, rotator_widget)
    litmos_widget = LitmosControlWidget(data_collector)

    layout_left.addWidget(power_meter_widget1)
    layout_left.addWidget(power_meter_widget2)
    layout_left.addWidget(flir_cam_widget)
    layout_center.addWidget(rotator_widget)
    layout_center.addWidget(spectrometer_widget)
    layout_right.addWidget(penningvac_widget)
    layout_right.addWidget(litmos_widget)
    main_layout.addLayout(layout_left)
    main_layout.addLayout(layout_center)
    main_layout.addLayout(layout_right)
    tab_widget.addWidget(QWidget().setLayout(main_layout), "Main")
    tab_widget.addTab(litmos_widget, "LITMoS Measurement Control")

    win.setLayout(tab_widget)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()