from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QLocale
from widgets.elliptec_rotator_widget import ElliptecRotatorWidget


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("Laser Cooling App")
    win.resize(600, 800)
    layout = QVBoxLayout()
    tab_widget = QTabWidget()

    polling_interval = 0.5 # sec

    # laser_widget = LaserControlWidget(polling_interval=polling_interval)
    # powermeter_widget = OphirPowerMeterWidget(polling_interval=polling_interval)
    # spectrometer_widget = OceanSpectrometerWidget(polling_interval=polling_interval)
    rotator_widget = ElliptecRotatorWidget(polling_interval=polling_interval)

    # tab_widget.addTab(laser_widget, "Laser")
    # tab_widget.addTab(powermeter_widget, "Power Meter")
    # tab_widget.addTab(spectrometer_widget, "Spectrometer")
    tab_widget.addTab(rotator_widget, "Elliptec Rotator")
    # tab_widget.addTab(flir_cam_widget, "Thermal Camera")
    # tab_widget.addTab(litmos_control_widget, "LITMoS Control Panel")


    layout.addWidget(tab_widget)
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()