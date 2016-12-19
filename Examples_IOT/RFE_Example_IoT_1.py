#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

#============================================================================
#This is an example code for RFExplorer python functionality. 
#Display amplitude value in dBm and frequency in MHz of the maximum value of sweep data.
#The number of stored sweep data can be configurated by time
#============================================================================

import time
from datetime import datetime, timedelta
import RFExplorer

#---------------------------------------------------------
# Helper functions
#---------------------------------------------------------

def PrintPeak(objRFE):
    """This function prints the amplitude and frequency peak of the latest received sweep
	"""
    nInd = objRFE.SweepData.Count-1
    objSweepTemp = objRFE.SweepData.GetData(nInd)
    nStep = objSweepTemp.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = objSweepTemp.GetAmplitude_DBM(nStep)    #Get amplitude of the peak
    fCenterFreq = objSweepTemp.GetFrequencyMHZ(nStep)   #Get frequency of the peak

    print("Sweep[" + str(nInd)+"]: Peak: " + "{0:.3f}".format(fCenterFreq) + "MHz  " + str(fAmplitudeDBM) + "dBm")

#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

#SERIALPORT = None    #serial port data 
SERIALPORT = "/dev/ttyUSB0"    #serial port data 
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread
TOTAL_SECONDS = 10           #Initialize time span to display activity

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

try:
    #Find and show valid serial ports
    objRFE.GetConnectedPorts()    

    #Reset IoT board GPIO2 to High Level and GPIO3 to High Level
    objRFE.ResetIOT_HW(True)

    #Connect to available port
    if (objRFE.ConnectPort(SERIALPORT, BAUDRATE)):     
        #Wait for unit to notify reset completed
        while(objRFE.IsResetEvent):
            pass
        #Wait for unit to stabilize
        time.sleep(3)

        #Request RF Explorer configuration
        objRFE.SendCommand_RequestConfigData()
        #Wait to receive configuration and model details
        while(objRFE.ActiveModel == RFExplorer.RFE_Common.eModel.MODEL_NONE):
            objRFE.ProcessReceivedString(True)    #Process the received configuration

        #If object is an analyzer, we can scan for received sweeps
        if (objRFE.IsAnalyzer()):     
            print("Receiving data...")
            #Process until we complete scan time
            nLastDisplayIndex=0
            startTime=datetime.now()
            while ((datetime.now() - startTime).seconds<TOTAL_SECONDS):    
                #Process all received data from device 
                objRFE.ProcessReceivedString(True)
                #Print data if received new sweep only
                if (objRFE.SweepData.Count>nLastDisplayIndex):
                    PrintPeak(objRFE)      
                nLastDisplayIndex=objRFE.SweepData.Count
        else:
            print("Error: Device connected is a Signal Generator. \nPlease, connect a Spectrum Analyzer")
    else:
        print("Not Connected")
except Exception as obEx:
    print("Error: " + str(obEx))

#---------------------------------------------------------
# Close object and release resources
#---------------------------------------------------------

objRFE.Close()    #Finish the thread and close port
objRFE = None 
