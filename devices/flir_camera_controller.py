import os
import PySpin
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class IRFormatType:
    LINEAR_10MK = 1
    LINEAR_100MK = 2
    RADIOMETRIC = 3


class FlirCameraController:

    ImageTemp = None

    def __init__(self) -> None:
        # self.ContinueRecording = True
        self._ir_type = IRFormatType.RADIOMETRIC
        self._is_connected = False
    
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected


    def connect(self):
        if self._is_connected == False:
            try:
                self.system = PySpin.system.GetInstance()
                self._cam_list = self.system.GetCameras()
                num_cameras = self._cam_list.GetSize()
                logging.info(f"Number of cameras detected: {num_cameras}")
                if num_cameras == 0:
                    self._cam_list.Clear()
                    self.system.ReleaseInstance()
                self.camera = self._cam_list[0]
                self.NodeMapTlDevice = self.camera.GetTLDeviceNodeMap()
                self.camera.Init()
                self.Nodemap = self.camera.GetNodeMap()
                self._is_connected = True
                logging.info("FLIR camera connected")
            except Exception as e:
                logging.error(f"Failed to connect: {e}")
                self.system.ReleaseInstance()


    def disconnect(self):
        try:
            if self._is_connected:
                self.camera.EndAcquisition()
                self.camera.DeInit()
                del self.camera
            self._cam_list.Clear()
            self.system.ReleaseInstance()
            logging.info("FLIR camera disconnected")
        except Exception as e:
            logging.error(f"Failed to disconnect camera: {e}")
            self._is_connected = False


    @property
    def version(self) -> str:
        try:
            version = self.system.GetLibraryversion()
            version_string = f"{version.major}, {version.minor}, {version.type}, {version.build}"
            return version_string
        except Exception as e:
            logging.error("Failed to read version: {e}")
            return ""
    

    @property
    def camera_list(self) -> list:
        pass


    @property
    def emissivity(self) -> float:
        return self.Emiss


    def start_stream(self):
        self.setup_camera()
        logging.info("Image acquisition set up...")

        try:
            self.NodeAcquisitionMode = PySpin.CEnumerationPtr(
                self.Nodemap.GetNode('AcquisitionMode'))
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

            self.camera.BeginAcquisition()
            
            self.DeviceSerialNumber = ''
            self.NodeDeviceSerialNumber = PySpin.CStringPtr(self.NodeMapTlDevice.GetNode('DeviceSerialNumber'))
            if PySpin.IsAvailable(self.NodeDeviceSerialNumber) and PySpin.IsReadable(self.NodeDeviceSerialNumber):
                self.DeviceSerialNumber = self.NodeDeviceSerialNumber.GetValue()
                logging.info(f"Device serial number retrieved as {self.DeviceSerialNumber}")

             # Retrieve Calibration details
            self.NodeCalibrationQueryR = PySpin.CFloatPtr(self.Nodemap.GetNode('R'))
            self.R = self.NodeCalibrationQueryR.GetValue()

            self.NodeCalibrationQueryB = PySpin.CFloatPtr(self.Nodemap.GetNode('B'))
            self.B = self.NodeCalibrationQueryB.GetValue()

            self.NodeCalibrationQueryF = PySpin.CFloatPtr(self.Nodemap.GetNode('F'))
            self.F = self.NodeCalibrationQueryF.GetValue()

            self.NodeCalibrationQueryX = PySpin.CFloatPtr(self.Nodemap.GetNode('X'))
            self.X = self.NodeCalibrationQueryX.GetValue()

            self.NodeCalibrationQueryA1 = PySpin.CFloatPtr(self.Nodemap.GetNode('alpha1'))
            self.A1 = self.NodeCalibrationQueryA1.GetValue()

            self.NodeCalibrationQueryA2 = PySpin.CFloatPtr(self.Nodemap.GetNode('alpha2'))
            self.A2 = self.NodeCalibrationQueryA2.GetValue()

            self.NodeCalibrationQueryB1 = PySpin.CFloatPtr(self.Nodemap.GetNode('beta1'))
            self.B1 = self.NodeCalibrationQueryB1.GetValue()

            self.NodeCalibrationQueryB2 = PySpin.CFloatPtr(self.Nodemap.GetNode('beta2'))
            self.B2 = self.NodeCalibrationQueryB2.GetValue()

            self.NodeCalibrationQueryJ1 = PySpin.CFloatPtr(self.Nodemap.GetNode('J1'))
            self.J1 = self.NodeCalibrationQueryJ1.GetValue()

            self.NodeCalibrationQueryJ0 = PySpin.CIntegerPtr(self.Nodemap.GetNode('J0'))
            self.J0 = self.NodeCalibrationQueryJ0.GetValue()

            if self._ir_type == IRFormatType.RADIOMETRIC:
                self.Emiss = 0.97
                self.TRefl = 293.15
                self.TAtm = 293.15
                self.TAtmC = self.TAtm - 273.15
                self.Humidity = 0.55
                self.Dist = 2
                self.ExtOpticsTransmission = 1
                self.ExtOpticsTemp = self.TAtm
                self.H2O = self.Humidity * np.exp(1.5587 + 0.06939 * self.TAtmC - 0.00027816 *
                                                  self.TAtmC * self.TAtmC + 0.00000068455 * self.TAtmC * self.TAtmC * self.TAtmC)
                self.Tau = self.X * np.exp(-np.sqrt(self.Dist) * (self.A1 + self.B1 * np.sqrt(self.H2O))) + (
                    1 - self. X) * np.exp(-np.sqrt(self.Dist) * (self.A2 + self.B2 * np.sqrt(self.H2O)))
                # Pseudo radiance of the reflected environment
                self.r1 = ((1 - self.Emiss) / self.Emiss) * \
                    (self.R / (np.exp(self.B / self.TRefl) - self.F))
                # Pseudo radiance of the atmosphere
                self.r2 = ((1 - self.Tau) / (self.Emiss * self.Tau)) * \
                    (self.R / (np.exp(self.B / self.TAtm) - self.F))
                # Pseudo radiance of the external optics
                self.r3 = ((1 - self.ExtOpticsTransmission) / (self.Emiss * self.Tau *
                           self.ExtOpticsTransmission)) * (self.R / (np.exp(self.B / self.ExtOpticsTemp) - self.F))
                self.K2 = self.r1 + self.r2 + self.r3
            self._is_connected = True # necessary?
            logging.info("Camera started streaming")

        except PySpin.SpinnakerException as e:
            logging.error(f"Failed to start streaming: {e}")


    def get_image(self):
        if self._is_connected == True:
            try:
                self.ImageResult = self.camera.GetNextImage(1000)
                if self.ImageResult.IsIncomplete():
                    print('Image incomplete with image status %d ...' %
                            self.ImageResult.GetImageStatus())
                else:
                    self.ImageData = self.ImageResult.GetNDArray()

                    if self._ir_type == IRFormatType.LINEAR_10MK:
                        self.ImageTempCelsiusHigh = (
                            self.ImageData * 0.01) - 273.15
                    elif self._ir_type == IRFormatType.LINEAR_100MK:
                        self.ImageTempCelsiusLow = (
                            self.ImageData * 0.1) - 273.15
                    elif self._ir_type == IRFormatType.RADIOMETRIC:
                        self.ImageRadiance = (
                            self.ImageData - self.J0) / self.J1
                        self.ImageTemp = (
                            self.B / np.log(self.R / ((self.ImageRadiance / self.Emiss / self.Tau) - self.K2) + self.F)) - 273.15
                self.ImageResult.Release()
                return self.ImageTemp
            except PySpin.SpinnakerException as e:
                logging.error(f"Failed to get image: {e}")
                return None


    def setup_camera(self):
        self.StreamNodeMap = self.camera.GetTLStreamNodeMap()
        self.NodeBufferHandlingMode = PySpin.CEnumerationPtr(
            self.StreamNodeMap.GetNode('StreamBufferHandlingMode'))
        self.NodePixelFormat = PySpin.CEnumerationPtr(
            self.Nodemap.GetNode('PixelFormat'))
        self.NodePixelFormatMono16 = PySpin.CEnumEntryPtr(
            self.NodePixelFormat.GetEntryByName('Mono16'))
        self.PixelFormatMono16 = self.NodePixelFormatMono16.GetValue()
        self.NodePixelFormat.SetIntValue(self.PixelFormatMono16)
        if self._ir_type == IRFormatType.LINEAR_10MK:
            self.NodeIRFormat = PySpin.CEnumerationPtr(
                self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearHigh = PySpin.CEnumEntryPtr(
                self.NodeIRFormat.GetEntryByName('TemperatureLinear10mK'))
            self.NodeTempHigh = self.NodeTempLinearHigh.GetValue()
            self.NodeIRFormat.SetIntValue(self.NodeTempHigh)
        if self._ir_type == IRFormatType.LINEAR_100MK:
            self.NodeIRFormat = PySpin.CEnumerationPtr(
                self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearLow = PySpin.CEnumEntryPtr(
                self.NodeIRFormat.GetEntryByName('TemperatureLinear100mK'))
            self.NodeTempLow = self.NodeTempLinearLow.GetValue()
            self.NodeIRFormat.SetIntValue(self.NodeTempLow)
        if self._ir_type == IRFormatType.RADIOMETRIC:
            self.NodeIRFormat = PySpin.CEnumerationPtr(
                self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearLow = PySpin.CEnumEntryPtr(
                self.NodeIRFormat.GetEntryByName('Radiometric'))
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