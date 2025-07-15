from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QLocale
from widgets.ipg_fiber_laser_widget import LaserControlWidget
from widgets.ophir_powermeter_widget import OphirPowerMeterWidget


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("Laser Cooling App")
    win.resize(400, 300)
    layout = QVBoxLayout()
    tab_widget = QTabWidget()

    laser_widget = LaserControlWidget()
    powermeter_widget = OphirPowerMeterWidget()

    tab_widget.addTab(laser_widget, "Laser Control")
    tab_widget.addTab(powermeter_widget, "Power Meter Control")

    layout.addWidget(tab_widget)
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()