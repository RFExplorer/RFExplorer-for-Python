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
            self.nFreqSpectrumDataPoints = objSource.nFreqSpectrumDataPoints
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

            self.fRFEGenExpansionPowerStepDBM = objSource.fRFEGenExpansionPowerStepDBM
            self.fRFEGenExpansionPowerStartDBM = objSource.fRFEGenExpansionPowerStartDBM
            self.fRFEGenExpansionPowerStopDBM = objSource.fRFEGenExpansionPowerStopDBM
        else:
            self.fStartMHZ = 0.0
            self.fStepMHZ = 0.0
            self.fAmplitudeTopDBM = 0.0
            self.fAmplitudeBottomDBM = 0.0
            self.nFreqSpectrumDataPoints = 0
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
            self.fRFEGenExpansionPowerDBM = -100.0

            self.bRFEGenStartHighPowerSwitch = False
            self.bRFEGenStopHighPowerSwitch = False
            self.nRFEGenStartPowerLevel = 0
            self.nRFEGenStopPowerLevel = 1
            self.nRFGenSweepPowerSteps = 0

            self.fRFEGenExpansionPowerStepDBM = 0.25
            self.fRFEGenExpansionPowerStartDBM = -100
            self.fRFEGenExpansionPowerStopDBM = 10

            self.eCalculator = RFE_Common.eCalculator.UNKNOWN

    @property
    def FreqSpectrumSteps(self):
        """Get frequency steps that is frequency points - 1
        """
        return int(self.nFreqSpectrumDataPoints - 1)


    @property
    def LineString(self):
        """Complete string line with all configuration data
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

            if ((len(sLine) >= 60) and (sLine.startswith("#C2-F:") or sLine.startswith("#C2-f:"))):
                #Spectrum Analyzer mode
                nPos = 6;
                self.fStartMHZ = int(sLine[nPos:(nPos + 7)]) / 1000.0 #Note it comes in KHZ
                nPos += 8;
                if (sLine[(nPos + 7)] == ','):
                    self.fStepMHZ = int(sLine[nPos:(nPos + 7)]) / 1000000.0  #Note it comes in HZ
                    nPos += 8;
                elif (sLine[(nPos + 8)] == ','):
                    self.fStepMHZ = int(sLine[nPos:(nPos + 8)]) / 1000000.0  #Note it comes in HZ
                    nPos += 9;
                self.fAmplitudeTopDBM = int(sLine[nPos:(nPos + 4)])
                nPos += 5;
                self.fAmplitudeBottomDBM = int(sLine[nPos:(nPos + 4)])
                nPos += 5;
                if (sLine.startswith("#C2-f:")):
                    self.nFreqSpectrumDataPoints = int(sLine[nPos:(nPos + 5)])
                    nPos += 1
                else:
                    self.nFreqSpectrumDataPoints = int(sLine[nPos:(nPos + 4)])
                nPos += 4; #we use this variable to keep state for long step number

                self.bExpansionBoardActive = (sLine[(nPos + 1)] == '1')
                nPos += 3
                self.m_eMode = RFE_Common.eMode(int(sLine[nPos:(nPos + 3)]))
                nPos += 4
                self.fMinFreqMHZ = int(sLine[nPos:(nPos + 7)]) / 1000.0
                nPos += 8
                self.fMaxFreqMHZ = int(sLine[nPos:(nPos + 7)]) / 1000.0
                nPos += 8
                self.fMaxSpanMHZ = int(sLine[nPos:(nPos + 7)]) / 1000.0
                nPos += 8
                if (len(sLine)) >= nPos:
                    self.fRBWKHZ = int(sLine[nPos:(nPos + 5)])
                nPos += 6
                if (len(sLine)) >= nPos:
                    self.fOffset_dB = int(sLine[nPos:(nPos + 4)])
                nPos += 5
                if (len(sLine) > nPos):
                    self.eCalculator = RFE_Common.eCalculator(int(sLine[nPos:(nPos + 3)]))
            elif ((len(sLine) >= 29) and (sLine[0:4] == "#C3-")):
                #Signal generator CW, SweepFreq and SweepAmp modes
                if (sLine[4] == '*'):
                    self.fStartMHZ = int(sLine[6:13]) / 1000.0 #Note it comes in KHZ
                    self.fRFEGenCWFreqMHZ = int(sLine[14: 21]) / 1000.0  #Note it comes in KHZ
                    self.nFreqSpectrumDataPoints = int(sLine[22:26]) + 1
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
                    # Positions:6,14,19,27,29,31,33
                    self.fStartMHZ = int(sLine[6:13]) / 1000.0 #Note it comes in KHZ
                    self.nFreqSpectrumDataPoints = int(sLine[14:18]) + 1
                    self.fStepMHZ = int(sLine[19:26]) / 1000.0  #Note it comes in KHZ
                    self.bRFEGenHighPowerSwitch = (sLine[27] == '1')
                    self.nRFEGenPowerLevel = int(ord(sLine[29]) - 0x30)
                    self.bRFEGenPowerON = (sLine[31] == '1')
                    self.nRFEGenSweepWaitMS = int(sLine[33:38])
                    self.m_eMode = RFE_Common.eMode.MODE_GEN_SWEEP_FREQ
                elif (sLine[4] == 'G'):
                    #Normal CW mode
                    # r'#C3-G:0432144,0432144,0020,0000100,0,0,0'
                    # Positions:14,22,27,35,37,39
                    self.fRFEGenCWFreqMHZ = int(sLine[14:21]) / 1000.0  #Note it comes in KHZ
                    self.nFreqSpectrumDataPoints = int(sLine[22:26]) + 1
                    self.fStepMHZ = int(sLine[27:34]) / 1000.0  #Note it comes in KHZ
                    self.bRFEGenHighPowerSwitch = (sLine[35] == '1')
                    self.nRFEGenPowerLevel = int(ord(sLine[37]) - 0x30)
                    self.bRFEGenPowerON = (sLine[39] == '1')
                    self.m_eMode = RFE_Common.eMode.MODE_GEN_CW
                else:
                    self.m_eMode = RFE_Common.eMode.MODE_NONE
                    bOk = False
            elif ((len(sLine) >= 20) and (sLine.startswith("#C5-"))):
                #Signal generator CW, SweepFreq and SweepAmp modes
                if(sLine[4] == '*') :
                    self.fStartMHZ = int(sLine[6:13]) / 1000.0 #Note it comes in KHZ
                    self.fRFEGenCWFreqMHZ = int(sLine[14:21]) / 1000.0  #Note it comes in KHZ
                    self.nFreqSpectrumDataPoints = int(sLine[22:26]) + 1
                    self.fStepMHZ = int(sLine[27:34]) / 1000.0  #Note it comes in KHZ
                    self.fRFEGenExpansionPowerDBM = float(sLine[35:40])
                    self.fRFEGenExpansionPowerStepDBM = float(sLine[41:46])
                    self.fRFEGenExpansionPowerStartDBM = float(sLine[47:52])
                    self.fRFEGenExpansionPowerStopDBM = float(sLine[53:58])
                    self.bRFEGenPowerON = (sLine[59] == '1')
                    self.nRFEGenSweepWaitMS = int(sLine[61:66])
                    self.m_eMode = RFE_Common.eMode.MODE_NONE
                elif(sLine[4] == 'A'):
                    #Sweep Amplitude mode
                    self.fRFEGenCWFreqMHZ = int(sLine[6:13]) / 1000.0 #note it comes in KHZ
                    self.fRFEGenExpansionPowerStepDBM = float(sLine[14:19])
                    self.fRFEGenExpansionPowerStartDBM = float(sLine[20:25])
                    self.fRFEGenExpansionPowerStopDBM = float(sLine[26:31])
                    self.bRFEGenPowerON = (sLine[32] == '1')
                    self.nRFEGenSweepWaitMS = int(sLine[34:39])
                    self.m_eMode = RFE_Common.eMode.MODE_GEN_SWEEP_AMP
                elif(sLine[4] == 'F'):
                    #Sweep Frequency mode
                    self.fStartMHZ = int(sLine[6:13]) / 1000.0 #note it comes in KHZ
                    self.nFreqSpectrumDataPoints = int(sLine[14:18]) + 1
                    self.fStepMHZ = int(sLine[19:26]) / 1000.0  #Note it comes in KHZ
                    self.fRFEGenExpansionPowerDBM = float(sLine[27:32])
                    self.bRFEGenPowerON = (sLine[33] == '1')
                    self.nRFEGenSweepWaitMS = int(sLine[35:40])
                    self.m_eMode = RFE_Common.eMode.MODE_GEN_SWEEP_FREQ
                elif(sLine[4] == 'G'):
                    #Normal CW mode
                    self.fRFEGenCWFreqMHZ = int(sLine[6:13]) / 1000.0  #Note it comes in KHZ
                    self.fRFEGenExpansionPowerDBM = float(sLine[14:19])
                    self.bRFEGenPowerON = (sLine[20] == '1')
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
