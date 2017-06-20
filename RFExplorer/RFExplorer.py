#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments, duplicate-code

#============================================================================
#RF Explorer Python Libraries - A Spectrum Analyzer for everyone!
#Copyright © 2010-16 Ariel Rocholl, www.rf-explorer.com
#
# Contributed by:
# 
#       Julian Calderon
#
#This application is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 3.0 of the License, or (at your option) any later version.
#
#This software is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.
#
#You should have received a copy of the GNU General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#=============================================================================

import queue
import threading
import time
import math
from datetime import datetime, timedelta
import serial.tools.list_ports
import serial

#---------------------------------------------------------

from RFExplorer import RFE_Common 
from RFExplorer.ReceiveSerialThread import ReceiveSerialThread
from RFExplorer.RFESweepData import RFESweepData
from RFExplorer.RFESweepDataCollection import RFESweepDataCollection
from RFExplorer.RFEConfiguration import RFEConfiguration
from RFExplorer.RFEAmplitudeTableData import RFEAmplitudeTableData
from RFExplorer.RFE6GEN_CalibrationData import RFE6GEN_CalibrationData

#---------------------------------------------------------

def Convert_mW_2_dBm(mW):
    """Convert mw to dBm

    Parameters:
        mW -- Value in mW
    Returns:
        Float Value in dBm
    """
    return (10.0 * math.log10(mW))

def Convert_Watt_2_dBm(Watt):
    """Convert Watt to dBm

    Parameters:
        Watt -- Value in Watt
    Returns:
        Float Value in dBm
    """
    return (30.0 + Convert_mW_2_dBm(Watt))

def Convert_dBm_2_dBuV(dBm):
    """Convert dBm to dBuV
    
    Parameters:
        dBm -- Value in dBm
    Returns:
        Float Value in dBuV
	"""
    return (dBm + 107.0)

def Convert_dBuV_2_dBm(dBuV):
    """Convert dBuV to dBm
    
    Parameters:
        dBuV -- Value in dBuV
    Returns:
        Float Value in dBm
	"""
    return (dBuV - 107.0)

def Convert_dBm_2_mW(dBm):
    """Convert dBm to mW
    
    Parameters:
        dBm -- Value in dBm
    Returns:
        Float Value in mW
	"""
    return (math.pow(10, dBm / 10.0))

def Convert_dBm_2_Watt(dBm):
    """Convert dBm to Watt
    
    Parameters:
        dBm -- Value in dBm
    Returns:
        Float Value in Watt
	"""
    return (Convert_dBm_2_mW(dBm) / 1000.0)

def DecorateSerialNumberRAWString(sRAWSerialNumber):
    """This function gives format to the serial number string as xxxx-xxxx-xxxx-xxxx 

    Parameters:
        sRAWSerialNumber -- Original serial number format
    Returns:
        String changed serial number format
    """
    if (sRAWSerialNumber and len(sRAWSerialNumber) >= 16):
        return (sRAWSerialNumber[:4] + "-" + sRAWSerialNumber[4:8] + "-" + sRAWSerialNumber[8:12] + "-" + sRAWSerialNumber[12:16])
    else:
        return ""

g_arrModels = ["UNKWN"] * 256
g_arrModels[RFE_Common.eModel.MODEL_433.value] = "433M"
g_arrModels[RFE_Common.eModel.MODEL_868.value] = "868M"
g_arrModels[RFE_Common.eModel.MODEL_915.value] = "915M"
g_arrModels[RFE_Common.eModel.MODEL_WSUB1G.value] = "WSUB1G"
g_arrModels[RFE_Common.eModel.MODEL_2400.value] = "2.4G"
g_arrModels[RFE_Common.eModel.MODEL_WSUB3G.value] = "WSUB3G"
g_arrModels[RFE_Common.eModel.MODEL_6G.value] = "6G"
g_arrModels[RFE_Common.eModel.MODEL_RFGEN.value] = "RFE6GEN"
g_arrModels[RFE_Common.eModel.MODEL_NONE.value] = "NONE"

def GetModelTextFromEnum(model):
    """Returns a human readable and normalized identifier text for the model specified in the enum

    Parameters:
        model -- RFExplorer model
    Returns:
	    String text identifier such as 433M or WSUB1G
	"""
    return g_arrModels[model]

def GetModelEnumFromText(sText):
    """Returns model enumerator based on text provided

    Parameters:
        sText -- One of "433M", "868M", "915M", "WSUB1G", "2.4G", "WSUB3G", "6G"
    Returns:
        RFE_Common.eModel Valid model enumerator or will set to MODEL_NONE if not found
	"""
    eReturn = RFE_Common.eModel.MODEL_NONE

    for nInd in range(len(g_arrModels)):
        if (sText.upper() == g_arrModels[nInd]):
            eReturn = RFE_Common.eModel(nInd)
            break

    return eReturn

#---------------------------------------------------------

