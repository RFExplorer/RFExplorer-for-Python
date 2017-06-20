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

class RFEConfiguration:
    """Store configuration data
    """
    def __init__(self, objSource):
        self.m_sLineString = ""
        if objSource:
            self.fStartMHZ = objSource.fStartMHZ
            self.fStepMHZ = objSource.fStepMHZ
            self.fAmplitudeTopDBM = objSource.fAmplitudeTopDBM
            self.fAmplitudeBottomDBM = objSource.fAmplitudeBottomDBM
            self.nFreqSpectrumSteps = objSource.nFreqSpectrumSteps
            self.bExpansionBoardActive = objSource.bExpansionBoardActive
            self.m_eMode = objSource.m_eMode
            self.fMinFreqMHZ = objSource.fMinFreqMHZ
            self.fMaxFreqMHZ = objSource.fMaxFreqMHZ
            self.fMaxSpanMHZ = objSource.fMaxSpanMHZ
            self.fRBWKHZ = objSource.fRBWKHZ
            self.fOffset_dB = objSource.fOffset_dB
            self.eCalculator = objSource.eCalculator
            self.nBaudrate = objSource.nBaudrate
            self.eModulations = objSource.eModulations
            self.fThresholdDBM = objSource.fThresholdDBM

            self.bRFEGenHighPowerSwitch = objSource.bRFEGenHighPowerSwitch
            self.nRFEGenPowerLevel = objSource.nRFEGenPowerLevel
            self.fRFEGenCWFreqMHZ = objSource.fRFEGenCWFreqMHZ
            self.nRFEGenSweepWaitMS = objSource.nRFEGenSweepWaitMS
            self.bRFEGenPowerON = objSource.bRFEGenPowerON

            self.bRFEGenStartHighPowerSwitch = objSource.bRFEGenStartHighPowerSwitch
            self.bRFEGenStopHighPowerSwitch = objSource.bRFEGenStopHighPowerSwitch
            self.nRFEGenStartPowerLevel = objSource.nRFEGenStartPowerLevel
            self.nRFEGenStopPowerLevel = objSource.nRFEGenStopPowerLevel
            self.nRFGenSweepPowerSteps = objSource.nRFGenSweepPowerSteps    
        else:
            self.fStartMHZ = 0.0
            self.fStepMHZ = 0.0
            self.fAmplitudeTopDBM = 0.0
            self.fAmplitudeBottomDBM = 0.0
            self.nFreqSpectrumSteps = 0
            self.bExpansionBoardActive = False
            self.m_eMode = RFE_Common.eMode.MODE_NONE
            self.fMinFreqMHZ = 0.0
            self.fMaxFreqMHZ = 0.0
            self.fMaxSpanMHZ = 0.0
            self.fRBWKHZ = 0.0
            self.fOffset_dB = 0.0
            self.nBaudrate = 0
            self.eModulations = RFE_Common.eModulation.MODULATION_NONE
            self.fThresholdDBM = 0.0

            self.nRFEGenSweepWaitMS = 0
            self.bRFEGenHighPowerSwitch = False
            self.nRFEGenPowerLevel = 0
            self.fRFEGenCWFreqMHZ = 0.0
            self.bRFEGenPowerON = False

            self.bRFEGenStartHighPowerSwitch = False
            self.bRFEGenStopHighPowerSwitch = False
            self.nRFEGenStartPowerLevel = 0
            self.nRFEGenStopPowerLevel = 1
            self.nRFGenSweepPowerSteps = 0

            self.eCalculator = RFE_Common.eCalculator.UNKNOWN

    @property
    def LineString(self):
        """Complete sting line with all configuration data
		"""
        return self.m_sLineString
    
    @property
    def Mode(self):
        """ Get current operational mode 
		"""
        return self.m_eMode 

    def ProcessReceivedString(self, sLine):
        """ Process sLine string and store all configuration data

        Parameters:
            sLine -- String with the standart configuration expected
        Returns:
            Boolean True it is possible to process and store configuration, False otherwise 
		"""
        bOk = True

        try:
            self.m_sLineString = sLine

            if (len(sLine) >= 60) and (sLine.startswith("#C2-F")):
                #Spectrum Analyzer mode
                self.fStartMHZ = int(sLine[6:13]) / 1000.0 #Note it comes in KHZ
                self.fStepMHZ = int(sLine[14:21]) / 1000000.0  #Note it comes in HZ
                self.fAmplitudeTopDBM = int(sLine[22:26])
                self.fAmplitudeBottomDBM = int(sLine[27:31])
                self.nFreqSpectrumSteps = int(sLine[32:36])
                self.bExpansionBoardActive = (sLine[37] == '1')
                self.m_eMode = RFE_Common.eMode(int(sLine[39:42]))
                self.fMinFreqMHZ = int(sLine[43:50]) / 1000.0
                self.fMaxFreqMHZ = int(sLine[51:58]) / 1000.0
                self.fMaxSpanMHZ = int(sLine[59:66]) / 1000.0

                if (len(sLine)) > 66:
                    self.fRBWKHZ = int(sLine[67:72])
                if (len(sLine)) > 72:
                    self.fOffset_dB = int(sLine[73:77])
                if (len(sLine) > 76):
                    self.eCalculator = RFE_Common.eCalculator(int(sLine[78:81]))
            elif ((len(sLine) >= 29) and (sLine[0:4] == "#C3-")):
                #Signal generator CW, SweepFreq and SweepAmp modes
                if (sLine[4] == '*'):
                    self.fStartMHZ = int(sLine[6:13]) / 1000.0 #Note it comes in KHZ
                    self.fRFEGenCWFreqMHZ = int(sLine[14: 21]) / 1000.0  #Note it comes in KHZ
                    self.nFreqSpectrumSteps = int(sLine[22:26])
                    self.fStepMHZ = int(sLine[27:34]) / 1000.0  #Note it comes in KHZ
                    self.bRFEGenHighPowerSwitch = (sLine[35] == '1')
                    self.nRFEGenPowerLevel = int(ord(sLine[37]) - 0x30)
                    self.nRFGenSweepPowerSteps = int(sLine[39:43])
                    self.bRFEGenStartHighPowerSwitch = (sLine[44] == '1')
                    self.nRFEGenStartPowerLevel = int(ord(sLine[46]) - 0x30)
                    self.bRFEGenStopHighPowerSwitch = (sLine[48] == '1')
                    self.nRFEGenStopPowerLevel = int(ord(sLine[50]) - 0x30)
                    self.bRFEGenPowerON = (sLine[52] == '1')
                    self.nRFEGenSweepWaitMS = int(sLine[54:59])
                    self.m_eMode = RFE_Common.eMode.MODE_NONE
                elif (sLine[4] == 'A'):
                    #Sweep Amplitude mode
                    self.fRFEGenCWFreqMHZ = int(sLine[6:13]) / 1000.0 #Note it comes in KHZ
                    self.nRFGenSweepPowerSteps = int(sLine[14:18])
                    self.bRFEGenStartHighPowerSwitch = (sLine[19] == '1')
                    self.nRFEGenStartPowerLevel = int(ord(sLine[21]) - 0x30)
                    self.bRFEGenStopHighPowerSwitch = (sLine[23] == '1')
                    self.nRFEGenStopPowerLevel = int(ord(sLine[25]) - 0x30)
                    self.bRFEGenPowerON = (sLine[27] == '1')
                    self.nRFEGenSweepWaitMS = int(sLine[29:34])
                    self.m_eMode = RFE_Common.eMode.MODE_GEN_SWEEP_AMP
                elif (sLine[4] == 'F'):
                    #Sweep Frequency mode
                    # r'#C3-F:0221000,0020,0000100,0,0,1,00150'
                    #       0 0      11   11      22 2 3 3    3
                    #       4 6      34   89      67 9 1 3    8
                    self.fStartMHZ = int(sLine[6:13]) / 1000.0 #Note it comes in KHZ
                    self.nFreqSpectrumSteps = int(sLine[14:18])
                    self.fStepMHZ = int(sLine[19:26]) / 1000.0  #Note it comes in KHZ
                    self.bRFEGenHighPowerSwitch = (sLine[27] == '1')
                    self.nRFEGenPowerLevel = int(ord(sLine[29]) - 0x30)
                    self.bRFEGenPowerON = (sLine[31] == '1')
                    self.nRFEGenSweepWaitMS = int(sLine[33:38])
                    self.m_eMode = RFE_Common.eMode.MODE_GEN_SWEEP_FREQ
                elif (sLine[4] == 'G'):
                    #Normal CW mode
                    # r'#C3-G:0432144,0432144,0020,0000100,0,0,0'
                    #       0         1      22   22      33 3 3
                    #       4         4      12   67      45 7 9
                    self.fRFEGenCWFreqMHZ = int(sLine[14:21]) / 1000.0  #Note it comes in KHZ
                    self.nFreqSpectrumSteps = int(sLine[22:26])
                    self.fStepMHZ = int(sLine[27:34]) / 1000.0  #Note it comes in KHZ
                    self.bRFEGenHighPowerSwitch = (sLine[35] == '1')
                    self.nRFEGenPowerLevel = int(ord(sLine[37]) - 0x30)
                    self.bRFEGenPowerON = (sLine[39] == '1')
                    self.m_eMode = RFE_Common.eMode.MODE_GEN_CW
                else:
                    self.m_eMode = RFE_Common.eMode.MODE_NONE
                    bOk = False
            elif ((len(sLine) >= 10) and (sLine.startswith("#C4-F:"))):
                #Sniffer mode
                self.fStartMHZ = int(sLine[6:13]) / 1000.0 #note it comes in KHZ
                self.bExpansionBoardActive = (sLine[14] == '1')
                self.m_eMode = RFE_Common.eMode(int(sLine[16:19]))
                nDelay = int(sLine[20:25])
                self.nBaudrate = int(round(float(RFE_Common.CONST_FCY_CLOCK) / nDelay))   #FCY_CLOCK = 16 * 1000 * 1000
                self.eModulations = RFE_Common.eModulation(int(sLine[26:27]))
                self.fRBWKHZ = int(sLine[28:33])
                self.fThresholdDBM = (float)(-0.5 * float(sLine[34:37]))
            else:
                bOk = False
        except Exception as obEx:
            bOk = False
            print("Error in RFEConfiguration - ProcessReceivedString(): " + print(obEx))

        return bOk
