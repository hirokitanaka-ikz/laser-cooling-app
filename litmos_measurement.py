from data_interface import IData
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional



@dataclass
class LITMoSMeasurementData(IData):
    timestamp: str
    sample_temperature: Optional[float] = None
    reference_temperature: Optional[float] = None
    reference_power: Optional[float] = None
    transmitted_power: Optional[float] = None
    peak_wavelength: Optional[float] = None
    mean_wavelength: Optional[float] = None
    rotator_angle: Optional[float] = None


    def to_dict(self) -> dict:
        return asdict(self)


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

