import socket
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BUFFER_SIZE = 1024
TIMEOUT = 0.5

class LaserStatus:
    '''
    Bit 6, 7, 13, 14, 26, 28 are reserved and not used. 
    '''
    def __init__(self, status_bits: int):
        self._bits = status_bits

    
    def update_status_bits(self, new_status_bits):
        self._bits = new_status_bits
        # logging.info(f"update status bits to {new_status_bits}")

    
    @property
    def command_buffer_overload(self) -> bool:
        return bool(self._bits & (1 << 0)) # Bit 0
    
    @property
    def overheat(self) -> bool:
        return bool(self._bits & (1 << 1)) # Bit 1
    
    @property
    def emission_on(self) -> bool:
        return bool(self._bits & (1 << 2)) # Bit 2
    
    @property
    def high_back_reflection(self) -> bool:
        return bool(self._bits & (1 << 3)) # Bit 3
    
    @property
    def analog_power_control_enabled(self) -> bool:
        return bool(self._bits & (1 << 4)) # Bit 4
    
    @property
    def pulse_too_long(self) -> bool:
        # QCW Models only
        return bool(self._bits & (1 << 5)) # Bit 5
    
    @property
    def guide_laser_on(self) -> bool:
        return bool(self._bits & (1 << 8)) # Bit 8
    
    @property
    def pulse_too_short(self) -> bool:
        return bool(self._bits & (1 << 9)) # Bit 9
    
    @property
    def pulsed_mode(self) -> bool:
        # QCW Models only
        return bool(self._bits & (1 << 10)) # Bit 10
    
    @property
    def power_supply_off(self) -> bool:
        return bool(self._bits & (1 << 11)) # Bit 11
    
    @property
    def modulation_enabled(self) -> bool:
        return bool(self._bits & (1 << 12)) # Bit 12
    
    @property
    def emission_startup(self) -> bool:
        return bool(self._bits & (1 << 15)) # Bit 15
    
    @property
    def gate_mode_enabled(self) -> bool:
        # Lasers with touchscreen only
        return bool(self._bits & (1 << 16)) # Bit 16
    
    @property
    def high_pulse_energy(self) -> bool:
        # QCW Models only
        return bool(self._bits & (1 << 17)) # Bit 17
    
    @property
    def hardware_emission_control_enabled(self) -> bool:
        return bool(self._bits & (1 << 18)) # Bit 18
    
    @property
    def power_supply_failure(self) -> bool:
        return bool(self._bits & (1 << 19)) # Bit 19
    
    @property
    def front_panel_locked(self) -> bool:
        # Lasers with touchscreen only
        return bool(self._bits & (1 << 20)) # Bit 20
    
    @property
    def keyswitch_in_REM(self) -> bool:
        # Lasers with touchscreen only
        return bool(self._bits & (1 << 21)) # Bit 21
    
    @property
    def waveform_pulse_mode(self) -> bool:
        # Lasers with pulse shaping option only
        return bool(self._bits & (1 << 22)) # Bit 22
    
    @property
    def duty_cycle_too_high(self) -> bool:
        # QCW Models only
        return bool(self._bits & (1 << 23)) # Bit 23
    
    @property
    def low_temperature(self) -> bool:
        return bool(self._bits & (1 << 24)) # Bit 24
    
    @property
    def power_supply_alarm(self) -> bool:
        return bool(self._bits & (1 << 25)) # Bit 25
    
    @property
    def hardware_guide_laser_control_enabled(self) -> bool:
        return bool(self._bits & (1 << 27)) # Bit 27
    
    @property
    def critical_error(self) -> bool:
        return bool(self._bits & (1 << 29)) # Bit 29
    
    @property
    def fiber_interlock_active(self) -> bool:
        return bool(self._bits & (1 << 30)) # Bit 30
    
    @property
    def high_average_power(self) -> bool:
        # QCW Models only
        return bool(self._bits & (1 << 31)) # Bit 31
    

    def __repr__(self):
        return f"<LaserStatusBits bits={self._bits:032b}>"


