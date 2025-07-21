from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QLocale
from widgets.ipg_fiber_laser_widget import LaserControlWidget
from widgets.ophir_powermeter_widget import OphirPowerMeterWidget
from widgets.ocean_spectrometer_widget import OceanSpectrometerWidget
from widgets.elliptec_rotator_widget import ElliptecRotatorWidget
from widgets.flir_camera_widget import FlirCameraWidget
from widgets.litmos_control_widget import LitmosControlWidget
from litmos_measurement import LITMoSMeasurementCollector


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("Laser Cooling App")
    win.resize(600, 800)
    layout = QVBoxLayout()
    tab_widget = QTabWidget()

    polling_interval = 0.5 # sec

    laser_widget = LaserControlWidget(polling_interval=polling_interval)
    flir_cam_widget = FlirCameraWidget(polling_interval=polling_interval)
    power_meter_widget1 = OphirPowerMeterWidget(polling_interval=polling_interval)
    power_meter_widget2 = OphirPowerMeterWidget(polling_interval=polling_interval)
    spectrometer_widget = OceanSpectrometerWidget(polling_interval=polling_interval)
    rotator_widget = ElliptecRotatorWidget(polling_interval=polling_interval)

    data_collector = LITMoSMeasurementCollector(flir_cam_widget, power_meter_widget1, power_meter_widget2, spectrometer_widget, rotator_widget)
    litmos_widget = LitmosControlWidget(data_collector)


    tab_widget.addTab(laser_widget, "Laser")
    tab_widget.addTab(flir_cam_widget, "Thermal Camera")
    tab_widget.addTab(power_meter_widget1, "Power Meter 1")
    tab_widget.addTab(power_meter_widget2, "Power Meter 2")
    tab_widget.addTab(spectrometer_widget, "Spectrometer")
    tab_widget.addTab(rotator_widget, "Elliptec Rotator")
    tab_widget.addTab(litmos_widget, "LITMoS Measurement Control")


    layout.addWidget(tab_widget)
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()