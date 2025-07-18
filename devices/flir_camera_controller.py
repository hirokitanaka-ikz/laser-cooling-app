import os
import PySpin # install using wheel!
import numpy as np
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class IRFormatType:
    LINEAR_10MK = 1
    LINEAR_100MK = 2
    RADIOMETRIC = 3


class FlirCameraController:

    def __init__(self) -> None:
        self._ir_type = IRFormatType.RADIOMETRIC
        self._system = PySpin.System.GetInstance()
         # system object is used to retrive the list of interfaces and cameras available
        self._cam_list = []
        self._camera = None
        self._streaming = False
    
    
    @property
    def camera_connected(self) -> bool:
        if self._camera is None:
            return False
        else:
            return True
    

    @property
    def streaming(self) -> bool:
        return self._streaming
    

    def connect(self):
        if self._camera is None:
            try:
                self._cam_list = self._system.GetCameras() # PySpin.CameraList object
                num_cameras = self._cam_list.GetSize()
                logging.info(f"Number of cameras detected: {num_cameras}")
                if num_cameras == 0:
                    self._cam_list.Clear()
                    logging.info("No FLIR camera found")
                    return
                self._camera = self._cam_list[0] # use the first available camera
                self.NodeMapTlDevice = self._camera.GetTLDeviceNodeMap()
                self._camera.Init()
                self.Nodemap = self._camera.GetNodeMap()
                self.set_calibration_parameters()
                logging.info("FLIR camera connected")
            except PySpin.SpinnakerException as e:
                logging.error(f"Failed to connect: {e}")


    def disconnect(self):
        if self._camera is None:
            return
        try:
            self.stop_stream()
            self._camera.DeInit()
            self._camera = None
            self._cam_list.Clear()
            logging.info("FLIR camera disconnected")
        except Exception as e:
            logging.error(f"Failed to disconnect camera: {e}")
    

    def __del__(self):
        self.disconnect()
        self._system.ReleaseInstance()
    

    @property
    def serial_number(self) -> str:
        self.NodeDeviceSerialNumber = PySpin.CStringPtr(self.NodeMapTlDevice.GetNode('DeviceSerialNumber'))
        if PySpin.IsAvailable(self.NodeDeviceSerialNumber) and PySpin.IsReadable(self.NodeDeviceSerialNumber):
            self.DeviceSerialNumber = self.NodeDeviceSerialNumber.GetValue()
            logging.info(f"Device serial number retrieved as {self.DeviceSerialNumber}")
            return 
            

    @property
    def library_version(self) -> str:
        try:
            version = self._system.GetLibraryVersion()
            version_string = f"{version.major}.{version.minor}.{version.type}.{version.build}"
            return version_string
        except PySpin.SpinnakerException as e:
            logging.error(f"Failed to read version: {e}")
            return ""
    

    @property
    def camera_list(self) -> list:
        pass


    @property
    def emissivity(self) -> Optional[float]:
        if self._camera is None:
            return None
        try:
            return self._emissivity
        except PySpin.SpinnakerException as e:
            logging.error(f"Failed to read emissivity: {e}")
            return None


    def set_calibration_parameters(self) -> None:
        # Retrieve Calibration details
        try:
            self.NodeCalibrationQueryR = PySpin.CFloatPtr(self.Nodemap.GetNode('R'))
            self._R = self.NodeCalibrationQueryR.GetValue()

            self.NodeCalibrationQueryB = PySpin.CFloatPtr(self.Nodemap.GetNode('B'))
            self._B = self.NodeCalibrationQueryB.GetValue()

            self.NodeCalibrationQueryF = PySpin.CFloatPtr(self.Nodemap.GetNode('F'))
            self._F = self.NodeCalibrationQueryF.GetValue()

            self.NodeCalibrationQueryX = PySpin.CFloatPtr(self.Nodemap.GetNode('X'))
            self._X = self.NodeCalibrationQueryX.GetValue()

            self.NodeCalibrationQueryA1 = PySpin.CFloatPtr(self.Nodemap.GetNode('alpha1'))
            self._A1 = self.NodeCalibrationQueryA1.GetValue()

            self.NodeCalibrationQueryA2 = PySpin.CFloatPtr(self.Nodemap.GetNode('alpha2'))
            self._A2 = self.NodeCalibrationQueryA2.GetValue()

            self.NodeCalibrationQueryB1 = PySpin.CFloatPtr(self.Nodemap.GetNode('beta1'))
            self._B1 = self.NodeCalibrationQueryB1.GetValue()

            self.NodeCalibrationQueryB2 = PySpin.CFloatPtr(self.Nodemap.GetNode('beta2'))
            self._B2 = self.NodeCalibrationQueryB2.GetValue()

            self.NodeCalibrationQueryJ1 = PySpin.CFloatPtr(self.Nodemap.GetNode('J1'))
            self._J1 = self.NodeCalibrationQueryJ1.GetValue()

            self.NodeCalibrationQueryJ0 = PySpin.CIntegerPtr(self.Nodemap.GetNode('J0'))
            self._J0 = self.NodeCalibrationQueryJ0.GetValue()

            self._emissivity = 0.97
            self._TRefl = 293.15
            self._TAtm = 293.15
            self._TAtmC = self._TAtm - 273.15
            self._Humidity = 0.55
            self._Dist = 2
            self._ExtOpticsTransmission = 1
            self._ExtOpticsTemp = self._TAtm
            self._H2O = self._Humidity * np.exp(1.5587 + 0.06939 * self._TAtmC - 0.00027816 * self._TAtmC * self._TAtmC + 0.00000068455 * self._TAtmC * self._TAtmC * self._TAtmC)
            self._Tau = self._X * np.exp(-np.sqrt(self._Dist) * (self._A1 + self._B1 * np.sqrt(self._H2O))) + (1 - self._X) * np.exp(-np.sqrt(self._Dist) * (self._A2 + self._B2 * np.sqrt(self._H2O)))
            # Pseudo radiance of the reflected environment
            self._r1 = ((1 - self._emissivity) / self._emissivity) * (self._R / (np.exp(self._B / self._TRefl) - self._F))
            # Pseudo radiance of the atmosphere
            self._r2 = ((1 - self._Tau) / (self._emissivity * self._Tau)) * (self._R / (np.exp(self._B / self._TAtm) - self._F))
            # Pseudo radiance of the external optics
            self._r3 = ((1 - self._ExtOpticsTransmission) / (self._emissivity * self._Tau * self._ExtOpticsTransmission)) * (self._R / (np.exp(self._B / self._ExtOpticsTemp) - self._F))
            self._K2 = self._r1 + self._r2 + self._r3
            logging.info("Parameters of camera successfully retrieved")
        except (PySpin.SpinnakerException, Exception) as e:
            logging.error(f"Failed to read parameters: {e}")


    def start_stream(self):
        self.setup_camera()
        logging.info("Image acquisition set up...")

        try:
            self.NodeAcquisitionMode = PySpin.CEnumerationPtr(self.Nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(self.NodeAcquisitionMode) or not PySpin.IsWritable(self.NodeAcquisitionMode):
                logging.warning("Unable to set acquisition mode to continuous (enum retrieval). Aborting...")
                return False

            self.NodeAcquisitionModeContinuous = self.NodeAcquisitionMode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(self.NodeAcquisitionModeContinuous) or not PySpin.IsReadable(self.NodeAcquisitionModeContinuous):
                logging.warning("Unable to set acquisition mode to continuous (enum retrieval). Aborting...")
                return False

            self.AcquisitionModeContinuous = self.NodeAcquisitionModeContinuous.GetValue()
            self.NodeAcquisitionMode.SetIntValue(self.AcquisitionModeContinuous)
            logging.info('Acquisition mode set to continuous...')
            self._camera.BeginAcquisition()
            self._streaming = True
            logging.info("Camera started streaming")
        except PySpin.SpinnakerException as e:
            logging.error(f"Failed to start streaming: {e}")
    

    def stop_stream(self):
        if self._streaming:
            try:
                self._camera.EndAcquisition()
            except Exception as e:
                logging.error(f"Failed to stop streaming: {e}")
            finally:
                self._streaming = False
        

    def get_image(self) -> Optional[np.ndarray]:
        if self._streaming:
            try:
                self.ImageResult = self._camera.GetNextImage(1000)
                if self.ImageResult.IsIncomplete():
                    print('Image incomplete with image status %d ...' %
                            self.ImageResult.GetImageStatus())
                else:
                    self.ImageData = self.ImageResult.GetNDArray()

                    if self._ir_type == IRFormatType.LINEAR_10MK:
                        self.ImageTempCelsiusHigh = (self.ImageData * 0.01) - 273.15
                    elif self._ir_type == IRFormatType.LINEAR_100MK:
                        self.ImageTempCelsiusLow = (self.ImageData * 0.1) - 273.15
                    elif self._ir_type == IRFormatType.RADIOMETRIC:
                        self.ImageRadiance = (self.ImageData - self._J0) / self._J1
                        self.ImageTemp = (self._B / np.log(self._R / ((self.ImageRadiance / self._emissivity / self._Tau) - self._K2) + self._F)) - 273.15
                self.ImageResult.Release()
                return self.ImageTemp
            except PySpin.SpinnakerException as e:
                logging.error(f"Failed to get image: {e}")
                return None


    def setup_camera(self):
        self.StreamNodeMap = self._camera.GetTLStreamNodeMap()
        self.NodeBufferHandlingMode = PySpin.CEnumerationPtr(self.StreamNodeMap.GetNode('StreamBufferHandlingMode'))
        self.NodePixelFormat = PySpin.CEnumerationPtr(self.Nodemap.GetNode('PixelFormat'))
        self.NodePixelFormatMono16 = PySpin.CEnumEntryPtr(self.NodePixelFormat.GetEntryByName('Mono16'))
        self.PixelFormatMono16 = self.NodePixelFormatMono16.GetValue()
        self.NodePixelFormat.SetIntValue(self.PixelFormatMono16)
        if self._ir_type == IRFormatType.LINEAR_10MK:
            self.NodeIRFormat = PySpin.CEnumerationPtr(self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearHigh = PySpin.CEnumEntryPtr(self.NodeIRFormat.GetEntryByName('TemperatureLinear10mK'))
            self.NodeTempHigh = self.NodeTempLinearHigh.GetValue()
            self.NodeIRFormat.SetIntValue(self.NodeTempHigh)
        if self._ir_type == IRFormatType.LINEAR_100MK:
            self.NodeIRFormat = PySpin.CEnumerationPtr(self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearLow = PySpin.CEnumEntryPtr(self.NodeIRFormat.GetEntryByName('TemperatureLinear100mK'))
            self.NodeTempLow = self.NodeTempLinearLow.GetValue()
            self.NodeIRFormat.SetIntValue(self.NodeTempLow)
        if self._ir_type == IRFormatType.RADIOMETRIC:
            self.NodeIRFormat = PySpin.CEnumerationPtr(self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearLow = PySpin.CEnumEntryPtr(self.NodeIRFormat.GetEntryByName('Radiometric'))
            self.NodeTempLow = self.NodeTempLinearLow.GetValue()
            self.NodeIRFormat.SetIntValue(self.NodeTempLow)

        if not PySpin.IsAvailable(self.NodeBufferHandlingMode) or not PySpin.IsWritable(self.NodeBufferHandlingMode):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return False

        self.NodeNewestOnly = self.NodeBufferHandlingMode.GetEntryByName(
            'NewestOnly')
        if not PySpin.IsAvailable(self.NodeNewestOnly) or not PySpin.IsReadable(self.NodeNewestOnly):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return False

        self.NodeNewestOnlyMode = self.NodeNewestOnly.GetValue()
        self.NodeBufferHandlingMode.SetIntValue(self.NodeNewestOnlyMode)