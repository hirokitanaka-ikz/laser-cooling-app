import os
import PySpin
import numpy as np


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class IRFormatType:
    LINEAR_10MK = 1
    LINEAR_100MK = 2
    RADIOMETRIC = 3


class FlirController:

    ImageTemp = None

    def __init__(self) -> None:
        self.ContinueRecording = True
        self.IrType = IRFormatType.RADIOMETRIC
        self.IsConnected = False
    

    def is_connected(self) -> bool:
        return self.IsConnected


    def connect(self) -> bool:
        if self.IsConnected == False:
            self.System = PySpin.System.GetInstance()
            self.Version = self.System.GetLibraryVersion()
            print('Library version: %d.%d.%d.%d' % (self.Version.major,
                self.Version.minor, self.Version.type, self.Version.build))
            self.Cam_list = self.System.GetCameras()
            self.Num_cameras = self.Cam_list.GetSize()
            print('Number of cameras detected: %d' % self.Num_cameras)
            if self.Num_cameras == 0:

                # Clear camera list before releasing system
                self.Cam_list.Clear()

                # Release system instance
                self.System.ReleaseInstance()
                return False

            self.Camera = self.Cam_list[0]
            self.NodeMapTlDevice = self.Camera.GetTLDeviceNodeMap()
            self.Camera.Init()
            self.Nodemap = self.Camera.GetNodeMap()

            print('Camera connected')
            return True


    def disconnect(self):
        if self.IsConnected:
            self.Camera.EndAcquisition()
            self.Camera.DeInit()
            del self.Camera
            self.Cam_list.Clear()
            self.System.ReleaseInstance()
            print('Camera disconnected')
            self.IsConnected = False
    

    # def get_serial_number(self):
    #     return self.DeviceSerialNumber
    

    def get_emissivity(self):
        return self.Emiss


    def startStream(self):
        self.SetupCamera()

        print('*** IMAGE ACQUISITION ***\n')

        try:
            self.NodeAcquisitionMode = PySpin.CEnumerationPtr(
                self.Nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(self.NodeAcquisitionMode) or not PySpin.IsWritable(self.NodeAcquisitionMode):
                print(
                    'Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                return False

            self.NodeAcquisitionModeContinuous = self.NodeAcquisitionMode.GetEntryByName(
                'Continuous')
            if not PySpin.IsAvailable(self.NodeAcquisitionModeContinuous) or not PySpin.IsReadable(self.NodeAcquisitionModeContinuous):
                print(
                    'Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                return False

            self.AcquisitionModeContinuous = self.NodeAcquisitionModeContinuous.GetValue()
            self.NodeAcquisitionMode.SetIntValue(
                self.AcquisitionModeContinuous)
            print('Acquisition mode set to continuous...')

            self.Camera.BeginAcquisition()
            print('Acquiring images...')

            self.DeviceSerialNumber = ''
            self.NodeDeviceSerialNumber = PySpin.CStringPtr(
                self.NodeMapTlDevice.GetNode('DeviceSerialNumber'))
            if PySpin.IsAvailable(self.NodeDeviceSerialNumber) and PySpin.IsReadable(self.NodeDeviceSerialNumber):
                self.DeviceSerialNumber = self.NodeDeviceSerialNumber.GetValue()
                print('Device serial number retrieved as %s...' %
                      self.DeviceSerialNumber)

             # Retrieve Calibration details
            self.NodeCalibrationQueryR = PySpin.CFloatPtr(
                self.Nodemap.GetNode('R'))
            self.R = self.NodeCalibrationQueryR.GetValue()
            # print('R =', self.R)

            self.NodeCalibrationQueryB = PySpin.CFloatPtr(
                self.Nodemap.GetNode('B'))
            self.B = self.NodeCalibrationQueryB.GetValue()
            # print('B =', self.B)

            self.NodeCalibrationQueryF = PySpin.CFloatPtr(
                self.Nodemap.GetNode('F'))
            self.F = self.NodeCalibrationQueryF.GetValue()
            # print('F =', self.F)

            self.NodeCalibrationQueryX = PySpin.CFloatPtr(
                self.Nodemap.GetNode('X'))
            self.X = self.NodeCalibrationQueryX.GetValue()
            # print('X =', self.X)

            self.NodeCalibrationQueryA1 = PySpin.CFloatPtr(
                self.Nodemap.GetNode('alpha1'))
            self.A1 = self.NodeCalibrationQueryA1.GetValue()
            # print('alpha1 =', self.A1)

            self.NodeCalibrationQueryA2 = PySpin.CFloatPtr(
                self.Nodemap.GetNode('alpha2'))
            self.A2 = self.NodeCalibrationQueryA2.GetValue()
            # print('alpha2 =', self.A2)

            self.NodeCalibrationQueryB1 = PySpin.CFloatPtr(
                self.Nodemap.GetNode('beta1'))
            self.B1 = self.NodeCalibrationQueryB1.GetValue()
            # print('beta1 =', self.B1)

            self.NodeCalibrationQueryB2 = PySpin.CFloatPtr(
                self.Nodemap.GetNode('beta2'))
            self.B2 = self.NodeCalibrationQueryB2.GetValue()
            # print('beta2 =', self.B2)

            self.NodeCalibrationQueryJ1 = PySpin.CFloatPtr(
                self.Nodemap.GetNode('J1'))    # Gain
            self.J1 = self.NodeCalibrationQueryJ1.GetValue()
            # print('Gain =', self.J1)

            self.NodeCalibrationQueryJ0 = PySpin.CIntegerPtr(
                self.Nodemap.GetNode('J0'))   # Offset
            self.J0 = self.NodeCalibrationQueryJ0.GetValue()
            # print('Offset =', self.J0)

            if self.IrType == IRFormatType.RADIOMETRIC:
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
                # print('H20 =', self.H2O)

                self.Tau = self.X * np.exp(-np.sqrt(self.Dist) * (self.A1 + self.B1 * np.sqrt(self.H2O))) + (
                    1 - self. X) * np.exp(-np.sqrt(self.Dist) * (self.A2 + self.B2 * np.sqrt(self.H2O)))
                # print('tau =', self.Tau)

                # Pseudo radiance of the reflected environment
                self.r1 = ((1 - self.Emiss) / self.Emiss) * \
                    (self.R / (np.exp(self.B / self.TRefl) - self.F))
                # print('r1 =', self.r1)

                # Pseudo radiance of the atmosphere
                self.r2 = ((1 - self.Tau) / (self.Emiss * self.Tau)) * \
                    (self.R / (np.exp(self.B / self.TAtm) - self.F))
                # print('r2 =', self.r2)

                # Pseudo radiance of the external optics
                self.r3 = ((1 - self.ExtOpticsTransmission) / (self.Emiss * self.Tau *
                           self.ExtOpticsTransmission)) * (self.R / (np.exp(self.B / self.ExtOpticsTemp) - self.F))
                # print('r3 =', self.r3)

                self.K2 = self.r1 + self.r2 + self.r3
                # print('K2 =', self.K2)

            # self.fig = plt.figure(1)

            # self.takeImage()
            self.IsConnected = True

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return True


    def getImage(self):
        if self.IsConnected == True:
            try:
                self.ImageResult = self.Camera.GetNextImage(1000)
                if self.ImageResult.IsIncomplete():
                    print('Image incomplete with image status %d ...' %
                            self.ImageResult.GetImageStatus())
                else:
                    self.ImageData = self.ImageResult.GetNDArray()

                    if self.IrType == IRFormatType.LINEAR_10MK:
                        self.ImageTempCelsiusHigh = (
                            self.ImageData * 0.01) - 273.15
                        # plt.imshow(self.ImageTempCelsiusHigh,
                        #    cmap='inferno', aspect='auto')
                        # plt.colorbar(format='%.2f')

                    elif self.IrType == IRFormatType.LINEAR_10MK:
                        self.ImageTempCelsiusLow = (
                            self.ImageData * 0.1) - 273.15
                        # plt.imshow(self.ImageTempCelsiusLow,
                        #    cmap='inferno', aspect='auto')
                        # plt.colorbar(format='%.2f')
                    elif self.IrType == IRFormatType.RADIOMETRIC:
                        self.ImageRadiance = (
                            self.ImageData - self.J0) / self.J1
                        self.ImageTemp = (
                            self.B / np.log(self.R / ((self.ImageRadiance / self.Emiss / self.Tau) - self.K2) + self.F)) - 273.15
                        # plt.imshow(self.ImagaeTemp,
                        #    cmap='inferno', aspect='auto')
                        # plt.colorbar(format='%.2f')
                # plt.pause(0.001)
                # plt.clf()
                self.ImageResult.Release()
                return self.ImageTemp
                # break
            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False


    def SetupCamera(self):
        self.StreamNodeMap = self.Camera.GetTLStreamNodeMap()
        self.NodeBufferHandlingMode = PySpin.CEnumerationPtr(
            self.StreamNodeMap.GetNode('StreamBufferHandlingMode'))
        self.NodePixelFormat = PySpin.CEnumerationPtr(
            self.Nodemap.GetNode('PixelFormat'))
        self.NodePixelFormatMono16 = PySpin.CEnumEntryPtr(
            self.NodePixelFormat.GetEntryByName('Mono16'))
        self.PixelFormatMono16 = self.NodePixelFormatMono16.GetValue()
        self.NodePixelFormat.SetIntValue(self.PixelFormatMono16)
        if self.IrType == IRFormatType.LINEAR_10MK:
            self.NodeIRFormat = PySpin.CEnumerationPtr(
                self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearHigh = PySpin.CEnumEntryPtr(
                self.NodeIRFormat.GetEntryByName('TemperatureLinear10mK'))
            self.NodeTempHigh = self.NodeTempLinearHigh.GetValue()
            self.NodeIRFormat.SetIntValue(self.NodeTempHigh)
        if self.IrType == IRFormatType.LINEAR_100MK:
            self.NodeIRFormat = PySpin.CEnumerationPtr(
                self.Nodemap.GetNode('IRFormat'))
            self.NodeTempLinearLow = PySpin.CEnumEntryPtr(
                self.NodeIRFormat.GetEntryByName('TemperatureLinear100mK'))
            self.NodeTempLow = self.NodeTempLinearLow.GetValue()
            self.NodeIRFormat.SetIntValue(self.NodeTempLow)
        if self.IrType == IRFormatType.RADIOMETRIC:
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
