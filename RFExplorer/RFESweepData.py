#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments, duplicate-code

#============================================================================
#RF Explorer Python Libraries - A Spectrum Analyzer for everyone!
#Copyright © 2010-21 RF Explorer Technologies SL, www.rf-explorer.com
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

import math
from datetime import datetime

from RFExplorer import RFE_Common 
from RFExplorer import RFExplorer 

class RFESweepData:
    """Class support a full sweep of data from RF Explorer, and it is used in the RFESweepDataCollection container
	"""
    def __init__(self, fStartFreqMHZ, fStepFreqMHZ, nTotalDataPoints):
        self.m_Time = datetime.now()
        self.m_nTotalDataPoints = nTotalDataPoints
        self.m_fStartFrequencyMHZ = fStartFreqMHZ
        self.m_fStepFrequencyMHZ = fStepFreqMHZ
        self.m_arrAmplitude = [RFE_Common.CONST_MIN_AMPLITUDE_DBM] * self.m_nTotalDataPoints     # The actual data container, a consecutive set of dBm amplitude values
        self.m_arrBLOB = []
        self.m_sBLOBString = ""   #variable used to internall store byte array in string format received if is used externally
        
    @property
    def StartFrequencyMHZ(self):
        """Get Start frequency 
		"""
        return self.m_fStartFrequencyMHZ

    @property
    def EndFrequencyMHZ(self):
        """Get End frequency
		"""
        return self.GetFrequencyMHZ(self.m_nTotalDataPoints - 1)

    @property
    def StepFrequencyMHZ(self):
        """Step frequency between each sweep step
		"""
        return self.m_fStepFrequencyMHZ
    @StepFrequencyMHZ.setter
    def StepFrequencyMHZ(self, value):
        self.m_fStepFrequencyMHZ = value

    @property
    def TotalSteps(self):
        """Total number of sweep steps captured
		"""
        return (self.m_nTotalDataPoints - 1)

    @property
    def TotalDataPoints(self):
        """Total number of sweep data points captured (same as TotalSteps + 1)
		"""
        return self.m_nTotalDataPoints

    @property
    def CaptureTime(self):
        """The time when this data sweep was created, it should match as much as
        possible the real data capture
		"""
        return self.m_Time
    @CaptureTime.setter 
    def CaptureTime(self, value):       
        self.m_Time = value
    
    def ProcessReceivedString(self, sLine, fOffsetDB, bBLOB=False, bString=False):
        """This function will process a received, full consistent string received from remote device
        and fill it in all data

        Parameters:
            sLine     -- String received from device, previously parsed and validated
            fOffsetDB -- Currently specified offset in DB
            bBLOB     -- If true the internal BLOB object will be filled in for later use in GetBLOB
            bString   -- If true the internal string object will be filled in for later use in GetBLOBString
        Returns:
            Boolean True if parsing was ok, False otherwise
		"""
        bOk = True

        try:
            if ((len(sLine) > 2) and (sLine[:2] == "$S") and (len(sLine[2:]) == self.m_nTotalDataPoints)):
                if (bBLOB):
                    self.m_arrBLOB = [bytes(0)] * self.m_nTotalDataPoints
                objSweep = RFESweepData(self.StartFrequencyMHZ, self.StepFrequencyMHZ, self.m_nTotalDataPoints)
                objSweep.CaptureTime = datetime.now()
                #print("sLine length: " + str(len(sLine)) +" - "+ "TotalDataPoints: " + str(self.m_nTotalDataPoints))
                if (bString):
                    self.m_sBLOBString = sLine[2:(self.m_nTotalDataPoints + 2)]
                    print("sLine: " + sLine[2:(self.m_nTotalDataPoints + 2)])

                for nInd in range(self.m_nTotalDataPoints):
                    #print("sLine byte[" + str(nInd) + "]:"+ str(sLine[2 + nInd].encode('utf-8')))
                    nVal = ord(sLine[2 + nInd])
                    fVal = nVal / -2.0
                    if (bBLOB):
                        self.m_arrBLOB[nInd] = nVal
                    self.SetAmplitudeDBM(nInd, fVal + fOffsetDB)
            else:
                bOk = False
        except Exception as obEx:
            print("Error in RFESweepData - ProcessReceivedString(): " + str(obEx))
            bOk = False

        return bOk
    
    def GetAmplitude_DBM(self, nDataPoint):
        """Returns amplitude data in dBm.  This is the value as it was read from
        the device or from a file so it is not adjusted by offset or additionally compensated in any way.
        If the value was read from a device, it may already be an adjusted value including device configured offset.

        Parameters:
            nDataPoint -- Internal frequency step or bucket to read data from
        Returns:
		    Float Value in dBm
		"""
        return self.GetAmplitudeDBM(nDataPoint, None, False)

    def GetAmplitudeDBM(self, nDataPoint, AmplitudeCorrection, bUseCorrection):
        """Returns amplitude data in dBm. This is the value as it was read from 
        the device or from a file so it is not adjusted by offset or additionally compensated in any way. 
        If the value was read from a device,
        it may already be an adjusted value including device configured offset.

        Parameters:
            nDataPoint          -- Internal frequency data point to read data from
            AmplitudeCorrection -- Optional parameter, can be None. If different than None, use the amplitude correction table
            bUseCorrection      -- If the AmplitudeCorrection is not None, this boolean will tell whether to use it or not
        Returns:
		    Float Value in dBm
		"""
        if (nDataPoint < self.m_nTotalDataPoints):
            if ((AmplitudeCorrection) and bUseCorrection):
                return self.m_arrAmplitude[nDataPoint] + AmplitudeCorrection.GetAmplitudeCalibration(int(self.GetFrequencyMHZ(nDataPoint))) 
            else:
                return self.m_arrAmplitude[nDataPoint]
        else:
            return RFE_Common.CONST_MIN_AMPLITUDE_DBM

    def SetAmplitudeDBM(self, nDataPoint, fDBM):
        """Set Amplitude in dBm 

        Parameters:
            nDataPoint  -- Internal frequency data point where to set data
            fDBM        -- New value in dBm
		"""
        if (nDataPoint < self.m_nTotalDataPoints):
            self.m_arrAmplitude[nDataPoint] = fDBM

    def GetFrequencyMHZ(self, nDataPoint):
        """Get frequency in MHz 
            
        Parameters:
            nDataPoint -- Internal frequency data point to read data from
        Returns:
		    Float Frequency in MHz, zero otherwise
		"""
        if (nDataPoint < self.m_nTotalDataPoints):
            return self.m_fStartFrequencyMHZ + (self.m_fStepFrequencyMHZ * nDataPoint)
        else:
            return 0.0

    def GetFrequencySpanMHZ(self):
        """Get frequency span in MHz
        
        Returns:
		    Float Frequency span in MHz
		"""
        return (self.m_fStepFrequencyMHZ * self.TotalSteps)

    def GetMinDataPoint(self):
        """Returns the step of the lowest amplitude value found
                
        Returns:
		    Integer The data point of the lowest amplitude value
		"""
        nMinDataPoint = 0
        fMin = RFE_Common.CONST_MAX_AMPLITUDE_DBM
        for nInd in range(self.m_nTotalDataPoints):
            if (fMin > self.m_arrAmplitude[nInd]):
                fMin = self.m_arrAmplitude[nInd]
                nMinDataPoint = nInd
        return nMinDataPoint

    def GetPeakDataPoint(self):
        """Returns the step of the highest amplitude value found
                        
        Returns:
		    Integer The data point of the highest amplitude value
		"""
        nPeakDataPoint = 0
        fPeak = RFE_Common.CONST_MIN_AMPLITUDE_DBM

        for nInd in range(self.m_nTotalDataPoints):
            if (fPeak < self.m_arrAmplitude[nInd]):
                fPeak = self.m_arrAmplitude[nInd]
                nPeakDataPoint = nInd
        return nPeakDataPoint

    def IsSameConfiguration(self, objOther):
        """Compare new object configuration with stored configuration data

        Parameters:
            objOther -- New configuration object
        Returns:
		    Boolean True if they are the same, False otherwise
		"""
        return (math.fabs(objOther.StartFrequencyMHZ - self.StartFrequencyMHZ) < 0.001 and math.fabs(objOther.StepFrequencyMHZ - self.StepFrequencyMHZ) < 0.001 and (objOther.TotalSteps == self.TotalSteps))

    def Duplicate(self):
        """Duplicate RFESweepData object

        Returns: 
            RFESweepData  Duplicate object
		"""
        objSweep = RFESweepData(self.StartFrequencyMHZ, self.StepFrequencyMHZ, self.m_nTotalDataPoints)

        objSweep.m_arrAmplitude = self.m_arrAmplitude.copy()

        return objSweep

    def GetChannelPowerDBM(self):
        """Returns power channel over the full span being captured. The power is instantaneous real time
        For average power channel use the collection method GetAverageChannelPower().

        Returns:
		    Float Channel power in dBm/span
		"""
        fChannelPower = RFE_Common.CONST_MIN_AMPLITUDE_DBM
        fPowerTemp = 0.0

        for nInd in range(self.m_nTotalDataPoints):
            fPowerTemp += RFExplorer.Convert_dBm_2_mW(self.m_arrAmplitude[nInd])

        if (fPowerTemp > 0.0):
            #add here actual RBW calculation in the future - currently we are
            #assuming frequency step is the same
            #as RBW which is not 100% accurate.
            fChannelPower = RFExplorer.Convert_mW_2_dBm(fPowerTemp)

        return fChannelPower

    def Dump(self):
        """ Dump a CSV string line with sweep data.

        Returns:
            String All sweep data in CSV format
		"""
        
        sResult = "Sweep data: " + str("{0:.3f}".format(self.StartFrequencyMHZ)) + " - " + "MHz " + str("{0:.3f}".format(self.StepFrequencyMHZ)) + "MHz " + " - " + "Steps: " + str(self.TotalSteps)
        try:
            for nDataPoint in range(self.m_nTotalDataPoints):
                if (nDataPoint > 0):
                    sResult += ","
                if ((nDataPoint % 16) == 0):
                    sResult += "\n"
                sResult += str('{:04.1f}'.format(self.GetAmplitudeDBM(nDataPoint, None, False)))
        except Exception as obEx:
            if self.m_nVerboseLevel>0: 
                print("m_arrReceivedStrings processing: " + str(obEx))

        return sResult

    def SaveFileCSV(self, sFilename, cCSVDelimiter, AmplitudeCorrection):
        """Save a CSV file using one frequency point/dBm value per line

        Parameters:
            sFilename           -- Full path filename
            cCSVDelimiter       -- Comma delimiter to use
            AmplitudeCorrection -- Optional parameter, can be None. If different than None, use the amplitude correction table
		"""
        try:
            with open(sFilename, 'w') as objWriter:
                for nStep in range(self.TotalDataPoints):
                    objWriter.write("{0:.3f}".format(self.GetFrequencyMHZ(nStep)))
                    objWriter.write(cCSVDelimiter)
                    objWriter.write("{0:.1f}".format(self.GetAmplitudeDBM(nStep, AmplitudeCorrection, AmplitudeCorrection != None)))
                    objWriter.write("\n")
        except Exception as obEx:
            print("Error: " + str(obEx))