class RFECommunicator(object):    
    """Main API class to support all basic low level operations with RF Explorer
	"""
    def __init__(self):
        self.m_bAutoCleanConfig = True
        self.m_bUseByteBLOB = False
        self.m_bUseStringBLOB = False
        self.m_bAutoConfigure = True 
        self.m_arrConnectedPorts = []
        self.m_arrValidCP2102Ports = []
        self.m_nVerboseLevel = 1
        self.m_bIsResetEvent = False
        self.m_objSerialPort = serial.Serial()
        self.m_hQueueLock = threading.Lock()
        self.m_hSerialPortLock = threading.Lock()
        self.m_ReceivedBytesMutex = threading.Lock()
        self.m_bDisposed = False 
        self.m_fStartFrequencyMHZ = 0.0
        self.m_fStepFrequencyMHZ = 0.0
        self.m_fRefFrequencyMHZ = 0.0
        self.m_nFreqSpectrumSteps = 112  #$S byte buffer by default
        self.m_fOffset_dB = 0.0
        self.m_fThresholdDBM = 0.0
        self.m_fRBWKHZ = 0.0
        self.m_fRFGenStartFrequencyMHZ = 0.0
        self.m_fRFGenCWFrequencyMHZ = 0.0
        self.m_fRFGenStepFrequencyMHZ = 0.0
        self.m_fRFGenStopFrequencyMHZ = 0.0
        self.m_bRFGenStartHighPowerSwitch = False
        self.m_nRFGenSweepSteps = 1
        self.m_bRFGenHighPowerSwitch = False
        self.m_nRFGenStepWaitMS = 0
        self.m_nRFGenPowerLevel = 0
        self.m_nRFGenStopPowerLevel = 0
        self.m_bRFGenStopHighPowerSwitch = False
        self.m_bRFGenPowerON = False
        self.m_bPortConnected = False
        self.m_fMinSpanMHZ = 0.112      
        self.m_fPeakValueAmp = -120.0   
        self.m_fMaxSpanMHZ = 100.0      
        self.m_fMinFreqMHZ = 430.0       
        self.m_fMaxFreqMHZ = 440.0      
        self.m_fPeakValueMHZ = 0.0      
        self.m_fAmplitudeTopDBM = -30       #dBm for top graph limit
        self.m_bUseMaxHold = True
        self.m_nRFGenStartPowerLevel = 0
        #offset values read from spectrum analyzer calibration
        self.m_bMainboardInternalCalibrationAvailable = False
        self.m_bExpansionBoardInternalCalibrationAvailable = False
        self.m_arrSpectrumAnalyzerEmbeddedCalibrationOffsetDB = []
        self.m_arrSpectrumAnalyzerExpansionCalibrationOffsetDB = []
        self.m_fAmplitudeBottomDBM = RFE_Common.CONST_MIN_AMPLITUDE_DBM   #dBm for bottom graph limit
        self.m_eMode = RFE_Common.eMode.MODE_SPECTRUM_ANALYZER
        self.m_bStoreSweep = True
        self.m_LastCaptureTime = datetime(2000, 1, 1, 0, 0, 0, 000)
        self.m_spanAverageSpeedAcumulator = timedelta()
        self.m_fAverageSweepTime = 0.0
        self.m_nAverageSweepSpeedIterator = 0
        self.m_bAcknowledge = False 
        self.m_bIntendedAnalyzer = True     
        self.m_eDSP = RFE_Common.eDSP.DSP_AUTO
        self.m_sSerialNumber = ""
        self.m_sSweepInfoText = ""     
        self.m_eMainBoardModel = RFE_Common.eModel.MODEL_NONE
        self.m_eExpansionBoardModel = RFE_Common.eModel.MODEL_NONE 
        self.m_eCalculator = RFE_Common.eCalculator.NORMAL
        self.m_eActiveModel = RFE_Common.eModel.MODEL_NONE
        self.m_bExpansionBoardActive = False
        self.m_sSerialNumber = ""
        self.m_sExpansionSerialNumber = ""
        self.m_nBaudrate = 0
        self.m_bRunReceiveThread = True
        self.m_bHoldMode = False
        self.m_sDebugAllReceivedBytes = ""        #Debug string for all received bytes record.
        self.m_sRFExplorerFirmware = ""       #Detected firmware
        self.m_nRetriesCalibration = 0
        self.m_RFGenCal = RFE6GEN_CalibrationData()
        self.m_FileAmplitudeCalibration = RFEAmplitudeTableData()   #This variable contains the latest correction file loaded
        self.m_SweepDataContainer = RFESweepDataCollection(100 * 1024, True)
        self.m_objQueue = queue.Queue()
        self.m_objThread = ReceiveSerialThread(self, self.m_objQueue, self.m_objSerialPort, self.m_hQueueLock, self.m_hSerialPortLock)
        self.m_objThread.start()

    def __del__(self):
        #print("destructor called")
        self.Dispose(self)
        time.sleep(0.5)

    @property
    def AutoCleanConfig(self):
        """True if SweepData collection clean automatically, otherwise False
	    """
        return self.m_bAutoCleanConfig
    @AutoCleanConfig.setter
    def AutoCleanConfig(self, value):
        self.m_bAutoCleanConfig = value

    @property
    def RunReceiveThread(self):
        """True if thread is running, otherwise False 
	    """
        return self.m_bRunReceiveThread
    @RunReceiveThread.setter
    def RunReceiveThread(self, value):
        self.m_bRunReceiveThread = value

    @property
    def SweepData(self):
        """The main and only data collection with all the Sweep accumulated data
	    """
        return self.m_SweepDataContainer

    @property
    def IsResetEvent(self):
        """Reset string is detected. When is check in the get property, is set automatically to false. 
        We detect the last reset
	    """
        if(self.m_bIsResetEvent):
            self.m_bIsResetEvent = False
            return True
        else:
            return self.m_bIsResetEvent

    @property
    def VerboseLevel(self):
        """Debug trace level for print console messages 1-10 being 10 the most verbose
	    """
        return self.m_nVerboseLevel
    @VerboseLevel.setter
    def VerboseLevel(self, value):
        self.m_nVerboseLevel = value

    @property
    def Calculator(self):
        """Get the currently configured calculator in the device
	    """
        return self.m_eCalculator
    
    @property
    def UseByteBLOB(self):
        """Get/Set
	    """
        return self.m_bUseByteBLOB
    @UseByteBLOB.setter
    def UseByteBLOB(self, value):
        self.m_bUseByteBLOB = value

    @property
    def UseStringBLOB(self):
        """Get/Set
	    """
        return self.m_bUseStringBLOB
    @UseStringBLOB.setter
    def UseStringBLO(self, value):
        self.m_bUseStringBLOB = value

    @property
    def PortConnected(self):
        """Will be True while COM port is connected, as Serial.IsOpen() is not reliable
	    """
        return self.m_bPortConnected
    @PortConnected.setter
    def PortConnected(self, value):       
        self.m_bPortConnected = value

    @property
    def DebugAllReceivedBytes(self):
        """Debug string collection for all bytes received from device
		"""
        self.m_ReceivedBytesMutex.acquire()
        sReturn = self.m_sDebugAllReceivedBytes
        self.m_ReceivedBytesMutex.release()
        return sReturn

    @property
    def UseMaxHold(self):
        """True if Max Hold is used, otherwise False 
		"""
        return self.m_bUseMaxHold
    @UseMaxHold.setter
    def UseMaxHold(self, value):    
        if (value != self.m_bUseMaxHold):
            if (value):
                self.SendCommand_SetMaxHold()
            else:
                if (self.Calculator != RFE_Common.eCalculator.NORMAL):
                    self.SendCommand_Realtime() #avoid sending it again if already in normal mode
        self.m_bUseMaxHold = value

    @property
    def SweepInfoText(self):
        """Human readable text with time of last capture as well as average sweep time and sweeps / second
		"""
        return self.m_sSweepInfoText

    #Initializer for 433MHz model, will change later based on settings  
    @property
    def MinSpanMHZ(self):
        """Min valid span in MHZ for connected model
		""" 
        return self.m_fMinSpanMHZ
    @MinSpanMHZ.setter
    def MinSpanMHZ(self, value):
        self.m_fMinSpanMHZ = value

    @property
    def MaxSpanMHZ(self):
        """Max valid span in MHZ for connected model
		"""
        return self.m_fMaxSpanMHZ
    @MaxSpanMHZ.setter
    def MaxSpanMHZ(self, value):
        self.m_fMaxSpanMHZ = value

    @property
    def MinFreqMHZ(self):
        """Min valid frequency in MHZ for connected mode
		"""
        return self.m_fMinFreqMHZ
    @MinFreqMHZ.setter
    def MinFreqMHZ(self, value):
        self.m_fMinFreqMHZ = value

    @property
    def MaxFreqMHZ(self):
        """Max valid frequency in MHZ for connected model
		"""
        return self.m_fMaxFreqMHZ
    @MaxFreqMHZ.setter
    def MaxFreqMHZ(self, value):
        self.m_fMaxFreqMHZ = value

    @property
    def PeakValueMHZ(self):
        """Last drawing iteration peak value MHZ read
		"""
        return self.m_fPeakValueMHZ
    @PeakValueMHZ.setter
    def PeakValueMHZ(self, value):
        self.m_fPeakValueMHZ = value
    
    @property
    def PeakValueAmplitudeDBM(self):
        """Last drawing iteration peak value dBm read
		"""
        return self.m_fPeakValueAmp
    @PeakValueAmplitudeDBM.setter
    def PeakValueAmplitudeDBM(self, value):
        self.m_fPeakValueAmp = value
    
    @property
    def AmplitudeTopDBM(self):
        """This is the highest value that should be selected for display, includes Offset dBm
		"""
        return self.m_fAmplitudeTopDBM
    @AmplitudeTopDBM.setter
    def AmplitudeTopDBM(self, value):
        self.m_fAmplitudeTopDBM = value

    @property
    def AmplitudeTopNormalizedDBM(self):
        """AmplitudeTop property includes the offset dBm, the normalized one does not
		"""
        return self.m_fAmplitudeTopDBM - self.m_fOffset_dB
    @AmplitudeTopNormalizedDBM.setter
    def AmplitudeTopNormalizedDBM(self, value):
        self.m_fAmplitudeTopDBM = value + self.m_fOffset_dB

    @property
    def AmplitudeBottomDBM(self):
        """This is the lowest value that should be selected for display, includes Offset dBm
		"""
        return self.m_fAmplitudeBottomDBM
    @AmplitudeBottomDBM.setter
    def AmplitudeBottomDBM(self, value):
        self.m_fAmplitudeBottomDBM = value
    
    @property
    def AmplitudeBottomNormalizedDBM(self):
        """AmplitudeBottom property includes the offset dBm, the normalized one does not
		"""
        return self.m_fAmplitudeBottomDBM - self.m_fOffset_dB
    @AmplitudeBottomNormalizedDBM.setter
    def AmplitudeBottomNormalizedDBM(self, value):
        self.m_fAmplitudeBottomDBM = value + self.m_fOffset_dB

    #spectrum analyzer configuration
    @property
    def StartFrequencyMHZ(self):
        """Frequency in MHZ for the span start position, 
        used to calculate all other positions together with StepFrequencyMHZ
		"""
        return self.m_fStartFrequencyMHZ
    @StartFrequencyMHZ.setter
    def StartFrequencyMHZ(self, value):
        self.m_fStartFrequencyMHZ = value

    @property
    def StepFrequencyMHZ(self):
        """Analyzer sweep frequency step in MHZ
		"""
        return self.m_fStepFrequencyMHZ
    @StepFrequencyMHZ.setter
    def StepFrequencyMHZ(self, value):
        self.m_fStepFrequencyMHZ = value

    @property
    def StopFrequencyMHZ(self):
        """Calculated span stop frequency in MHZ
		"""
        return self.m_fStartFrequencyMHZ + self.m_fStepFrequencyMHZ * self.FreqSpectrumSteps
    
    @property
    def RFGenStartPowerLevel(self):
        """Get/Set amplitude sweep start value for Signal Generator Power Level (0-3)
		"""
        return self.m_nRFGenStartPowerLevel
    @RFGenStartPowerLevel.setter
    def RFGenStartPowerLevel(self, value):
        self.m_nRFGenStartPowerLevel = value

    @property
    def FreqSpectrumSteps(self):
        """$S byte buffer by default
		"""
        return self.m_nFreqSpectrumSteps
    @FreqSpectrumSteps.setter
    def FreqSpectrumSteps(self, value):
        self.m_nFreqSpectrumSteps = value 
    
    @property
    def RefFrequencyMHZ(self):
        """Reference frequency used for sniffer decoder and other zero span functions
		"""
        return self.m_fRefFrequencyMHZ 
    @RefFrequencyMHZ.setter
    def RefFrequencyMHZ(self, value):        
        self.m_fRefFrequencyMHZ = value

    #Signal generator configuration
    @property
    def RFGenStartFrequencyMHZ(self):
        """Get/Set Signal Generator sweep start frequency in MHZ.
		"""
        return self.m_fRFGenStartFrequencyMHZ
    @RFGenStartFrequencyMHZ.setter
    def RFGenStartFrequencyMHZ(self, value):
        self.m_fRFGenStartFrequencyMHZ = value

    @property
    def RFGenCWFrequencyMHZ(self):
        """Get/Set Signal Generator CW frequency in MHZ.
		"""
        return self.m_fRFGenCWFrequencyMHZ
    @RFGenCWFrequencyMHZ.setter
    def RFGenCWFrequencyMHZ(self, value):
        self.m_fRFGenCWFrequencyMHZ = value
    
    @property
    def RFGenStepFrequencyMHZ(self):
        """Get/Set Signal Generator sweep step frequency in MHZ.
		"""
        return self.m_fRFGenStepFrequencyMHZ
    @RFGenStepFrequencyMHZ.setter
    def RFGenStepFrequencyMHZ(self, value):
        self.m_fRFGenStepFrequencyMHZ = value

    @property    
    def RFGenStopFrequencyMHZ(self):
        """ Get/Set Signal Generator sweep stop frequency in MHZ.
		"""
        return self.m_fRFGenStopFrequencyMHZ
    @RFGenStopFrequencyMHZ.setter    
    def RFGenStopFrequencyMHZ(self, value):
        self.m_fRFGenStopFrequencyMHZ = value 
    
    @property
    def RFGenSweepSteps(self):
        """ Get/Set Signal Generator sweep steps with valid values in 2-9999.
		"""
        return self.m_nRFGenSweepSteps
    @RFGenSweepSteps.setter
    def RFGenSweepSteps(self, value): 
        self.m_nRFGenSweepSteps = value

    @property
    def RFGenStepWaitMS(self):  
        """ Get/Set Signal Generator sweep step wait delay in Milliseconds, with a limit of 65,535 max.
		"""
        return self.m_nRFGenStepWaitMS 
    @RFGenStepWaitMS.setter
    def RFGenStepWaitMS(self, value):  
        self.m_nRFGenStepWaitMS = value 

    @property
    def RFGenHighPowerSwitch(self):
        """ Get/Set Signal Generator High Power switch. 
        This is combined with RFGenHighPowerSwitch in order to define power level for a CW or Sweep command
		"""
        return self.m_bRFGenHighPowerSwitch
    @RFGenHighPowerSwitch.setter
    def RFGenHighPowerSwitch(self, value):
        self.m_bRFGenHighPowerSwitch = value

    @property
    def RFGenPowerLevel(self):
        """ Get/Set Signal Generator power level status (0-3). 
        This is combined with RFGenHighPowerSwitch in order to define power level for a CW or Sweep command
		"""
        return self.m_nRFGenPowerLevel
    @RFGenPowerLevel.setter
    def RFGenPowerLevel(self, value):      
        self.m_nRFGenPowerLevel = value

    @property
    def RFGenPowerON(self):
        """ Get/Set Signal Generator power on status.
		"""
        return self.m_bRFGenPowerON

    @property
    def RFGenStartHighPowerSwitch(self):
        """Get/Set amplitude sweep start value for Signal Generator High Power Switch
		"""
        return self.m_bRFGenStartHighPowerSwitch
    @RFGenStartHighPowerSwitch.setter
    def RFGenStartHighPowerSwitch(self, value):
        self.m_bRFGenStartHighPowerSwitch = value

    @property
    def RFGenStopHighPowerSwitch(self):
        """ Get/Set amplitude sweep stop value for Signal Generator High Power Switch
		"""
        return self.m_bRFGenStopHighPowerSwitch
    @RFGenStopHighPowerSwitch.setter
    def RFGenStopHighPowerSwitch(self, value):
        self.m_bRFGenStopHighPowerSwitch = value
    
    @property
    def RFGenStopPowerLevel(self):
        """ Get/Set amplitude sweep stop value for Signal Generator Power Level (0-3)
		"""
        return self.m_nRFGenStopPowerLevel
    @RFGenStopPowerLevel.setter
    def RFGenStopPowerLevel(self, value):
        self.m_nRFGenStopPowerLevel = value

    @property
    def MainBoardModel(self):
        """The RF model installed in main board
		"""
        return self.m_eMainBoardModel

    @property
    def ExpansionBoardActive(self):
        """True when the expansion board is active, false otherwise
		"""
        return self.m_bExpansionBoardActive
    
    @property
    def BaudRate(self):
        """Get/Set the baudrate for modulation modes such as Sniffer. Note it may be actual baudrate or sample rate depending on modulation type
		"""
        return self.m_nBaudrate
    @BaudRate.setter
    def BaudRate(self, value):    
        self.m_nBaudrate = value
    
    @property
    def Acknowledged(self):     
        """Everytime we check the acknowledge, it reset itself to false
		"""
        bTemp = self.m_bAcknowledge
        self.m_bAcknowledge = False
        return bTemp

    @property
    def ActiveModel(self):    
        """The model active, regardless being main or expansion board
		"""
        return self.m_eActiveModel

    @property
    def AmplitudeOffsetDB(self): 
        """Manual offset of the amplitude reading to compensate external adjustments
		"""
        return self.m_fOffset_dB
    @AmplitudeOffsetDB.setter
    def AmplitudeOffsetDB(self, value): 
        self.m_fOffset_dB = value

    @property
    def AutoConfigure(self): 
        """Auto configure is true by default and is used for the communicator to auto request config data to RFE upon port connection
		"""
        return self.m_bAutoConfigure
    @AutoConfigure.setter
    def AutoConfigure(self, value): 
        self.m_bAutoConfigure = value

    @property
    def ExpansionBoardModel(self): 
        """The RF model installed in the expansion board
		"""
        return self.m_eExpansionBoardModel

    @property
    def ExpansionSerialNumber(self): 
        """Serial number for the expansion board, if any.
		"""    
        if (not self.m_bPortConnected):
            self.m_sExpansionSerialNumber = ""
        return DecorateSerialNumberRAWString(self.m_sExpansionSerialNumber)

    @property
    def HoldMode(self): 
        """Get or Set Hold mode state
		"""
        return self.m_bHoldMode
    @HoldMode.setter
    def HoldMode(self, value):
        self.m_bHoldMode = value

    @property
    def FirmwareCertified(self):
        """The currently certified firmware
		"""
        return RFE_Common.CONST_RFEXPLORER_FIRMWARE_CERTIFIED

    @property
    def Mode(self):
        """Get the current operational mode 
		"""
        return self.m_eMode

    @property
    def PortName(self):
        """String for name of COM Port
		"""
        return self.m_objSerialPort.port 
        
    @property
    def RBW_KHZ(self):
        """RBW in KHZ currently in use, both in analyzer and sniffer
		"""        
        return self.m_fRBWKHZ

    @property
    def RFExplorerFirmwareDetected(self):
        """Get detected firmware, otherwise "N/A" 
		"""
        if (not self.m_sRFExplorerFirmware):
            return "N/A"
        else:
            return self.m_sRFExplorerFirmware

    @property
    def SerialNumber(self):
        """Serial number for the device (main board)
		"""    
        if (not self.m_bPortConnected):
            self.m_sSerialNumber = ""

        return DecorateSerialNumberRAWString(self.m_sSerialNumber)

    @property
    def StoreSweep(self):
        """It gets or sets the capacity to store multiple historical sweep data in the <see cref>SweepData</ref> collection
		"""
        return self.m_bStoreSweep
    @StoreSweep.setter
    def StoreSweep(self, value):      
        self.m_bStoreSweep = value
    
    @property
    def ThresholdDBM(self):
        """Threshold in dBm used for alarm, sniffer capture, etc
		"""    
        return self.m_fThresholdDBM
    @ThresholdDBM.setter
    def ThresholdDBM(self, value):
        self.m_fThresholdDBM = value

    def ProcessReceivedString(self, bProcessAllEvents):
        """Processes all strings received and queued by the ReceiveThreadFunc.

        Parameters:
            bProcessAllEvents -- If this is False then only one event will be processed, otherwise will do all that are waiting on the queue
        Returns:
            Boolean Returns true if an event was received requiring redraw
            String the last processed string from the queue
		"""
        bDraw = False
        sReceivedString = ""

        if(self.m_bPortConnected):
            try:     
                nCount = 1   
                while(bProcessAllEvents and nCount > 0):
                    bWrongFormat = False
                    objNew = None
                    try:
                        self.m_hQueueLock.acquire() 
                        nCount = self.m_objQueue.qsize()
                        if (nCount == 0): 
                            break
                        objNew = self.m_objQueue.get_nowait()                       
                    except Exception as obEx:
                        if self.m_nVerboseLevel>0: 
                            print("m_arrReceivedStrings processing: " + str(obEx))
                    finally:
                        self.m_hQueueLock.release()

                    if (isinstance(objNew, RFEConfiguration)):
                        objConfiguration = objNew
                        if self.m_nVerboseLevel>4: 
                            print("Received configuration: " + objConfiguration.LineString)

                        if (self.IsGenerator()):
                            #it is a signal generator
                            if (self.m_RFGenCal.GetCalSize() < 0):
                                #request internal calibration data, if available
                                if (self.m_nRetriesCalibration < 3):
                                    self.SendCommand("Cq")
                                    self.m_nRetriesCalibration += 1
                            #signal generator
                            self.m_eMode = objConfiguration.Mode
                            self.m_bRFGenPowerON = objConfiguration.bRFEGenPowerON
                            if (self.m_eMode == RFE_Common.eMode.MODE_GEN_CW):
                                self.RFGenCWFrequencyMHZ = objConfiguration.fRFEGenCWFreqMHZ
                                self.RFGenStepFrequencyMHZ = objConfiguration.fStepMHZ
                                self.RFGenPowerLevel = objConfiguration.nRFEGenPowerLevel
                                self.RFGenHighPowerSwitch = objConfiguration.bRFEGenHighPowerSwitch

                            elif(self.m_eMode == RFE_Common.eMode.MODE_GEN_SWEEP_FREQ):
                                self.RFGenStartFrequencyMHZ = objConfiguration.fStartMHZ
                                self.RFGenStepFrequencyMHZ = objConfiguration.fStepMHZ
                                self.RFGenSweepSteps = objConfiguration.nFreqSpectrumSteps
                                self.RFGenStopFrequencyMHZ = self.RFGenStartFrequencyMHZ + self.RFGenSweepSteps * self.RFGenStepFrequencyMHZ
                                self.RFGenPowerLevel = objConfiguration.nRFEGenPowerLevel
                                self.RFGenHighPowerSwitch = objConfiguration.bRFEGenHighPowerSwitch
                                self.RFGenStepWaitMS = objConfiguration.nRFEGenSweepWaitMS
                            elif(self.m_eMode == RFE_Common.eMode.MODE_GEN_SWEEP_AMP):
                                self.RFGenCWFrequencyMHZ = objConfiguration.fRFEGenCWFreqMHZ
                                self.RFGenStartHighPowerSwitch = objConfiguration.bRFEGenStartHighPowerSwitch
                                self.RFGenStartPowerLevel = objConfiguration.nRFEGenStartPowerLevel
                                self.RFGenStopHighPowerSwitch = objConfiguration.bRFEGenStopHighPowerSwitch
                                self.RFGenStopPowerLevel = objConfiguration.nRFEGenStopPowerLevel
                                self.RFGenStepWaitMS = objConfiguration.nRFEGenSweepWaitMS
                            elif(self.m_eMode == RFE_Common.eMode.MODE_NONE):
                                if (objConfiguration.fStartMHZ > 0):
                                    #if RFE_Common.eMode.MODE_NONE and fStartMHZ has some meaningful value, it means
                                    #we are receiving a C3-* full status update
                                    self.RFGenCWFrequencyMHZ = objConfiguration.fRFEGenCWFreqMHZ
                                    self.RFGenHighPowerSwitch = objConfiguration.bRFEGenHighPowerSwitch
                                    self.RFGenStartFrequencyMHZ = objConfiguration.fStartMHZ
                                    self.RFGenStepFrequencyMHZ = objConfiguration.fStepMHZ
                                    self.RFGenSweepSteps = objConfiguration.nFreqSpectrumSteps
                                    self.RFGenStopFrequencyMHZ = self.RFGenStartFrequencyMHZ + self.RFGenSweepSteps * self.RFGenStepFrequencyMHZ
                                    self.RFGenPowerLevel = objConfiguration.nRFEGenPowerLevel
                                    self.RFGenStartHighPowerSwitch = objConfiguration.bRFEGenStartHighPowerSwitch
                                    self.RFGenStartPowerLevel = objConfiguration.nRFEGenStartPowerLevel
                                    self.RFGenStopHighPowerSwitch = objConfiguration.bRFEGenStopHighPowerSwitch
                                    self.RFGenStopPowerLevel = objConfiguration.nRFEGenStopPowerLevel
                                    self.RFGenStepWaitMS = objConfiguration.nRFEGenSweepWaitMS
                                else:
                                    print("Unknown Signal Generator configuration received")

                            else:
                                pass

                            self.MinFreqMHZ = RFE_Common.CONST_RFGEN_MIN_FREQ_MHZ
                            self.MaxFreqMHZ = RFE_Common.CONST_RFGEN_MAX_FREQ_MHZ

                            self.m_eActiveModel = self.m_eMainBoardModel

                        else:
                            #it is an spectrum analyzer
                            if (self.m_arrSpectrumAnalyzerEmbeddedCalibrationOffsetDB):
                                #request internal calibration data, if available
                                if (self.m_nRetriesCalibration < 3):
                                    self.SendCommand("Cq")
                                    if (self.m_objSerialPort.baudrate < 115200):
                                        time.sleep(0.2)
                                    self.m_nRetriesCalibration += 1

                            self.m_eMode = objConfiguration.Mode

                            if (self.m_eMode != RFE_Common.eMode.MODE_SNIFFER):
                                if ((math.fabs(self.StartFrequencyMHZ - objConfiguration.fStartMHZ) >= 0.001) or 
                                        (math.fabs(self.StepFrequencyMHZ - objConfiguration.fStepMHZ) >= 0.001)):
                                    self.StartFrequencyMHZ = objConfiguration.fStartMHZ
                                    self.StepFrequencyMHZ = objConfiguration.fStepMHZ
                                    print("New Freq range - buffer cleared.")
                                self.AmplitudeTopDBM = objConfiguration.fAmplitudeTopDBM
                                self.AmplitudeBottomDBM = objConfiguration.fAmplitudeBottomDBM
                                self.FreqSpectrumSteps = objConfiguration.nFreqSpectrumSteps
                            self.m_bExpansionBoardActive = objConfiguration.bExpansionBoardActive
                            if (self.m_bExpansionBoardActive):
                                self.m_eActiveModel = self.m_eExpansionBoardModel
                            else:
                                self.m_eActiveModel = self.m_eMainBoardModel

                            if (self.m_eActiveModel == RFE_Common.eModel.MODEL_WSUB3G):
                                #If it is a MODEL_WSUB3G, make sure we use the MAX HOLD mode to account for proper DSP
                                self.m_eCalculator = objConfiguration.eCalculator
                                time.sleep(0.5) 
                                if (self.m_bUseMaxHold):
                                    if (self.m_eCalculator != RFE_Common.eCalculator.MAX_HOLD):
                                        print("Updated remote mode to Max Hold for reliable DSP calculations with fast signals")
                                        self.SendCommand_SetMaxHold()
                                else:
                                    if (self.m_eCalculator == RFE_Common.eCalculator.MAX_HOLD):
                                        print("Remote mode is not Max Hold, some fast signals may not be detected")
                                        self.SendCommand_Realtime()


                            if (objConfiguration.Mode == RFE_Common.eMode.MODE_SNIFFER):
                                self.m_nBaudrate = objConfiguration.nBaudrate
                                self.m_fThresholdDBM = objConfiguration.fThresholdDBM
                                self.m_fRefFrequencyMHZ = objConfiguration.fStartMHZ
                            else:
                                #spectrum analyzer
                                if ((math.fabs(self.StartFrequencyMHZ - objConfiguration.fStartMHZ) >= 0.001) or
                                        (math.fabs(self.StepFrequencyMHZ - objConfiguration.fStepMHZ) >= 0.001)):
                                    self.StartFrequencyMHZ = objConfiguration.fStartMHZ
                                    self.StepFrequencyMHZ = objConfiguration.fStepMHZ
                                    print("New Freq range - buffer cleared.")
                                self.AmplitudeTopDBM = objConfiguration.fAmplitudeTopDBM
                                self.AmplitudeBottomDBM = objConfiguration.fAmplitudeBottomDBM
                                self.FreqSpectrumSteps = objConfiguration.nFreqSpectrumSteps
                                if (self.m_eActiveModel == RFE_Common.eModel.MODEL_WSUB3G):
                                    #If it is a MODEL_WSUB3G, make sure we use the MAX HOLD mode to account for proper DSP
                                    self.m_eCalculator = objConfiguration.eCalculator
                                    time.sleep(0.5)
                                    if (self.m_bUseMaxHold):
                                        if (self.m_eCalculator != RFE_Common.eCalculator.MAX_HOLD):
                                            print("Updated remote mode to Max Hold for reliable DSP calculations with fast signals")
                                            self.SendCommand_SetMaxHold()
                                    else:
                                        if (self.m_eCalculator == RFE_Common.eCalculator.MAX_HOLD):
                                            print("Remote mode is not Max Hold, some fast signals may not be detected")
                                            self.SendCommand_Realtime()

                                self.MinFreqMHZ = objConfiguration.fMinFreqMHZ
                                self.MaxFreqMHZ = objConfiguration.fMaxFreqMHZ
                                self.MaxSpanMHZ = objConfiguration.fMaxSpanMHZ

                                self.m_fOffset_dB = objConfiguration.fOffset_dB
                                self.m_fRBWKHZ = objConfiguration.fRBWKHZ
                                self.FreqSpectrumSteps = objConfiguration.nFreqSpectrumSteps

                                if ((self.m_eActiveModel == RFE_Common.eModel.MODEL_2400)
                                        or (self.m_eActiveModel == RFE_Common.eModel.MODEL_6G)):
                                    self.MinSpanMHZ = 2.0
                                else:
                                    self.MinSpanMHZ = 0.001 * self.FreqSpectrumSteps
                            if(self.AutoCleanConfig):
                                #print("count before clean:(ProcessReceivedString): " + str(self.m_SweepDataContainer.Count))
                                self.m_SweepDataContainer.CleanAll()
                                #print("count after clean:(ProcessReceivedString): " + str(self.m_SweepDataContainer.Count))
                    #Check if Sweep data case
                    elif (isinstance(objNew, RFESweepData)):
                        if (self.m_eMode != RFE_Common.eMode.MODE_TRACKING):
                            if (not self.m_bHoldMode):
                                objSweep = objNew
                                if (not self.m_bStoreSweep):
                                    self.m_SweepDataContainer.CleanAll()
                                self.m_SweepDataContainer.Add(objSweep)
                                #print("Added sweep " + str(self.m_SweepDataContainer.Count))

                                bDraw = True
                                if (self.m_SweepDataContainer.IsFull()):
                                    self.m_bHoldMode = True
                                    print("RAM Buffer is full.")
                                self.m_sSweepInfoText = "Captured:" + str(objSweep.CaptureTime) + " - Data points:" + str(objSweep.TotalSteps)
                                objSpan = objSweep.CaptureTime - self.m_LastCaptureTime  
                                if (objSpan.seconds < 60):
                                    #if time between captures is less than 60
                                    #seconds, we can assume we are getting
                                    #realtime data
                                    #and therefore can provide average
                                    #sweep/seconds information, otherwise we
                                    #were in hold or something
                                    #and data could not be used for these
                                    #calculations.
                                    self.m_nAverageSweepSpeedIterator += 1
                                    self.m_spanAverageSpeedAcumulator += (objSweep.CaptureTime - self.m_LastCaptureTime)
                                    if (self.m_fAverageSweepTime > 0.0):
                                        self.m_sSweepInfoText += "\nSweep time: " + str(self.m_fAverageSweepTime) + " seconds"
                                        if (self.m_fAverageSweepTime < 1.0):
                                            self.m_sSweepInfoText += " - Avg Sweeps/second: " + str((1.0 / self.m_fAverageSweepTime)) #add this only for fast, short duration scans
                                    if (self.m_nAverageSweepSpeedIterator >= 10):
                                        self.m_fAverageSweepTime = self.m_spanAverageSpeedAcumulator.seconds / self.m_nAverageSweepSpeedIterator
                                        self.m_nAverageSweepSpeedIterator = 0
                                        self.m_spanAverageSpeedAcumulator = self.m_LastCaptureTime - self.m_LastCaptureTime #set it to zero and start average all over again
                                self.m_LastCaptureTime = objSweep.CaptureTime
                            else:
                                #if in hold mode, we just record last time came
                                #here to make sure we start from most reliable
                                #point in time
                                self.m_LastCaptureTime = datetime.now()  
                    #Nothing specific, so just consider individual cases
                    else:
                        sLine = str(objNew)
                        sReceivedString = sLine
                        if ((len(sLine) > 3) and (sLine[:4] == RFE_Common.CONST_ACKNOWLEDGE)):
                            self.m_bAcknowledge = True
                        elif ((len(sLine) > 4) and (sLine[:4] == "DSP:")):
                            self.m_eDSP = RFE_Common.eDSP(int(sLine[4:5]))
                            print("DSP mode: " + str(self.m_eDSP))
                        elif ((len(sLine) > 16) and (sLine[:3] == "#Sn")):
                            self.m_sSerialNumber = sLine[3:19]
                            print("Device serial number: " + self.m_sSerialNumber)
                        elif ((len(sLine) > 5) and sLine[:6] == "#C2-M:"):
                            print("Received RF Explorer device model info:" + sLine)
                            self.m_eMainBoardModel = RFE_Common.eModel(int(sLine[6:9]))
                            self.m_eExpansionBoardModel = RFE_Common.eModel(int(sLine[10:13]))
                            self.m_sRFExplorerFirmware = sLine[14:19]
                        elif ((len(sLine) > 5) and sLine[:6] == "#C3-M:"):
                            print("Received RF Explorer Generator device info:" + sLine)
                            self.m_eMainBoardModel = RFE_Common.eModel(int(sLine[6:9]))
                            self.m_eExpansionBoardModel = RFE_Common.eModel(int(sLine[10:13]))
                            self.m_sRFExplorerFirmware = sLine[14:19]

                        # RFE6GEN calibration data '$q' message
                        elif ( (len(sLine) >= 164) and (sLine[:2] == '$q') ):
                            sReport = self.m_RFGenCal.InitializeCal( len(sLine), sLine, "" )
                            if ( sReport == "" ):
                                print("Invalid calibration data!")
                            else:
                                print("RFE6GEN calibration data:\n" + sReport)

                        elif ((len(sLine) > 18) and (sLine[:18] == RFE_Common.CONST_RESETSTRING)):
                            #RF Explorer device was reset for some reason, reconfigure client based on new configuration
                            self.m_bIsResetEvent = True
                        elif ((len(sLine) > 2) and (sLine[:2] == "$S") and (self.StartFrequencyMHZ > 0.1)):
                            bWrongFormat = True
                        elif ((len(sLine) > 5) and (sLine.startswith("#C4-F:"))):
                            bWrongFormat = True     #parsed on the thread
                        elif ((len(sLine) > 5) and (sLine[:6] == "#C2-F:")):
                            bWrongFormat = True     #parsed on the thread
                        elif ((len(sLine) > 5) and (sLine[:6] == "#C1-F:")):
                            bWrongFormat = True     #obsolete firmware
                        else:
                            print(sLine)  #report any line we don't understand - it is likely a human readable message
                        if (bWrongFormat):
                            print("Received unexpected data from RFExplorer device:" + sLine)
                            print("Please update your RF Explorer to a recent firmware version and")
                            print("make sure you are using the latest version of RF Explorer for Windows.")
                            print("Visit http://www.rf-explorer/download for latest firmware updates.")


            except Exception as obEx:
                #print("ProcessReceivedString: " + sReceivedString + '\n' + str(obEx))
                print("ProcessReceivedString: " + str(obEx))

        return bDraw, sReceivedString
    
    def SendCommand_Realtime(self):
        """Set RF Explorer SA devince in Calculator:Normal, this is useful to
        minimize spikes and spurs produced by unwanted signals
		"""
        self.SendCommand("C+\x00")
    
    def SendCommand_SetMaxHold(self):
        """Set RF Explorer SA device in Calculator:MaxHold, this is useful to capture fast transient signals even if the actual Windows application is representing other trace modes
		"""
        self.SendCommand("C+\x04")

    def CalculateCenterFrequencyMHZ(self):
        """Calculate Center Frequency in MHz 

        Returns:
            Float Center frequency in MHz
		"""
        return self.StartFrequencyMHZ + self.CalculateFrequencySpanMHZ() / 2.0

    def CalculateFrequencySpanMHZ(self):
        """Calculate Step Frequency in MHz 

        Returns:
            Float Span frequency in MHz
		"""
        return self.StepFrequencyMHZ * self.FreqSpectrumSteps

    def CalculateEndFrequencyMHZ(self):
        """Calculates the END or STOP frequency of the span, based on Start / Step values.

        Returns:
            Float end frequency in MHz
		"""
        return self.StartFrequencyMHZ + self.StepFrequencyMHZ * self.FreqSpectrumSteps

    def IsGenerator(self, bCheckModelAvailable=False):
        """True if is a generator, otherwise False

        Parameters:
            bCheckModelAvailable -- Use this to "true" in case you want to check actual model, not intended model if still not known - By default you will want this on "false"
        Returns:
            Boolean True if connected device is a generator, False otherwise
		"""
        if (not bCheckModelAvailable):
            if (self.MainBoardModel == RFE_Common.eModel.MODEL_NONE):
                return not self.m_bIntendedAnalyzer
            else:
                return self.MainBoardModel == RFE_Common.eModel.MODEL_RFGEN
        else:
            return self.MainBoardModel == RFE_Common.eModel.MODEL_RFGEN

    def IsAnalyzer(self, bCheckModelAvailable = False):
        """Check if the connected object is a Spectrum Analyzer device

        Parameters:
            bCheckModelAvailable -- Use this to "true" in case you want to check actual model, not intended model if still not known - By default you will want this on "false"
        Returns:
		    Boolean True if connected device is an analyzer, False otherwise
		"""
        if (not bCheckModelAvailable):
            return not self.IsGenerator()
        else:
            return (self.MainBoardModel != RFE_Common.eModel.MODEL_NONE)

    #region COM port low level details
    def GetConnectedPorts(self):
        """ Found the valid available serial port

        Returns:
            Boolean True if it found valid available serial port, False otherwise
		"""
        bOk = True
        sValidPorts = ""

        try:
            self.m_arrConnectedPorts = list(serial.tools.list_ports.comports())
            #print(str(len(self.m_arrConnectedPorts)))
            if(self.m_arrConnectedPorts):
                print("Detected COM ports:")
                for objPort in self.m_arrConnectedPorts:
                    print("  * " + objPort.device)

                for objPort in self.m_arrConnectedPorts:
                    if(self.IsConnectedPort(objPort.device)):
                        self.m_arrValidCP2102Ports.append(objPort)
                        print(objPort.device + " is a valid available port.")
                        sValidPorts += objPort.device + " "
                
                if(len(self.m_arrValidCP2102Ports) > 0):
                    print("RF Explorer Valid Ports found: " + str(len(self.m_arrValidCP2102Ports)) + " - " + sValidPorts)
                else:   
                    print("Error: not found valid COM Ports") 
                    bOk = False
            else: 
                print("Serial ports not detected")
                bOk = False
        except Exception as obEx:
            print("Error scanning COM ports: " + str(obEx))
            bOk = False   
        
        return bOk

    def IsConnectedPort(self, sPortName):
        """True if it is possible connect to specific port, otherwise False 
            
        Parameters:
            sPortName -- Serial port name, can take any form accepted by OS
        Returns:
            Boolean True if it is possible connect to specific port, otherwise False
		"""
        self.m_objSerialPort.baudrate = 500000
        self.m_objSerialPort.port = sPortName
        bOpen = False
        try:
            self.m_hSerialPortLock.acquire()
            self.m_objSerialPort.open()
        except Exception as obEx:
            print("Error in RFCommunicator - IsConnectedPort()" + str(obEx))
        finally:
            if(self.m_objSerialPort.is_open):
                bOpen = True
            self.m_objSerialPort.close()
            self.m_hSerialPortLock.release()

        return bOpen

    def ConnectPort(self, sUserPort, nBaudRate):
        """Connect serial port and start init sequence if AutoConfigure property is set. Connect automatically
        if sUserPort is None and there is only one available serial port, otherwise show an error message

        Parameters:
            sUserPort -- Serial port name, can take any form accepted by OS
            nBaudRate -- Usually 500000 or 2400, can be -1 to not define it and take default setting
        Returns:
		    Boolean True if port is open, otherwise False
		"""
        bConnected = False
        if(self.m_nVerboseLevel > 0):
            sErrorText = "User COM port: "
            if(sUserPort):
                sErrorText += sUserPort
            else:
                sErrorText += "void"
            print(sErrorText)
            
        try:
            self.m_hSerialPortLock.acquire()
            if(sUserPort):                              
                for sPort in self.m_arrValidCP2102Ports:
                    if(sUserPort == sPort.device):
                        sPortName = sUserPort
                        bConnected = True
            elif (len(self.m_arrValidCP2102Ports) == 1):
                sPortName = self.m_arrValidCP2102Ports[0].device
                bConnected = True
            elif(len(self.m_arrValidCP2102Ports) == 2):
                for objPort in self.m_arrValidCP2102Ports:
                    if (objPort.device == "/dev/ttyAMA0"):
                        self.m_arrValidCP2102Ports.remove(objPort)
                if(len(self.m_arrValidCP2102Ports) == 1):
                    sPortName = self.m_arrValidCP2102Ports[0].device
                    bConnected = True
                    print("Automatically selected port" + sPortName +" - ttyAMA0 ignored")
         
            if(bConnected):
                self.m_objSerialPort.baudrate = nBaudRate
                self.m_objSerialPort.port = sPortName
                self.m_objSerialPort.bytesize = serial.EIGHTBITS   
                self.m_objSerialPort.stopbits= serial.STOPBITS_ONE 
                self.m_objSerialPort.Parity = serial.PARITY_NONE   
                self.m_objSerialPort.timeout = 100  

                self.m_objSerialPort.open()

                self.m_bPortConnected = True
                self.m_LastCaptureTime = datetime.now()
                self.m_bHoldMode = False

                print("Connected: " + str(self.m_objSerialPort.port) + ", " + str(self.m_objSerialPort.baudrate) + " bauds")

                time.sleep(0.5)
                if (self.m_bAutoConfigure):
                    self.SendCommand_RequestConfigData()
                    time.sleep(0.5)
            else:             
                print("Error: select a different COM port")

        except Exception as obEx:
            print("ERROR ConnectPort: " + str(obEx))
        finally:
            self.m_hSerialPortLock.release()
        return self.m_objSerialPort.is_open   
        
    def ClosePort(self):
        """ Close port and initialize some settings

        Returns:
            Boolean True if serial port was closed, False otherwise
		"""
        try:
            self.m_hSerialPortLock.acquire()

            if (self.m_objSerialPort.is_open):
                time.sleep(0.2)
                if (self.IsAnalyzer()):
                    if (self.m_eMode == RFE_Common.eMode.MODE_SNIFFER):
						#Force device to configure in Analyzer mode if disconnected - C0 will be ignored so we send full config again
                        self.SendCommand("C2-F:" + str(self.StartFrequencyMHZ * 1000.0) + "," + str(self.CalculateEndFrequencyMHZ() * 1000) + "," +
                                         str(self.AmplitudeTopDBM) + "," + str(self.AmplitudeBottomDBM))
                    if (self.m_eMode != RFE_Common.eMode.MODE_SPECTRUM_ANALYZER and self.m_eMode != RFE_Common.eMode.MODE_SNIFFER):
						#If current mode is not analyzer, send C0 to force it
                        self.SendCommand_RequestConfigData()

                    time.sleep(0.2)
                    self.SendCommand_Hold() #Switch data dump to off
                    time.sleep(0.2)
                    if (self.m_objSerialPort.baudrate < 115200):
                        time.sleep(0.2)
                else:
                    self.SendCommand_GeneratorRFPowerOFF()
                    time.sleep(0.2)
                time.sleep(0.2)
                self.SendCommand_ScreenON()
                self.SendCommand_DisableScreenDump()

                #Close the port
                print("Disconnected.")
                self.m_objSerialPort.close()

                self.m_bPortConnected = False #do this here so the external event has the right port status

        except Exception:
            pass
        finally: 
            self.m_hSerialPortLock.release()

        self.m_bPortConnected = False  #to be double safe in case of exception
        self.m_eMainBoardModel = RFE_Common.eModel.MODEL_NONE
        self.m_eExpansionBoardModel = RFE_Common.eModel.MODEL_NONE

        self.m_LastCaptureTime = datetime(2000, 1, 1, 0, 0, 0, 000)

        self.m_sSerialNumber = ""
        self.m_sExpansionSerialNumber = ""
        self.m_nRetriesCalibration = 0
        self.m_arrSpectrumAnalyzerEmbeddedCalibrationOffsetDB = None
        self.m_arrSpectrumAnalyzerExpansionCalibrationOffsetDB = None

        return (not self.m_objSerialPort.is_open)
    
    def UpdateDeviceConfig(self, fStartMHZ, fEndMHZ, fTopDBM=0, fBottomDBM=-120, fRBW_KHZ=0.0):
        """Send a new configuration to the connected device

        Parameters:
            fStartMHZ  -- New start frequency, in MHZ, must be in valid range for the device
            fEndMHZ    -- New stop frequency, in MHZ, must be in valid range for the device
            fTopDBM    -- Optional, only impact visual not real data
            fBottomDBM -- Optional, only impact visual not real data
            fRBW_KHZ   -- Reserved future firmware support 
		"""
        if (self.m_bPortConnected):
            # #[32]C2-F:Sssssss,Eeeeeee,tttt,bbbb
            nStartKhz = int(fStartMHZ * 1000)
            nEndKhz = int(fEndMHZ * 1000)
            nTopDBM = int(fTopDBM)
            nBottomDBM = int(fBottomDBM)

            sTopDBM = "{:03d}".format(nTopDBM)
            sBottomDBM = "{:03d}".format(nBottomDBM)
            if (len(sTopDBM) < 4):
                sTopDBM = "0" + sTopDBM
            if (len(sBottomDBM) < 4):
                sBottomDBM = "0" + sBottomDBM
            sData = "C2-F:" + "{:07d}".format(nStartKhz)+ "," + "{:07d}".format(nEndKhz)+ "," + sTopDBM + "," + sBottomDBM
            if (fRBW_KHZ>0 and fRBW_KHZ >= 3.0 and fRBW_KHZ <= 670.0):
                nSteps = int(round((fEndMHZ - fStartMHZ) * 1000.0 / fRBW_KHZ))
                if (nSteps < 112):
                    nSteps = 112
                if (nSteps > RFE_Common.CONST_MAX_SPECTRUM_STEPS):
                    nSteps = RFE_Common.CONST_MAX_SPECTRUM_STEPS
                fRBW_KHZ = round((fEndMHZ - fStartMHZ) * 1000.0) / nSteps
                if (fRBW_KHZ >= 3.0 and fRBW_KHZ <= 620.0):
                    sData += "," + "{:05d}".format(nSteps)
                else:
                    print("Ignored RBW " + fRBW_KHZ + "Khz")

            self.SendCommand(sData)

            #wait some time for the unit to process changes, otherwise may get a different command too soon
            time.sleep(0.5)

    def SendCommand_RequestConfigData(self):
        """Request RF Explorer SA device to send configuration data and start sending feed back
		"""
        self.SendCommand("C0")

    def SendCommand_Hold(self):
        """Ask RF Explorer SA device to hold
		"""
        self.SendCommand("CH")

    def SendCommand_GeneratorRFPowerOFF(self):
        """Set RF Explorer RFGen device RF power output to OFF
		"""
        if (self.IsGenerator()):
            self.m_bRFGenPowerON = False
            self.SendCommand("CP0")

    def SendCommand_GeneratorRFPowerON(self):
        """Set RF Explorer RFGen device RF power output to ON
		"""
        if (self.IsGenerator()):
            self.m_bRFGenPowerON = True
            self.SendCommand("CP1")

    def SendCommand_DisableScreenDump(self):
        """Disable device LCD screen dump
		"""
        self.SendCommand("D0")

    def SendCommand_ScreenON(self):
        """Enable LCD and backlight on device screen (according to internal device configuration settings)
		"""
        self.SendCommand("L1")

    def SendCommand_ScreenOFF(self):
        """Disable LCD and backlight on device screen
		"""
        self.SendCommand("L0")
    
    def SendCommand_GeneratorCW(self):
        """Start CW generation using current configuration setting values - only valid for Signal Generator models
		"""
        if (self.IsGenerator()):
            self.SendCommand("C3-F:" + "{:07d}".format(int(self.RFGenCWFrequencyMHZ * 1000)) + self.GetRFGenPowerString())   
    
    def SendCommand_GeneratorSweepAmplitude(self):
        """Start Sweep Amplitude generation using current configuration setting values - only valid for Signal Generator models
		"""
        if (self.IsGenerator()):
            sSteps = "{:04d}".format(self.RFGenSweepSteps)

            sStartPower = ","
            if (self.RFGenStartHighPowerSwitch):
                sStartPower += "1,"
            else:
                sStartPower += "0,"
            sStartPower += str(self.RFGenStartPowerLevel) + ","

            sStopPower = ","
            if (self.RFGenStopHighPowerSwitch):
                sStopPower += "1,"
            else:
                sStopPower += "0,"
            sStopPower += str(self.RFGenStopPowerLevel) + ","

            self.SendCommand("C3-A:" + "{:07d}".format(int(self.RFGenCWFrequencyMHZ * 1000)) + sStartPower + sSteps +\
                sStopPower + "{:05d}".format(self.RFGenStepWaitMS))

    def SendCommand_GeneratorSweepFreq(self, bTracking = False):
        """Start Sweep Freq generation using current configuration setting values - only valid for Signal Generator models

        Parameters:
            bTracking -- Default is False, set it to 'True' to enable SNA tracking mode in generator
		"""
        if (self.IsGenerator()):
            sSteps = "," + "{:04d}".format(self.RFGenSweepSteps) + ","

            dStepMHZ = self.RFGenTrackStepMHZ()
            if (dStepMHZ < 0):
                return

            sCommand = "C3-"
            if (bTracking):
                sCommand += 'T'
                self.m_eMode = RFE_Common.eMode.MODE_NONE
            else:
                sCommand += 'F'
            sCommand += ":" + "{:07d}".format(int(self.RFGenStartFrequencyMHZ * 1000)) + self.GetRFGenPowerString() + sSteps +\
                "{:07d}".format(int(dStepMHZ * 1000))+ "," + "{:07d}".format(self.RFGenStepWaitMS)

            self.SendCommand(sCommand)
        
    def RFGenTrackStepMHZ(self):
        """Configured tracking step size in MHZ

        Returns: 
            Float Tracking step size in MHz
		"""
        return (self.RFGenStopFrequencyMHZ - self.RFGenStartFrequencyMHZ) / self.RFGenSweepSteps
    
    def SendCommand_SweepDataPoints(self, nDataPoints):
        """Define RF Explorer SA sweep data points

        Parameters:
            nDataPoints -- A value in the range of 16-4096, note a value multiple of 16 will be used, so any other number will be truncated to nearest 16 multiple
		"""
        self.SendCommand("CJ" + chr(int(nDataPoints / 16)))

    def SendCommand(self, sCommand):
        """Format and send command - for instance to reboot just use "r", the '#' decorator and byte length char will be included within
         
        Parameters: www.rf-explorer.com/API 
            sCommand -- Unformatted command from http://www.rf-explorer.com/API
		"""
        sCompleteCommand = "#" + chr(len(sCommand) + 2) + sCommand
        self.m_objSerialPort.write(sCompleteCommand.encode('ascii'))
        if self.m_nVerboseLevel>5:
            print("RFE Command: #(" + str(len(sCompleteCommand)) + ")" + sCommand + " [" + " ".join("{:02X}".format(ord(c)) for c in sCompleteCommand) + "]")
    
    def ResetInternalBuffers(self):
        """Use this function to internally re-initialize the MaxHold buffers used for cache data inside the RF Explorer device
		"""
        #we use this method to internally restore capture buffers to empty status
        self.SendCommand("Cr")

    def CleanReceivedBytes(self):
        """Clean and reset all debug internal received data bytes
		"""
        self.m_ReceivedBytesMutex.WaitOne()
        self.m_sDebugAllReceivedBytes=""
        self.m_ReceivedBytesMutex.ReleaseMutex()
   
    def Dispose(self, bDisposing):
        """Local dispose method

        Parameters:
            bDisposing -- If disposing is required
		"""
        self.Close()

        if (not self.m_bDisposed):
            if (bDisposing):
                if (self.m_objSerialPort):
                    if (self.m_objSerialPort.is_open):
                        self.m_objSerialPort.close()
                    self.m_objSerialPort = None
                if (self.m_ReceivedBytesMutex):
                    self.m_ReceivedBytesMutex = None
            self.m_bDisposed = True

    def Close(self):
        """End thread and close port
		"""
        if (self.m_bRunReceiveThread):
            #print("Close(): close thread")
            self.m_bRunReceiveThread = False
            time.sleep(1)
            self.m_objThread = None
        self.ClosePort()
    
    def GetSignalGeneratorEstimatedAmplitude(self, dFrequencyMHZ):
        """Returns best matching amplitude value

        Parameters:
            dFrequencyMHZ -- frequency in MHz to get estimate the amplitude from
        Returns:
            Float Best matching amplitude value
		"""
        return self.m_RFGenCal.GetEstimatedAmplitude(dFrequencyMHZ, self.m_bRFGenHighPowerSwitch, self.m_nRFGenPowerLevel)

    def GetRFGenPowerString(self):
        """Get a string with the power level 

        Returns:
            String Power level
		"""
        sPower = ","
        if (self.RFGenHighPowerSwitch):
            sPower += "1,"
        else:
            sPower += "0,"
        sPower += str(self.RFGenPowerLevel)

        return sPower

    def GetRFE6GENCal(self):
        """Get RFE6Gen calibration data
        
        Returns:
            RFE6GEN_CalibrationData Calibration data object
		"""
        return self.m_RFGenCal
    
    def GetAmplitudeCorrectionDB(self, nMHz):
        """Returns the current correction amplitude value for a given MHZ frequency
        
        Parameters:
            nMHz -- Frequency reference in MHZ to get correction data from
        Returns:
            Float Amplitude correction data in dB
        """
        return self.m_FileAmplitudeCalibration.GetAmplitudeCalibration(nMHz)
        
    @classmethod
    def ResetIOT_HW(cls, bMode):
        """Set Raspberry pi GPIO pins and reset RF Explorer device

        Parameters: 
            bMode -- True if the baudrate is set to 500000bps, False to 2400bps
        """
        try:
            import RPi.GPIO as GPIO
       
            #print("RPi info: " + str(GPIO.RPI_INFO)) #information about your RPi:
            #print("RPi.GPio version: " + GPIO.VERSION) #version of RPi.GPIO:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)    #refer to the pin numbers on the P1 header of the Raspberry Pi board
            GPIO.setup(12, GPIO.OUT)    #set /reset (pin 12) to output 
            GPIO.output(12, False)      #set /reset (pin 12) to LOW
            GPIO.setup(21, GPIO.OUT)    #set GPIO2 (pin 21) to output
            GPIO.output(21, bMode)      #set GPIO2 (pin 21) to HIGH (for 500Kbps)
            time.sleep(0.1)             #wait 100ms
            GPIO.output(12, True)       #set /reset to HIGH
            time.sleep(2.5)             #wait 2.5sec
            GPIO.setup(21, GPIO.IN)     #set GPIO2 to input
            GPIO.cleanup()              #clean up GPIO channels 

        except RuntimeError:
            print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
        
