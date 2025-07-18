from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QLocale
from widgets.ipg_fiber_laser_widget import LaserControlWidget
from widgets.ophir_powermeter_widget import OphirPowerMeterWidget
from widgets.ocean_spectrometer_widget import OceanSpectrometerWidget
from widgets.elliptec_rotator_widget import ElliptecRotatorWidget
from widgets.flir_camera_widget import FlirCameraWidget


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("Laser Cooling App")
    win.resize(600, 800)
    layout = QVBoxLayout()
    tab_widget = QTabWidget()

    laser_widget = LaserControlWidget()
    powermeter_widget = OphirPowerMeterWidget()
    spectrometer_widget = OceanSpectrometerWidget()
    rotator_widget = ElliptecRotatorWidget()
    flir_cam_widget = FlirCameraWidget()

    tab_widget.addTab(laser_widget, "Laser")
    tab_widget.addTab(powermeter_widget, "Power Meter")
    tab_widget.addTab(spectrometer_widget, "Spectrometer")
    tab_widget.addTab(rotator_widget, "Elliptec Rotator")
    tab_widget.addTab(flir_cam_widget, "Thermal Camera")


    layout.addWidget(tab_widget)
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()