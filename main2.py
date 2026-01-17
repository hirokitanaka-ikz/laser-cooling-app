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
    win.resize(1800, 1000)
    laytout1 = QHBoxLayout()
    layout_left = QVBoxLayout()
    layout_center = QVBoxLayout()
    layout_right = QVBoxLayout()
    layout2 = QVBoxLayout()
    tabs = QTabWidget()
    tab1 = QWidget()
    tab2 = QWidget()

    polling_interval = 0.5 # sec

    flir_cam_widget = FlirCameraWidget(polling_interval=polling_interval)
    power_meter_widget1 = OphirPowerMeterWidget(polling_interval=polling_interval)
    power_meter_widget2 = OphirPowerMeterWidget(polling_interval=polling_interval)
    spectrometer_widget = OceanSpectrometerWidget(polling_interval=polling_interval)
    rotator_widget = ElliptecRotatorWidget(polling_interval=2.0)
    penningvac_widget = PenningVacWidget(polling_interval=10.0)
    
    data_collector = LITMoSMeasurementCollector(
        power_meter_widget1 = power_meter_widget1,
        power_meter_widget2 = power_meter_widget2,
        penningvac_widget = penningvac_widget,
        spectrometer_widget = spectrometer_widget,
        rotator_widget = rotator_widget,
        flir_cam_widget = flir_cam_widget
        )
    litmos_widget = LitmosControlWidget(data_collector)

    layout_left.addWidget(power_meter_widget1)
    layout_left.addWidget(power_meter_widget2)
    layout_left.addWidget(penningvac_widget)
    layout_center.addWidget(rotator_widget)
    layout_center.addWidget(spectrometer_widget)
    layout_right.addWidget(flir_cam_widget)
    laytout1.addLayout(layout_left)
    laytout1.addLayout(layout_center)
    laytout1.addLayout(layout_right)

    tab1.setLayout(laytout1)
    layout2.addWidget(litmos_widget)
    tab2.setLayout(layout2)

    tabs.addTab(tab1, "Control")
    tabs.addTab(tab2, "LITMoS Measurement")

    main_layout = QVBoxLayout()
    main_layout.addWidget(tabs)
    win.setLayout(main_layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()