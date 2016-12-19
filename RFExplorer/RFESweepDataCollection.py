#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

#============================================================================
#RF Explorer Python Libraries - A Spectrum Analyzer for everyone!
#Copyright © 2010-16 Ariel Rocholl, www.rf-explorer.com
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

from RFExplorer import RFE_Common 
from RFExplorer.RFESweepData import RFESweepData

class RFESweepDataCollection:    
    """ Allocates up to nCollectionSize elements to start with the container.
	"""
    def __init__(self, nCollectionSize, bAutogrow):
        self.m_arrData = []            #Collection of available spectrum data items
        self.m_MaxHoldData = None    #Single data set, defined for the whole collection and updated with Add, to
                                     #keep the Max Hold values
        self.m_nUpperBound = -1              #Max value for index with available data
        self.m_nInitialCollectionSize = 0
                         
        if (nCollectionSize > RFE_Common.CONST_MAX_ELEMENTS):
            nCollectionSize = RFE_Common.CONST_MAX_ELEMENTS

        self.m_bAutogrow = bAutogrow        #true if the array bounds may grow up to _MAX_ELEMENTS, otherwise will
                                            #be limited to initial collection size

        self.m_nInitialCollectionSize = nCollectionSize

        self.CleanAll()
    
    @property    
    def MaxHoldData(self):
        """Single data set, defined for the whole collection and updated with Add, to keep the Max Hold values 
		"""
        return self.m_MaxHoldData

    @property
    def Count(self):
        """ Returns the total of elements with actual data allocated.
		"""
        return int(self.m_nUpperBound + 1)

    @property
    def UpperBound(self):
        """ Returns the highest valid index of elements with actual data allocated.
		"""
        return self.m_nUpperBound 

    @classmethod
    def FileHeaderVersioned_001(cls):
        """File format constant - 001

        Returns:
            String 001 File header version
		"""
        return "RFExplorer PC Client - Format v001"

    @classmethod
    def FileHeaderVersioned(cls):
        """File format constant indicates the latest known and supported file format 

        Returns:
            String File header version
		"""
        return "RFExplorer PC Client - Format v" + "{:03d}".format(RFE_Common.CONST_FILE_VERSION)

    def GetData(self, nIndex):
        """ Return the data pointed by the zero-starting index
        
        Parameters:
            nIndex -- Index to find specific data inside the data array
        Returns:
		    RFESweepData None if no data is available with this index
		"""
        if (nIndex <= self.m_nUpperBound):
            return self.m_arrData[nIndex]
        else:
            return None

    def IsFull(self):
        """ True when the absolute maximum of allowed elements in the container is allocated
                
        Returns:
		    Boolean True when the absolute maximum of allowed elements in the container is allocated, False otherwise
		"""
        return (self.m_nUpperBound >= RFE_Common.CONST_MAX_ELEMENTS)

    def Add(self, SweepData):
        """This function add a single sweep data in the collection 

        Parameters:
            SweepData -- A single sweep data
        Returns:
            Boolean True it sweep data is added, False otherwise
		"""
        try:
            if (self.IsFull()):
                return False

            if (not self.m_MaxHoldData):
                self.m_MaxHoldData = RFESweepData(SweepData.StartFrequencyMHZ, SweepData.StepFrequencyMHZ, SweepData.TotalSteps)
            if (self.m_nUpperBound >= (len(self.m_arrData) - 1)):
                if (self.m_bAutogrow):
                    self.ResizeCollection(10 * 1000) #add 10K samples more
                else:
                    #move all items one position down, lose the older one at position 0
                    self.m_nUpperBound = len(self.m_arrData) - 2
                    self.m_arrData[0] = None
                    for nInd in self.m_nUpperBound:
                        self.m_arrData[nInd] = self.m_arrData[nInd + 1]

            self.m_nUpperBound += 1
            self.m_arrData[self.m_nUpperBound] = SweepData
            
            nInd = 0
            while nInd < SweepData.TotalSteps:
                if (SweepData.GetAmplitudeDBM(nInd, None, False) > self.m_MaxHoldData.GetAmplitudeDBM(nInd, None, False)):
                    self.m_MaxHoldData.SetAmplitudeDBM(nInd, SweepData.GetAmplitudeDBM(nInd, None, False))
                nInd += 1
        except Exception as obEx:
            print("Error in RFESweepDataCollection - Add(): " + str(obEx))
            return False

        return True

    def CleanAll(self):
        """Initialize internal data
		"""
        self.m_arrData = [RFESweepData] * self.m_nInitialCollectionSize   
        self.m_MaxHoldData = None
        self.m_nUpperBound = -1

    def Dump(self):
        """Dump a CSV string line with sweep data collection

        Returns:
            String All sweep data collection
		"""
        sDump = ""
        for nIndex in range(self.Count):
            objSweep = self.m_arrData[nIndex]
            if (sDump != ""):
                sDump += '\n'
            if (objSweep):
                sDump += objSweep.Dump()
            else:
                sDump += "Sweep {null}"
        return sDump

    def GetMedianAverage(self, nStart, nEnd):
        """Return a SweepData object with median average data 

        Parameters:
            nStart -- Start frequency for the median average calculation  
            nEnd   -- End frequency for the median average calculation
        Returns:
            RFESweepData object with median average data, None otherwise
		"""
        #string sDebugText = ""
        if (nStart > self.m_nUpperBound or nEnd > self.m_nUpperBound or nStart > nEnd):
            return None

        nTotalIterations = nEnd - nStart + 1
        try:
            objReturn = RFESweepData(self.m_arrData[nEnd].StartFrequencyMHZ, self.m_arrData[nEnd].StepFrequencyMHZ, self.m_arrData[nEnd].TotalSteps)

            for nSweepInd in objReturn.TotalSteps:
                #sDebugText += "[" + nSweepInd + "]:"
                fSweepValue = 0.0
                arrSweepValues = [0.0] * nTotalIterations
                
                nIterationInd = nStart
                while(nIterationInd <= nEnd) :
                    if (nSweepInd == 0):
                        #check all the sweeps use the same configuration, but
                        #only in first loop to reduce overhead
                        if (not self.m_arrData[nIterationInd].IsSameConfiguration(objReturn)):
                            return None
                    arrSweepValues[nIterationInd - nStart] = self.m_arrData[nIterationInd].GetAmplitudeDBM(nSweepInd, None, False)
                    #sDebugText += str(self.m_arrData[nIterationInd].GetAmplitudeDBM(nSweepInd)) + ","
                    nIterationInd += 1
                                
                arrSweepValues.sort()
                fSweepValue = arrSweepValues[nTotalIterations / 2]
                #sDebugText += "(" + str(fSweepValue) + ")"
                objReturn.SetAmplitudeDBM(nSweepInd, fSweepValue)
        except Exception as obEx:
            print("Error in RFESweedDataCollection - GetMedianAverage(): " + str(obEx))
            objReturn = None

        return objReturn

    def GetAverage(self, nStart, nEnd):
        """Return a SweepData object with average data 

        Parameters:
            nStart -- Start frequency for the average calculation  
            nEnd   -- End frequency for the average calculation
        Returns:
            RFESweepData object with average data, None otherwise
		"""
        #string sDebugText = ""

        if (nStart > self.m_nUpperBound or nEnd > self.m_nUpperBound or nStart > nEnd):
            return None

        try:
            objReturn = RFESweepData(self.m_arrData[nEnd].StartFrequencyMHZ, self.m_arrData[nEnd].StepFrequencyMHZ, self.m_arrData[nEnd].TotalSteps)

            for nSweepInd in objReturn.TotalSteps:
                #sDebugText += "[" + nSweepInd + "]:"
                fSweepValue = 0.0

                nIterationInd = nStart 
                while (nIterationInd <= nEnd):
                    if (nSweepInd == 0):
                        #check all the sweeps use the same configuration, but
                        #only in first loop to reduce overhead
                        if (not self.m_arrData[nIterationInd].IsSameConfiguration(objReturn)):
                            return None

                    fSweepValue += self.m_arrData[nIterationInd].GetAmplitudeDBM(nSweepInd, None, False)
                    #sDebugText +=
                    #str(self.m_arrData[nIterationInd].GetAmplitudeDBM(nSweepInd))
                    #+ ","
                    nIterationInd += 1
                
                fSweepValue = fSweepValue / (nEnd - nStart + 1)
                #sDebugText += "(" + str(fSweepValue) + ")"
                objReturn.SetAmplitudeDBM(nSweepInd, fSweepValue)
        
        except Exception as obEx:
            objReturn = None
            print("Error in RFESweedDataCollection - GetAverage(): " + str(obEx))

        return objReturn

    def SaveFileCSV(self, sFilename, cCSVDelimiter, AmplitudeCorrection):
        """Will write large, complex, multi-sweep CSV file. No save anything, if there are no data

        Parameters:
            sFilename           -- Full path filename
            cCSVDelimiter       -- Comma delimiter to use
            AmplitudeCorrection -- Optional parameter, can be None. If different than None, use the amplitude correction table
		"""
        if (self.m_nUpperBound <= 0):
            return

        objFirst = self.m_arrData[0]
        try:
            with open(sFilename, 'w') as objWriter:
                objWriter.write("RF Explorer CSV data file: " + self.FileHeaderVersioned() + '\n' + \
                    "Start Frequency: " + str(objFirst.StartFrequencyMHZ) + "MHZ" + '\n' + \
                    "Step Frequency: " + str(objFirst.StepFrequencyMHZ * 1000) + "KHZ" + '\n' + \
                    "Total data entries: " + str(self.m_nUpperBound) + '\n' + \
                    "Steps per entry: " + str(objFirst.TotalSteps)+ '\n')

                sHeader = "Sweep" + cCSVDelimiter + "Date" + cCSVDelimiter + "Time" + cCSVDelimiter + "Milliseconds"

                for nStep in range(objFirst.TotalSteps):
                    dFrequency = objFirst.StartFrequencyMHZ + nStep * (objFirst.StepFrequencyMHZ)
                    sHeader += cCSVDelimiter + "{:08.3f}".format(dFrequency)

                objWriter.write(sHeader + '\n')

                for nSweepInd in range(self.m_nUpperBound):
                    objWriter.write(str(nSweepInd) + cCSVDelimiter)

                    objWriter.write(str(self.m_arrData[nSweepInd].CaptureTime.date()) + cCSVDelimiter + \
                        str(self.m_arrData[nSweepInd].CaptureTime.time())[:-7] + cCSVDelimiter + \
                        '.' +'{:03}'.format(int(str(getattr(self.m_arrData[nSweepInd].CaptureTime.time(), 'microsecond'))[:-3])) + cCSVDelimiter)

                    if (not self.m_arrData[nSweepInd].IsSameConfiguration(objFirst)):
                        break

                    for nStep in range(objFirst.TotalSteps):
                        objWriter.write(str(self.m_arrData[nSweepInd].GetAmplitudeDBM(nStep, AmplitudeCorrection, (AmplitudeCorrection != None))))
                        if (nStep != (objFirst.TotalSteps - 1)):
                            objWriter.write(cCSVDelimiter)
                    
                    objWriter.write('\n')

        except Exception as objEx:
            print("Error in RFESweepDataCollection - SaveFileCSV(): " + str(objEx))      

    def GetTopBottomDataRange(self, dTopRangeDBM, dBottomRangeDBM, AmplitudeCorrection):
        """Return estimated Top and Bottom level using data collection, no return anything if sweep data collection is empty

        Parameters:
            dTopRangeDBM        -- Bottom level in dBm
            dBottomRangeDBM     -- Top level in dBm
            AmplitudeCorrection -- Optional parameter, can be None. If different than None, use the amplitude correction table
        Returns:
            Float Bottom level in dBm
            Float Top level in dBm
		"""
        dTopRangeDBM = RFE_Common.CONST_MIN_AMPLITUDE_DBM
        dBottomRangeDBM = RFE_Common.CONST_MAX_AMPLITUDE_DBM

        if (self.m_nUpperBound <= 0):
            return

        for nIndSample in self.m_nUpperBound:
            for nIndStep in self.m_arrData[0].TotalSteps:
                dValueDBM = self.m_arrData[nIndSample].GetAmplitudeDBM(nIndStep, AmplitudeCorrection, (AmplitudeCorrection != None))
                if (dTopRangeDBM < dValueDBM):
                    dTopRangeDBM = dValueDBM
                if (dBottomRangeDBM > dValueDBM):
                    dBottomRangeDBM = dValueDBM

        return dTopRangeDBM, dBottomRangeDBM

    def ResizeCollection(self, nSizeToAdd):
        """Change data collection size 

        Parameters:
            nSizeToAdd -- Number of sample to add to the sweep data collection
		"""
        self.m_arrData += [RFESweepData] * nSizeToAdd
