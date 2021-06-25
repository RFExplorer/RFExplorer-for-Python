#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

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

class RFEAmplitudeTableData:
    """Class support a single collection of calibration amplitude values, of 1 MHz steps
    Positive values will be used to externally add to the measurement, that means imply correcting attenuation
    whereas negative values will be to externally substract to the measurement, implying correcting gain. 
	"""
    CONST_MAX_ENTRY_DATA = 6101
    CONST_MIN_ENTRY_DATA = 0
    CONST_INVALID_DATA = -1E10
    CONST_DEFAULT_COMPRESSION = -10.0
    CONST_DEFAULT_AMPLITUDE_CORRECTION = 0.0 

    def __init__(self):
        self.m_arrAmplitudeCalibrationDataDB = [0.0] * self.CONST_MAX_ENTRY_DATA
        self.m_arrCompressionDataDBM = [0.0] * self.CONST_MAX_ENTRY_DATA
        self.m_bHasCompressionData = False
        self.lm_bHasCalibrationData = False
        self.m_sCalibrationID = ""
        self.Clear()
    
    @property
    def CalibrationID(self):
        """Calibration ID is usually a filename to name the calibration in use
        future versions may support different IDs than a filename
		"""
        return self.m_sCalibrationID

    @property
    def HasCompressionData(self):
        """Returns true if data stored include compression amplitude for overload check
		"""    
        return self.m_bHasCompressionData

    @property
    def HasCalibrationData(self):
        """Will return true if there is loaded valid calibration data
		"""    
        return self.m_bHasCalibrationData

    @classmethod
    def FileHeaderVersioned(cls):
        """File header version to control an unknown format

        Returns:
            String File header version
		"""
        return "--RFEAT01"

    def Clear(self):
        """Initialize all collection of calibration amplitude values 
		"""
        self.m_sCalibrationID = ""
        self.m_bHasCalibrationData = False
        for nInd in range(len(self.m_arrAmplitudeCalibrationDataDB) - 1):
            self.m_arrAmplitudeCalibrationDataDB[nInd] = self.CONST_INVALID_DATA
            self.m_arrCompressionDataDBM[nInd] = self.CONST_INVALID_DATA

    def GetAmplitudeCalibration(self, nIndexMHz):
        """Amplitude correction data for each MHZ entry

        Parameters:
            nIndexMHz -- Frequency reference in MHZ to get correction data from
        Returns:
            Float Correction amplitude value in dB
		"""
        if ((nIndexMHz < self.CONST_MAX_ENTRY_DATA) and (self.m_arrAmplitudeCalibrationDataDB) and (range(self.m_arrAmplitudeCalibrationDataDB) > nIndexMHz) and (self.m_arrAmplitudeCalibrationDataDB[nIndexMHz] != self.CONST_INVALID_DATA)):
            return self.m_arrAmplitudeCalibrationDataDB[nIndexMHz]
        else:
            return self.CONST_DEFAULT_AMPLITUDE_CORRECTION

    def GetCompressionAmplitude(self, nIndexMHz):
        """Amplitude compression data for each MHZ entry

        Parameters: 
            nIndexMHz -- Frequency reference in MHZ to get compression amplitude data from
        Returns:
            Float Compression amplitude value in dB
		"""
        if ((nIndexMHz < self.CONST_MAX_ENTRY_DATA) and (self.m_arrCompressionDataDBM) and (range(self.m_arrCompressionDataDBM) > nIndexMHz) and (self.m_arrAmplitudeCalibrationDataDB[nIndexMHz] != self.CONST_INVALID_DATA)):
            return self.m_arrCompressionDataDBM[nIndexMHz]
        else:
            return self.CONST_DEFAULT_COMPRESSION

    def NormalizeDataIterating(self, arrAmplitudeData):
        """Utility function to be used by both arrays, when needed

        Parameters:
            arrAmplitudeData -- Collection of amplitude calibration data
        Returns:
            List  Collection of amplitude calibration data   
		"""
        fAmplitude1 = fAmplitude2 = self.CONST_INVALID_DATA  #the two amplitude values to iterate in order to adjust intermediate values
        nAmplitude1Ind = nAmplitude2Ind = -1 #Index used to know the position of the two amplitudes

        for nInd in range(len(arrAmplitudeData)-1):
            fVal = arrAmplitudeData[nInd]

            if (fAmplitude1 == self.CONST_INVALID_DATA):
                if (fVal != self.CONST_INVALID_DATA):
                    fAmplitude1 = fVal
                    nAmplitude1Ind = nInd
                else:
                    #use self._DEFAULT_AMPLITUDE_CORRECTION if nothing else is found
                    #valid yet
                    arrAmplitudeData[nInd] = self.CONST_DEFAULT_AMPLITUDE_CORRECTION
            elif (fAmplitude2 == self.CONST_INVALID_DATA):
                if (fVal != self.CONST_INVALID_DATA):
                    fAmplitude2 = fVal
                    nAmplitude2Ind = nInd

                    if ((nAmplitude2Ind - nAmplitude1Ind) > 1):
                        #if more than one step is between the two, iterate to
                        #add an incremental delta
                        fDelta = (fAmplitude2 - fAmplitude1) / (nAmplitude2Ind - nAmplitude1Ind)
                        nSteps = 1
                        nInd2 = nAmplitude1Ind + 1
                        while (nInd2 < nAmplitude2Ind):
                            arrAmplitudeData[nInd2] = fAmplitude1 + nSteps * fDelta
                            nInd2 += 1 
                            nSteps += 1

                    fAmplitude1 = fAmplitude2
                    nAmplitude1Ind = nAmplitude2Ind
                    fAmplitude2 = self.CONST_INVALID_DATA
                    nAmplitude2Ind = 0
                else:
                    #Use last valid value from now on, it should be overwritten
                    #and updated later, but if that was
                    #the last sample, then this will be good for the remaining
                    #of the samples
                    arrAmplitudeData[nInd] = fAmplitude1

        return arrAmplitudeData

    def NormalizeAmplitudeCalibrationDataIterating(self):
        """ It will iterate to all values and will fill in anything that is not initialized with a valid value
         As oposed to NormalizeDataCopy, it will look for valid values and will fill it in with intermediate
         calculated values in between these two. If no valid value is found among two (i.e. last value or first value)
         then it is filled in using NormalizedDataCopy.
		"""
        self.m_arrAmplitudeCalibrationDataDB = self.NormalizeDataIterating(self.m_arrAmplitudeCalibrationDataDB)

    def NormalizeCompressionData(self):
        """ This function will make sure the compression data has start/end points even if not specified in the file
		"""
        if (self.m_arrCompressionDataDBM[self.CONST_MIN_ENTRY_DATA] == self.CONST_INVALID_DATA):
            self.m_arrCompressionDataDBM[self.CONST_MIN_ENTRY_DATA] = self.CONST_DEFAULT_COMPRESSION
        if (self.m_arrCompressionDataDBM[self.CONST_MAX_ENTRY_DATA - 1] == self.CONST_INVALID_DATA):
            self.m_arrCompressionDataDBM[self.CONST_MAX_ENTRY_DATA - 1] = self.CONST_DEFAULT_COMPRESSION

    def NormalizeDataCopy(self):
        """It will iterate to all values and will fill in anything that is not initialized with a valid value
        It uses a copy method, not an incremental method (i.e. it will pick the first valid value and 
        go copying the same value over and over till it find another valid one. See NormalizeDataPredict for alternative
		"""
        fLastAmplitude = self.CONST_DEFAULT_AMPLITUDE_CORRECTION
        for nInd in range(len(self.m_arrAmplitudeCalibrationDataDB)-1):
            fVal = self.m_arrAmplitudeCalibrationDataDB[nInd]
            if (fVal == self.CONST_INVALID_DATA):
                self.m_arrAmplitudeCalibrationDataDB[nInd] = fLastAmplitude
            else:
                fLastAmplitude = fVal

    def LoadFile(self, sFilename):
        """Load a file with amplitude and optionally compression data 

        Parameters:
            sFilename -- Full path of the filename
        Returns:
		    Boolean True if everything ok, False if data was invalid
		"""
        bOk = True
        try:
            with open(sFilename, 'r') as objReader:
                sHeader = objReader.readline()[:-1] #[-1] is to delete '\n' at the end
                if (sHeader != self.FileHeaderVersioned()): 
                    #unknown format
                    return False

                self.Clear()
                while(bOk):
                    #Read line, trim and replace all consecutive blanks with a single tab
                    sLine = objReader.readline().strip(' ')
                    sLine = sLine.replace('\t', ' ')[:-1]
                    while ("  " in sLine):
                        sLine = sLine.replace("  ", " ")

                    if (sLine[:2] != "--"):
                        arrStrings = sLine.split(' ')
                        if (len(arrStrings) >= 2):
                            nMHZ = int(arrStrings[0])
                            self.m_arrAmplitudeCalibrationDataDB[nMHZ] = float(arrStrings[1])
                            if (len(arrStrings) >= 3):
                                #this is a file that includes compression data
                                self.m_arrCompressionDataDBM[nMHZ] = float(arrStrings[2])
                                self.m_bHasCompressionData = True
                        else:
                            bOk = False

                if (bOk):
                    #update calibration file name
                    sFile = sFilename.split('\\')
                    if (len(sFile) > 0):
                        self.m_sCalibrationID = sFile[len(sFile) - 1].ToUpper().Replace(".RFA", "")

                    #fill in all gaps
                    self.NormalizeAmplitudeCalibrationDataIterating()
                    self.NormalizeCompressionData()
                else:
                    self.Clear()
        except Exception as obEx:
            print("Error in RFEAmplitudeTableData - LoadFile(): " + str(obEx))
            bOk = False

        return bOk   
 