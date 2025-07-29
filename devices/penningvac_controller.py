import serial
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BRAUDRATE = 2400
TIMEOUT = 0.5
TERMINATION = "\r\n"


class PenningvacController():
    def __init__(self) -> None:
        self._last_value = 0.0
        self._last_unit = "MBAR"


    def connect(self, COM_PORT: str):
        try:
            self.ser = serial.Serial(COM_PORT, baudrate=BRAUDRATE, timeout=TIMEOUT)
            logging.info(f"PenningVac connected: {COM_PORT}")
        except serial.SerialException as e:
            logging.error(f"Error connecting to {COM_PORT}: {e}")
    

    def disconnect(self):
        try:
            if self.ser.isOpen():
                self.ser.close()
                logging.info("PenningVac disconnected")
        except serial.SerialException as e:
            logging.error(f"Error disconnecting: {e}")
        except AttributeError:
            logging.warning("PenningVac was not connected.")
    

    def __del__(self):
        try:
            self.disconnect()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
        

    @property
    def is_connected(self) -> bool:
        try:
            return self.ser.isOpen()
        except AttributeError as e:
            logging.error(f"Error checking connection: {e}")
            return False


    def _send_command(self, command_str) -> None:
        self.ser.flush()
        enc_command = (command_str + TERMINATION).encode()
        self.ser.write(enc_command)


    def _receive_response(self) -> str:
        res = self.ser.readline()
        return res.decode()


    @property
    def pressure(self) -> tuple[float, str]:
        res = self._receive_response()
        if res == "":
            return self._last_value, self._last_unit
        elif "OFF" in res:
            self._last_value = 0.0
            self._last_unit = "-"
            return self._last_value, self._last_unit
        else:
            res_split = res.replace(" ", "").rstrip().split(":")
            unit = res_split[1]
            value = res_split[2]
            self._last_value = float(value)
            self._last_unit = unit
            return self._last_value, self._last_unit