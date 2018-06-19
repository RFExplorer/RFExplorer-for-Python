#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except, R0801
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

#======================================================================================
#This is an example code for RFExplorer python functionality. 
#Display amplitude in dBm and frequency in MHz of the maximum value of frequency range.
#In order to avoid USB issues, connect only RF Explorer Spectrum Analyzer to run this example
#It is not suggested to connect RF Explorer Signal Generator at the same time
#======================================================================================

import time
import RFExplorer

#---------------------------------------------------------
# Helper functions
#---------------------------------------------------------

def PrintPeak(objAnalazyer):
    """This function prints the amplitude and frequency peak of the latest received sweep
    """
    nIndex = objAnalazyer.SweepData.Count-1
    objSweepTemp = objAnalazyer.SweepData.GetData(nIndex)
    nStep = objSweepTemp.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = objSweepTemp.GetAmplitude_DBM(nStep)    #Get amplitude of the peak
    fCenterFreq = objSweepTemp.GetFrequencyMHZ(nStep)   #Get frequency of the peak

    print("Peak: " + "{0:.3f}".format(fCenterFreq) + "MHz  " + str(fAmplitudeDBM) + "dBm")

def ControlSettings(objAnalazyer):
    """This functions check user settings 
    """
    SpanSizeTemp = None
    StartFreqTemp = None
    StopFreqTemp =  None

    #print user settings
    print("User settings:" + "Span: " + str(SPAN_SIZE_MHZ) +"MHz"+  " - " + "Start freq: " + str(START_SCAN_MHZ) +"MHz"+" - " + "Stop freq: " + str(STOP_SCAN_MHZ) + "MHz")

    #Control maximum Span size
    if(objAnalazyer.MaxSpanMHZ <= SPAN_SIZE_MHZ):
        print("Max Span size: " + str(objAnalazyer.MaxSpanMHZ)+"MHz")
    else:
        objAnalazyer.SpanMHZ = SPAN_SIZE_MHZ
        SpanSizeTemp = objAnalazyer.SpanMHZ
    if(SpanSizeTemp):
        #Control minimum start frequency
        if(objAnalazyer.MinFreqMHZ > START_SCAN_MHZ):
            print("Min Start freq: " + str(objAnalazyer.MinFreqMHZ)+"MHz")
        else:
            objAnalazyer.StartFrequencyMHZ = START_SCAN_MHZ
            StartFreqTemp = objAnalazyer.StartFrequencyMHZ    
        if(StartFreqTemp):
            #Control maximum stop frequency
            if(objAnalazyer.MaxFreqMHZ < STOP_SCAN_MHZ):
                print("Max Start freq: " + str(objAnalazyer.MaxFreqMHZ)+"MHz")
            else:
                if((StartFreqTemp + SpanSizeTemp) > STOP_SCAN_MHZ):
                    print("Max Stop freq (START_SCAN_MHZ + SPAN_SIZE_MHZ): " + str(STOP_SCAN_MHZ) +"MHz")
                else:
                    StopFreqTemp = (StartFreqTemp + SpanSizeTemp)
    
    return SpanSizeTemp, StartFreqTemp, StopFreqTemp

#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

SERIALPORT = None    #serial port identifier, use None to autodetect  
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread
objRFE.AutoConfigure = False
SPAN_SIZE_MHZ = 100           #Initialize settings
START_SCAN_MHZ = 500
STOP_SCAN_MHZ = 900

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
        
        #If object is an analyzer, we can scan for received sweeps
        if(objRFE.IsAnalyzer()):
            #Control settings
            SpanSize, StartFreq, StopFreq = ControlSettings(objRFE)
            if(SpanSize and StartFreq and StopFreq):
                #set new frequency range
                objRFE.UpdateDeviceConfig(StartFreq, StopFreq)

                LastStartFreq = 0
                nInd = 0
                while (StopFreq<=STOP_SCAN_MHZ and StartFreq < StopFreq): 
                    #Process all received data from device 
                    while (objRFE.SweepData.Count<1):
                        objRFE.ProcessReceivedString(True)

                    #Print data if received new sweep and a different start frequency 
                    if(StartFreq != LastStartFreq):
                        nInd += 1
                        print("Freq range["+ str(nInd) + "]: " + str(StartFreq) +" - "+ str(StopFreq) + "MHz" )
                        PrintPeak(objRFE)
                        LastFreqStart = StartFreq

                    #set new frequency range
                    StartFreq = StopFreq
                    StopFreq = StartFreq + SpanSize

                    #Maximum stop/start frequency control
                    if (StopFreq > STOP_SCAN_MHZ):
                        StopFreq = STOP_SCAN_MHZ
                    if (StartFreq < StopFreq):
                        objRFE.UpdateDeviceConfig(StartFreq, StopFreq)

                        #Wait for new configuration to arrive (as it will clean up old sweep data)
                        objSweep=None
                        while ((objSweep is None) or objSweep.StartFrequencyMHZ!=StartFreq):
                            objRFE.ProcessReceivedString(True)
                            if (objRFE.SweepData.Count>0):
                                objSweep=objRFE.SweepData.GetData(objRFE.SweepData.Count-1)
            else:
                print("Error: settings are wrong.\nPlease, change and try again")
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
