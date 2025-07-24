from PyQt6.Qtcore import QThread
import time
import logging
from abc import ABC, abstractmethod


class BasePollingThread(QThread, ABC):
    """
    Abstract base class for polling thread
    """
    def __init__(self, controller, interval:float, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.interval = interval
        self._running = True # run when polling thread instance is generated
    

    def run(self):
        while self._running:
            try:
                data = self.get_data()
                if data is not None:
                    self.emit_data(data)
            except Exception as e:
                logging.error(f"{self.__class__.__name__} polling failed: {e}")
            time.sleep(self.interval)
    

    @abstractmethod
    def get_data(self):
        """
        method to get data to be emitted
        """
        pass


    @abstractmethod
    def emit_data(self, data):
        """
        method to emit signal
        example) self.updated.emit(data)
        *** updated = pyqtSignal([data type]) should be writtin outside of __init__()
        """
        pass
