import win32com.client
from pywintypes import com_error
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHANNEL = 0 # single channel device


class OphirJunoController:

    def __init__(self) -> None:
        self._ophir_com = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
        self._ophir_com.StopAllStreams()
        self._ophir_com.CloseAll()
        self._connected = False
        self._serial_number = None
        self._device_handler = None
        self._last_power = 0.0
    

    @property
    def connected(self) -> bool:
        return self._connected
    

    @property
    def device_list(self) -> tuple[str]:
        """
        Scans for connected USB devices and returns a list of device handlers.
        Input:
            Serial number (used internally by the ScanUSB method).
        Output:
            List of device handlers (hDevice) corresponding to detected devices.
            Returns an empty list if scanning fails.
        Raises:
            Logs an error and returns an empty list if a COM error occurs during scanning.
        """    
        try:
            return self._ophir_com.ScanUSB()
        except com_error as e:
            logging.error(f"Failed to scan USB devices: {e}")
            return []


    def connect(self, serial_number:str):
        try:
            self._device_handler = self._ophir_com.OpenUSBDevice(serial_number)
            self._ophir_com.StartStream(self._device_handler, CHANNEL)
            self._connected = True
            logging.info("Juno connected and started streaming")
        except (IndexError, com_error) as e:
            logging.error(f"Failed to connect to Juno: {e}")
    

    def disconnect(self):
            try:
                self._ophir_com.StopAllStreams()
                self._ophir_com.CloseAll()
                self._connected = False
                logging.info(f"Juno disconnected")
            except (AttributeError, com_error) as e:
                logging.error(f"Failed to disconnect Juno or Juno not existing")
                # no log if already disconnected


    def __del__(self):
        self.disconnect()
    

    def start_stream(self):
        try:
            self._ophir_com.StartStream(self._device_handler, CHANNEL)
        except com_error as e:
            logging.error(f"Failed to start stream: {e}")


    def stop_stream(self):
        try:
            self._ophir_com.StopStream(self._device_handler, CHANNEL)
        except com_error as e:  
            logging.error(f"Failed to start stream: {e}")


    def get_data(self) -> list[dict]:
        """
        Returns the latest power reading from the device.
        Returns an empty list if not connected or if data is unavailable.
        """
        try:
            value_array, timestamp_array, status_array = self._ophir_com.GetData(self._device_handler, CHANNEL)
            data = [{"value": v, "timestamp": t, "status": s} for v, t, s in zip(value_array, timestamp_array, status_array)]
            return data
        except (ValueError, TypeError, AttributeError, com_error) as e:
            logging.error(f"Failed to get data reading: {e}")
            return []

    
    @property
    def is_sensor_exist(self) -> bool:
        return self._ophir_com.IsSensorExists(self._device_handler, CHANNEL)
    

    @property
    def sensor_info(self) -> Optional[tuple[str]]:
        if self._device_handler == None:
            logging.warning("No device connected")
            return None
        try:
            return self._ophir_com.GetSensorInfo(self._device_handler, CHANNEL)
        except com_error as e:
            logging.error(f"Failed to get sensor info: {e}")
            return None
    

    @property
    def device_info(self) -> Optional[tuple[str]]:
        try:
            return self._ophir_com.GetDeviceInfo(self._device_handler)
        except com_error as e:
            logging.error(f"Failed to get device info: {e}")
            return None
    

    def reset_device(self) -> str:
        try:
            self._ophir_com.ResetDevice(self._device_handler)
        except com_error as e:
            logging.error(f"Failed to reset device: {e}")
            return
        self.update_sensor_info()

    
    @property
    def wavelength(self) -> int:
        """
        GetWavelengths returns a tuple like ((1, ('10.6', '.8-6', '<.8u')))
        The first element (int) is selected index, and the second element (tuple) are currently available wavelengths
        """
        try:
            output = self._ophir_com.GetWavelengths(self._device_handler, CHANNEL)
        except com_error as e:
            logging.error(f"Failed get selected wavelength: {e}")
            return -1
        try:
            index = output[0]
            logging.info(f"Selected Wavelength: [{index}] {output[2][index]}")
            return index
        except (IndexError, TypeError) as e:
            logging.error(f"Failed to get selected wavelength: {e}")
            return -1
    
    
    def modify_wavelength(self, index:int, wavelength:int):
        """
        ModifyWavelength is only applicable to sensors with continuous spectrum
        """
        try:
            self._ophir_com.ModifyWavelength(self._device_handler, CHANNEL, index, wavelength)
        except com_error as e:
            logging.error(f"Failed to modify wavelength: {e}")


    def add_wavelength(self, wavelength:int):
        """
        AddWavelength is only applicable to sensors with continuous spectrum
        """
        try:
            self._ophir_com.AddWavelength(self._device_handler, CHANNEL, wavelength)
        except com_error as e:
            logging.error(f"Failed to add wavelength: {e}")


    @property
    def available_wavelengths(self) -> list:
        try:
            output = self._ophir_com.GetWavelengths(self._device_handler, CHANNEL)
        except com_error as e:
            logging.error(f"Failed to get wavelengths: {e}")
            return list
        try:
            wavelengths_list = output[1]
        except (IndexError, TypeError) as e:
            logging.error(f"Failed to parse wavelengths: {e}")
            return list
        return wavelengths_list
        

    @wavelength.setter
    def wavelength(self, new_index:int):
        try:
            self.stop_stream()
            self._ophir_com.SetWavelength(self._device_handler, CHANNEL, new_index)
            self.start_stream()
            logging.info(f"Wavelength set to Index [{new_index}]")
        except com_error as e:
            logging.error(f"Failed to set wavelength: {e}")
            return
    

    @property
    def available_ranges(self) -> list:
        try:
            output = self._ophir_com.GetRanges(self._device_handler, CHANNEL)
        except com_error as e:
            logging.error(f"Failed to get ranges: {e}")
            return []
        try:
            ranges_list = output[1]
        except (IndexError, TypeError) as e:
            logging.error(f"Failed to parse ranges: {e}")
            return []
        return ranges_list


    @property
    def range(self) -> int:
        """
        GetRanges return a tuple like (0, ('AUTO', '150W', '30.0W')).
        The first element is currently selected index and the second element (tuple) shows available ranges.
        """
        try:
            output = self._ophir_com.GetRanges(self._device_handler, CHANNEL)
            print(f"output: {output}")
        except com_error as e:
            logging.error(f"Failed to get selected ranges: {e}")
            return -1
        try:
            index = output[0]
            logging.info(f"Selected range: [{index}] {output[2][index]}")
            return index
        except (IndexError, TypeError) as e:
            logging.error(f"Failed to get selected ranges: {e}")
            return -1


    @range.setter
    def range(self, new_range_index: int):
        try:
            self.stop_stream()
            self._ophir_com.SetRange(self._device_handler, CHANNEL, new_range_index)
            self.start_stream()
            logging.info(f"Range set to Index [{new_range_index}]")
        except (com_error, TypeError) as e:
            logging.error(f"Failed to set range: {e}")
    

    def save_settings(self):
        try:
            self._ophir_com.SaveSettings(self._device_handler, CHANNEL)
        except com_error as e:
            logging.error(f"Failed to save setting: {e}")

