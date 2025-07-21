from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LITMoSMeasurementData:
    timestamp: str
    sample_temperature: Optional[float]
    reference_temperature: Optional[float]
    reference_power: Optional[float]
    transmitted_power: Optional[float]
    peak_wavelength: Optional[float]
    mean_wavelength: Optional[float]
    rotator_angle: Optional[float]


    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "sample_temperature": self.sample_temperature,
            "reference_temperature": self.reference_temperature,
            "reference_power": self.reference_power,
            "transmitted_power": self.transmitted_power,
            "peak_wavelength": self.peak_wavelength,
            "mean_wavelength": self.mean_wavelength,
            "rotator_angle": self.rotator_angle
        }


class LITMoSMeasurementCollector:
    def __init__(self, flir_cam_widget, power_meter_widget1, power_meter_widget2, spectrometer_widget, rotator_widget):
        self.flir_cam_widget = flir_cam_widget
        self.power_meter_widget1 = power_meter_widget1
        self.power_meter_widget2 = power_meter_widget2
        self.spectrometer_widget = spectrometer_widget
        self.rotator_widget = rotator_widget


    def collect_data(self) -> LITMoSMeasurementData:
        return LITMoSMeasurementData(
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sample_temperature = self.flir_cam_widget.sample_temperature,
            reference_temperature = self.flir_cam_widget.reference_temperature,
            reference_power = self.power_meter_widget1.power,
            transmitted_power = self.power_meter_widget2.power,
            peak_wavelength = self.spectrometer_widget.peak_wavelength,
            mean_wavelength = self.spectrometer_widget.mean_wavelength,
            rotator_angle = self.rotator_widget.angle
        )

