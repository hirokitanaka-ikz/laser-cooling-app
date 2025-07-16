from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout,
    QDoubleSpinBox, QFormLayout
)
from PyQt6.QtCore import QThread, pyqtSignal
import elliptec
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ElliptecRotatorWidget(QGroupBox):
    """
    Control Widget for Thorlabs Elliptec Rotator ELL14;
    use elliptec library https://github.com/roesel/elliptec
    """

    def __init__(self, parent=None):
        super().__init__("Ocean Optics Spectrometer Control", parent)
        self.controller = None
        self.rotator = None
        self.polling_thread = None

    
    def connect(self, com_port:str):
        if self.controller is None:
            try:
                self.controller = elliptec.Controller(com_port)
                self.rotator = elliptec.Rotator(self.controller)
                logging.info("Elliptec device connected")
            except Exception as e:
                logging.error(f"Failed to connect to elliptec device: {e}")
        else:
            if not self.polling_thread is None:
                try:
                    self.polling_thread.stop()
                except Exception as e:
                    logging.error(f"Failed to stop polling: {e}")
            self.polling_thread = None
            self.rotator = None
            self.controller = None
            logging.info("Elliptec device disconnected")


    def home(self):
        if self.rotator is None:
            return
        try:
            self.rotator.home()
        except Exception as e:
            logging.error(f"Failed to move to home: {e}")
    

    def go_to(self, target_angle:float):
        if self.rotator is None:
            return
        try:
            self.rotator.set_angle(target_angle)
        except Exception as e:
            logging.error(f"Failed to move to {target_angle} deg: {e}")



class RotatorPollingThread(QThread):
    updated = pyqtSignal(float)

    def __init__(self, rotator, interval=0.5, parent=None):
        super().__init__(parent)
        self.rotator = rotator
        self.interval = interval
        self._running = True

    
    def run(self):
        while self._running:
            try:
                angle = self.rotator.get_angle() # float?
            except Exception as e:
                logging.error(f"Polling spectrum failed: {e}")
            time.sleep(self.interval)


    def stop(self):
        self._running = False
        self.wait()