class IPGYLRLaserController:

    def __init__(self) -> None:
        self._is_connected = False
        self._serial_number = ""
        self._status = LaserStatus(0)


    def connect(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(TIMEOUT)
        try:
            self.s.connect((ip, port))
            self._is_connected = True
            self._get_serial_number()
            self._update_status()
            logging.info(f"Connected to laser (serial number: {self._serial_number})")
        except (socket.timeout, socket.error) as e:
            logging.error(f"Connection failed: {e}")
            self._is_connected = False
    
    
    def disconnect(self):
        if self._is_connected:
            try:
                self.s.close()
                self._is_connected = False
                logging.info(f"Disconnected from laser (serial number: {self._serial_number})")
                self._serial_number = ""
            except (socket.timeout, socket.error) as e:
                return

    
    def __del__(self):
        self.disconnect()


    def _update_status(self):
        command = "STA"
        res = self._send_receive(command)
        if res is None:
            return None
        status_decimal = int(res.split(": ")[1])
        self._status.update_status_bits(status_decimal)
    

    @property
    def status(self) -> Optional[LaserStatus]:
        self._update_status()
        return self._status
    

    @property
    def connected(self) -> bool:
        # check status bits and update here
        return self._is_connected
    

    def _send_receive(self, command: str) -> Optional[str]:
        if not self._is_connected:
            logging.error(f"Attempted to send command {command} while not connected.")
            return None
        c = command + "\r"
        try:
            self.s.send(c.encode())
            res = self.s.recv(BUFFER_SIZE).decode().strip()
            if not res:
                logging.error("Received empty response from the laser.")
                return None
        except (socket.timeout, socket.error) as e:
            logging.error(f"Socket error while waiting for response: {e}")
            return None
        return res


    def _send_check(self, command: str) -> bool:
        if not self._is_connected:
            logging.error(f"Attempted to send command {command} while not connected.")
            return False
        c = command + "\r"
        try:
            self.s.send(c.encode())
            res = self.s.recv(BUFFER_SIZE).decode().strip().replace(":", "")
        except (socket.timeout, socket.error) as e:
            logging.error(f"Socket error while waiting for response: {e}")
            return False
        if res == command.strip():
            return True
        else:
            logging.warning(f"Command: {command.strip()} -> Response: {res}")
            return False
    

    def _get_serial_number(self):
        command = "RSN"
        res = self._send_receive(command)
        if res is None:
            return
        self._serial_number = res.split(": ")[1]


    @property
    def serial_number(self) -> str:
        return self._serial_number
    
    
    def guide_on(self):
        command = "ABN"
        ack = self._send_check(command)
        if ack:
            logging.info("Guide laser on")
        else:
            logging.error("Failed to turn guide laser on.")


    def guide_off(self):
        command = "ABF"
        ack = self._send_check(command)
        if ack:
            logging.info("Guide laser off")
        else:
            logging.error("Failed to turn guide laser off.")


    def laser_on(self):
        command = "EMON"
        ack = self._send_check(command)
        if ack:
            logging.info("Laser on")
        else:
            logging.error("Failed to turn laser on.")


    def laser_off(self):
        command = "EMOFF"
        ack = self._send_check(command)
        if ack:
            logging.info("Laser off")
        else:
            logging.error("Failed to turn laser off.")


    def lock_front_panel(self):
        command = "UFP"
        ack = self._send_check(command)
        if not ack:
            logging.error("Failed to lock front panel.")


    def unlock_front_panel(self):
        command = "LFP"
        ack = self._send_check(command)
        if not ack:
            logging.error("Failed to unlock front panel.")

    
    @property
    def setpoint(self) -> Optional[float]:
        command = "RCS"
        res = self._send_receive(command)
        if res is None:
            logging.warning(f"No response while reading setpoint")
            return None
        try:
            return float(res.split(": ")[1])
        except (IndexError, ValueError) as e:
            logging.error(f"Failed to parse setpoint: {res} ({e})")
            return None
    

    @setpoint.setter
    def setpoint(self, new_setpoint: float):
        if not self._is_connected:
            logging.error("Attempted to set setpoint while not connected.")
            return
        ack = self._send_check(f"SDC {new_setpoint:.1f}")
        if not ack:
            logging.error("Failed to set setpoint.")


    @property
    def temperature(self) -> Optional[float]:
        command = "RCT"
        res = self._send_receive(command)
        if res is None:
            return None
        try:
            return float(res.split(": ")[1])
        except (IndexError, ValueError) as e:
            logging.error(f"Failed to parse temperature: {res} ({e})")
            return None


    @property
    def min_setpoint(self) -> Optional[float]:
        command = "RNC"
        res = self._send_receive(command)
        if res is None:
            return None
        try:
            return float(res.split(": ")[1])
        except (IndexError, ValueError) as e:
            logging.error(f"Failed to parse min setpoint: {res} ({e})")
            return None


    @property
    def output_power(self) -> Optional[float]:
        command = "ROP"
        res = self._send_receive(command)
        try:
            val = res.split(": ")[1]
        except IndexError as e:
            logging.error(f"Failed to parse output power response: {res} ({e})")
            return None
        if val == "Off":
            return 0.0
        try:
            return float(val)
        except (TypeError, ValueError) as e:
            logging.error(f"Failed to read output power value: {res} ({e})")
            return None
    

    def help_command(self, command: str):
        c = f"HELP {command}"
        res = self._send_receive(c)
        logging.info(res)

