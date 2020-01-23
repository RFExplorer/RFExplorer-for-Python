#=======================================================================================
#This is an example code for RFExplorer python functionality.
#Contributed by https://github.com/xiaolu1990 - check with author for support
#=======================================================================================
#try:
#    while True:
#        input_value = input("please enter [G] for next step, [Q] for quit: ")
#        if input_value == "G":
#            print ("number is", num)
#            num += 1
#            continue
#    #        input_value = input("please enter [G] for next step: ")
#        elif input_value == "Q":
#            break
#        else:
#            input_value = input("please enter [G] for next step: ")
#except:
#    pass


#=======================================================================================

import numpy as np
import time
from datetime import datetime
import RFExplorer


def PrintPeak(objAnalazyer):
    """This function prints the amplitude and frequency peak of the latest received sweep
	"""
    nIndex = objAnalazyer.SweepData.Count-1
    objSweepTemp = objAnalazyer.SweepData.GetData(nIndex)
    nStep = objSweepTemp.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = objSweepTemp.GetAmplitude_DBM(nStep)    #Get amplitude of the peak
    fCenterFreq = objSweepTemp.GetFrequencyMHZ(nStep)   #Get frequency of the peak

    print("Sweep[" + str(nIndex)+"]: Peak: " + "{0:.3f}".format(fCenterFreq) + "MHz  " + str(fAmplitudeDBM) + "dBm")

    return fAmplitudeDBM
#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

SERIALPORT = None    #serial port identifier, use None to autodetect
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread
TOTAL_SECONDS = 5           #Initialize time span to display activity

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------


try:
    #Find and show valid serial ports
    objRFE.GetConnectedPorts()

    #Connect to available port
    if (objRFE.ConnectPort(SERIALPORT, BAUDRATE)):
        #Reset the unit to start fresh
        objRFE.SendCommand("r")
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

        while True:
            #create a list for saving the recorded values
            sample_value = []
            objRFE.ResetInternalBuffers()
            input_value = input("please enter [G] for next step, [Q] for quit: ")
            if input_value == "G":
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
                            peak_value = PrintPeak(objRFE)
                            sample_value.append(peak_value)
                        nLastDisplayIndex=objRFE.SweepData.Count
                    print ("The average values of the sampling values is:", round(np.mean(sample_value), 2), "dBm")
                else:
                    print("Error: Device connected is a Signal Generator. \nPlease, connect a Spectrum Analyzer")
                continue
            elif input_value == "Q":
                break
            else:
                input_value = input("please enter [G] for next step: ")
    else:
        print("Not Connected")
except Exception as obEx:
    print("Error: " + str(obEx))

#---------------------------------------------------------
# Close object and release resources
#---------------------------------------------------------

#objRFE.Close()    #Finish the thread and close port
objRFE = None
