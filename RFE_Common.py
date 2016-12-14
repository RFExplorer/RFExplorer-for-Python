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

from enum import Enum

CONST_RFEXPLORER_FIRMWARE_CERTIFIED = "01.15"  #Firmware version of RF Explorer which was tested and certified with this PC Client

CONST_FCY_CLOCK = 16 * 1000 * 1000   #RFECommunicator - public const UInt32 FCY_CLOCK = 16 * 1000 * 1000
CONST_MIN_AMPLITUDE_DBM = -120.0   #RFECommunicator - public const float MIN_AMPLITUDE_DBM = -120.0f
CONST_MAX_SPECTRUM_STEPS = 65535   #RFECommunicator - public const UInt16 MAX_SPECTRUM_STEPS = 65535
CONST_MAX_AMPLITUDE_DBM = 50.0  #RFECommunicator - public const float MAX_AMPLITUDE_DBM = 50.0f
CONST_MAX_ELEMENTS = (1000)     #This is the absolute max size that can be allocated
CONST_FILE_VERSION = 2         #File format constant indicates the latest known and supported file format
CONST_ACKNOWLEDGE = "#ACK"

CONST_RFGEN_MIN_FREQ_MHZ = 23.438
CONST_RFGEN_MAX_FREQ_MHZ = 6000

CONST_RESETSTRING = "(C) Ariel Rocholl "

#---------------------------------------------------------

class eModel(Enum): 
    """All possible RF Explorer model values
    """
    MODEL_433 = 0  
    MODEL_868 = 1
    MODEL_915 = 2
    MODEL_WSUB1G = 3
    MODEL_2400 = 4
    MODEL_WSUB3G = 5
    MODEL_6G = 6
    MODEL_RFGEN = 60
    MODEL_NONE = 0xFF

class eMode(Enum):
    """The current operational mode
	""" 
    MODE_SPECTRUM_ANALYZER = 0
    MODE_TRANSMITTER = 1
    MODE_WIFI_ANALYZER = 2
    MODE_TRACKING = 5
    MODE_SNIFFER = 6

    MODE_GEN_CW = 60
    MODE_GEN_SWEEP_FREQ = 61
    MODE_GEN_SWEEP_AMP = 62

    MODE_NONE = 0xFF

class eCalculator(Enum): 
    """The current configured calculator in the device
	"""
    NORMAL = 0
    MAX = 1
    AVG = 2
    OVERWRITE = 3
    MAX_HOLD = 4
    MAX_HISTORICAL = 5
    UNKNOWN = 0xff

class eModulation(Enum): 
    """Modulation being used 
	"""   
    MODULATION_OOK_RAW = 0 
    MODULATION_PSK_RAW = 1   
    MODULATION_OOK_STD = 2    
    MODULATION_PSK_STD = 3   
    MODULATION_NONE = 0xFF 

class eDSP(Enum):    
    """All possible DSP values
	"""
    DSP_AUTO = 0
    DSP_FILTER = 1
    DSP_FAST = 2
    DSP_NO_IMG = 3

#---------------------------------------------------------
