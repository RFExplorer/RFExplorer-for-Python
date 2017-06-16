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

import threading
import time

from RFExplorer import RFE_Common 
from RFExplorer.RFEConfiguration import RFEConfiguration
from RFExplorer.RFESweepData import RFESweepData

class ReceiveSerialThread(threading.Thread):
    """The secondary thread used to get data from USB/RS232 COM port
    """
    def __init__(self,objRFECommunicator, objQueue, objSerialPort, hQueueLock, hSerialPortLock):
        threading.Thread.__init__(self)
        self.variable = RFE_Common.CONST_MAX_AMPLITUDE_DBM
        self.m_objRFECommunicator = objRFECommunicator
        self.m_objQueue = objQueue
        self.m_objSerialPort = objSerialPort
        self.m_hQueueLock = hQueueLock
        self.m_hSerialPortLock = hSerialPortLock
        self.m_objCurrentConfiguration = None

    def run(self):
        #print("Starting Thread")
        self.ReceiveThreadfunc()
        #print("Exiting Thread")

    def __del__(self):
        pass
        #print("destroying thread object")

    def ReceiveThreadfunc(self):
        """Where all data coming from the device are processed and queued
		"""
        nBytes = 0
        nTotalSpectrumDataDumps = 0
        while self.m_objRFECommunicator.RunReceiveThread:
            strReceived = ""
            while (self.m_objRFECommunicator.PortConnected and self.m_objRFECommunicator.RunReceiveThread):
                sNewText = ""
                self.m_hSerialPortLock.acquire()
                try:
                    if (self.m_objSerialPort.is_open): 
                        #print("port open")
                        nBytes = self.m_objSerialPort.in_waiting
                        if (nBytes > 0):
                            sNewText = self.m_objSerialPort.read(nBytes).decode("latin_1")
                except Exception as obEx:
                    print("Serial port Exception: " + str(obEx))
                finally:
                    self.m_hSerialPortLock.release()
                if (len(sNewText) > 0):
                    if(self.m_objRFECommunicator.VerboseLevel > 5):
                        print(sNewText) 
                    strReceived += str(sNewText)
                    sNewText = ""
                if (len(strReceived) > 66*1024):
                    #Safety code, some error prevented the string from being processed in several loop cycles.Reset it.
                    if(self.m_objRFECommunicator.VerboseLevel > 5):
                        print("Received string truncated (" + len(strReceived) + ")")
                    strReceived = ""
                nLen = len(strReceived)
                if (nLen > 1):
                    if (self.m_objRFECommunicator.VerboseLevel > 9): 
                        print(strReceived)
                 
                    if (strReceived[0] == '#'):
                        nEndPos = strReceived.find("\r\n")
                        if (nEndPos >= 0):
                            sNewLine = strReceived[:nEndPos]
                            sLeftOver = strReceived[nEndPos + 2:]
                            strReceived = sLeftOver
                            #print(sNewLine)

                            if ((len(sNewLine) > 5) and ((sNewLine[:6] == "#C2-F:") or ((sNewLine[:4] == "#C3-") and (sNewLine[4] != 'M'))) or sNewLine.startswith("#C4-F:")):
                                if (self.m_objRFECommunicator.VerboseLevel > 5):
                                    print("Received Config:" + str(len(strReceived)))

                                #Standard configuration expected
                                objNewConfiguration = RFEConfiguration(None)
                                #print("sNewLine: "+ sNewLine)
                                if (objNewConfiguration.ProcessReceivedString(sNewLine)):
                                    self.m_objCurrentConfiguration = RFEConfiguration(objNewConfiguration)
                                    self.m_hQueueLock.acquire() 
                                    self.m_objQueue.put(objNewConfiguration)
                                    self.m_hQueueLock.release() 
                            else:
                                self.m_hQueueLock.acquire() 
                                self.m_objQueue.put(sNewLine)
                                self.m_hQueueLock.release() 

                    elif (strReceived[0] == '$'):

                        if (nLen > 4 and (strReceived[1] == 'C')):
                            nSize = 2 #account for cr+lf
                            #calibration data
                            if (strReceived[2] == 'c'): 
                                nSize+=int(strReceived[3]) + 4
                            elif (strReceived[2] == 'b'): 
                                nSize+=(int(strReceived[4]) + 1) * 16 + 10
                            if (nSize > 2 and nLen >= nSize):
                                nEndPos = strReceived.find("\r\n")
                                sNewLine = strReceived[:nEndPos]
                                sLeftOver = strReceived[nEndPos:]
                                strReceived = sLeftOver
                                #print(" [" + " ".join("{:02X}".format(ord(c)) for
                                #c in sNewLine) + "]")
                                self.m_hQueueLock.acquire() 
                                self.m_objQueue.put(sNewLine)
                                self.m_hQueueLock.release() 

                        elif (nLen > 2 and ((strReceived[1] == 'q') or (strReceived[1] == 'Q'))):
                            # Not sure what $q responses are, but I see them on the siggen
                            # and need to drop them to unplug the receive queue
                            nEndPos = strReceived.find("\r\n")
                            if (nEndPos >= 0):
                                sLeftOver = strReceived[nEndPos + 2:]
                                strReceived = sLeftOver
                                #print("sLeftOver: " + strReceived)

                        elif (nLen > 1 and (strReceived[1] == 'D')):
                            #This is dump screen data
                            if (self.m_objRFECommunicator.VerboseLevel > 5):
                                print("Received $D" + len(strReceived))

                            if (len(strReceived) >= (4 + 128 * 8)):
                                pass 
                        elif (nLen > 2 and ((strReceived[1] == "S") or (strReceived[1] == 's') or (strReceived[1] == 'z'))):
                            #Standard spectrum analyzer data
                            nReceivedLength = ord(strReceived[2])
                            nSizeChars = 3
                            if (strReceived[1] == 's'):
                                if (nReceivedLength == 0):
                                    nReceivedLength = 256
                                nReceivedLength *= 16
                            elif (strReceived[1] == 'z'):
                                nReceivedLength *= 256
                                nReceivedLength += int(strReceived[3])
                                nSizeChars+=1
                            if (self.m_objRFECommunicator.VerboseLevel > 9):
                                print("Spectrum data: " + str(nReceivedLength) + " " + str(nLen))
                            bLengthOK = (nLen >= (nSizeChars + nReceivedLength + 2))    #OK if received data >= header command($S,$s or $z) + data length + end of line('\n\r')
                            bFullStringOK = False
                            if (bLengthOK): ## Ok if data length are ok and end of line('\r\n') is in the correct place
                                            ## (at the end).  Prevents corrupted data
                                bFullStringOK = bLengthOK and (ord(strReceived[nSizeChars + nReceivedLength:][0]) == ord('\r')) and (ord(strReceived[nSizeChars + nReceivedLength:][1]) == ord('\n'))
                            if (self.m_objRFECommunicator.VerboseLevel > 9):
                                print("bLengthOK " + str(bLengthOK) + "bFullStringOK " + str(bFullStringOK) + " " + str(ord(strReceived[nSizeChars + nReceivedLength:][1])) + " - " + strReceived[nSizeChars + nReceivedLength:])
                            if (bFullStringOK):
                                nTotalSpectrumDataDumps+=1
                                if (self.m_objRFECommunicator.VerboseLevel > 9):
                                    print("Full dump received: " + str(nTotalSpectrumDataDumps))

                                #So we are here because received the full set of chars expected, and all them are apparently of valid characters
                                if (nReceivedLength <= RFE_Common.CONST_MAX_SPECTRUM_STEPS):
                                    sNewLine = "$S" + strReceived[nSizeChars:(nSizeChars + nReceivedLength)]
                                    if (self.m_objRFECommunicator.VerboseLevel > 9):
                                        print("New line:\n" + " [" + "".join("{:02X}".format(ord(c)) for c in sNewLine) + "]")
                                    if (self.m_objCurrentConfiguration):
                                        nSweepSteps = self.m_objCurrentConfiguration.nFreqSpectrumSteps
                                        objSweep = RFESweepData(self.m_objCurrentConfiguration.fStartMHZ, self.m_objCurrentConfiguration.fStepMHZ, nSweepSteps)
                                        if (objSweep.ProcessReceivedString(sNewLine, self.m_objCurrentConfiguration.fOffset_dB, self.m_objRFECommunicator.UseByteBLOB, self.m_objRFECommunicator.UseStringBLOB)):
                                            if (self.m_objRFECommunicator.VerboseLevel > 5):
                                                print(objSweep.Dump())
                                            if (nSweepSteps > 5): #check this is not an incomplete scan (perhaps from a stopped SNA tracking step)
                                                #Normal spectrum analyzer sweep data
                                                self.m_hQueueLock.acquire() 
                                                self.m_objQueue.put(objSweep)
                                                self.m_hQueueLock.release()
                                        else:
                                            self.m_hQueueLock.acquire() 
                                            self.m_objQueue.put(sNewLine)
                                            self.m_hQueueLock.release()
                                    else:
                                        if (self.m_objRFECommunicator.VerboseLevel > 5):
                                            print("Configuration not available yet. $S string ignored.")
                                else:
                                    self.m_hQueueLock.acquire() 
                                    self.m_objQueue.put("Ignored $S of size " + str(nReceivedLength) + " expected " + str(self.m_objCurrentConfiguration.nFreqSpectrumSteps))
                                    self.m_hQueueLock.release()
                                strReceived = strReceived[(nSizeChars + nReceivedLength + 2):]
                                if (self.m_objRFECommunicator.VerboseLevel > 5):
                                    sText = "New String: "
                                    nLength = len(strReceived)
                                    if (nLength > 10):
                                        nLength = 10
                                    if (nLength > 0):
                                        sText += strReceived[:nLength]
                                    print(sText)
                            elif (bLengthOK):
                                #So we are here because the string doesn't end with the expected chars, but has the right length.
                                #The most likely cause is a truncated string was received, and some chars are from next string, not
                                #this one therefore we truncate the line to avoid being much larger, and start over again next time.
                                nPosNextLine = strReceived.index("\r\n")
                                if (nPosNextLine >= 0):
                                    strReceived = strReceived[nPosNextLine + 2:] 

                    else:
                        nEndPos = strReceived.find("\r\n")
                        if (nEndPos >= 0):
                            sNewLine = strReceived[:nEndPos]
                            sLeftOver = strReceived[nEndPos + 2:]
                            strReceived = sLeftOver
                            self.m_hQueueLock.acquire() 
                            self.m_objQueue.put(sNewLine)
                            self.m_hQueueLock.release() 
                            if (self.m_objRFECommunicator.VerboseLevel > 9):
                                print("sNewLine: " + sNewLine)
                        elif (self.m_objRFECommunicator.VerboseLevel > 5):
                            print("DEBUG partial:" + strReceived)
                if(self.m_objRFECommunicator.Mode != RFE_Common.eMode.MODE_TRACKING):
                    time.sleep(0.01)
            time.sleep(0.5)
        #print("ReceiveThreadfunc(): closing thread...")
