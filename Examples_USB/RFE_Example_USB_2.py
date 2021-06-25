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
from RFExplorer import RFE_Common 
import math

#---------------------------------------------------------
# Helper functions
#---------------------------------------------------------

def PrintPeak(objAnalazyer):
    """This function prints the amplitude and frequency peak of the latest received sweep
    """
    nIndex = objAnalazyer.SweepData.Count-1
    objSweepTemp = objAnalazyer.SweepData.GetData(nIndex)
    nStep = objSweepTemp.GetPeakDataPoint()      #Get index of the peak
    fAmplitudeDBM = objSweepTemp.GetAmplitude_DBM(nStep)    #Get amplitude of the peak
    fCenterFreq = objSweepTemp.GetFrequencyMHZ(nStep)   #Get frequency of the peak
    fCenterFreq = math.floor(fCenterFreq * 10 ** 3) / 10 ** 3   #truncate to 3 decimals

    print("     Peak: " + "{0:.3f}".format(fCenterFreq) + "MHz  " + str(fAmplitudeDBM) + "dBm")

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

#These values can be limited by specific RF Explorer Spectrum Analyzer model. 
#Check RFE SA Comparation chart from www.rf-explorer.com\models to know what
#frequency setting are available for your model
#These freq settings will be updated later in SA condition.
SPAN_SIZE_MHZ = 50           #Initialize settings
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
        print("Reseting device...")   
        #Reset the unit to start fresh
        objRFE.SendCommand("r")    
        #Wait for unit to notify reset completed
        while(objRFE.IsResetEvent):
            pass
        #Wait for unit to stabilize
        time.sleep(8)

        #Request RF Explorer configuration
        objRFE.SendCommand_RequestConfigData()

        #Wait to receive configuration and model details
        while(objRFE.ActiveModel == RFExplorer.RFE_Common.eModel.MODEL_NONE):
            objRFE.ProcessReceivedString(True)    #Process the received configuration

        #If object is an analyzer, we can scan for received sweeps
        if(objRFE.IsAnalyzer()):
            print("---- Spectrum Analyzer Example ----")
            #update frequency setting. This was added to be compatible with all RFE SA models
            START_SCAN_MHZ = objRFE.MinFreqMHZ
            STOP_SCAN_MHZ = START_SCAN_MHZ + 200
            #SPAN_SIZE_MHZ = 50 is the minimum span available for RF Explorer SA models

            #Control settings
            SpanSize, StartFreq, StopFreq = ControlSettings(objRFE)
            if(SpanSize and StartFreq and StopFreq):
                nInd = 0
                while (True): 
                    #Set new configuration into device
                    objRFE.UpdateDeviceConfig(StartFreq, StopFreq)

                    objSweep=None
                    #Wait for new configuration to arrive (as it will clean up old sweep data)
                    while(True):
                        objRFE.ProcessReceivedString(True);
                        if (objRFE.SweepData.Count>0):
                            objSweep=objRFE.SweepData.GetData(objRFE.SweepData.Count-1)

                            nInd += 1
                            print("Freq range["+ str(nInd) + "]: " + str(StartFreq) +" - "+ str(StopFreq) + "MHz" )
                            PrintPeak(objRFE)
                        if(math.fabs(objRFE.StartFrequencyMHZ - StartFreq) <= 0.001):
                                break
  
                    #set new frequency range
                    StartFreq = StopFreq
                    StopFreq = StartFreq + SpanSize
                    if (StopFreq > STOP_SCAN_MHZ):
                        StopFreq = STOP_SCAN_MHZ

                    if (StartFreq >= StopFreq):
                        break
            else:
                print("Error: settings are wrong.\nPlease, change and try again")
        else:
            print("---- Signal Generator Example ----")
            #request internal calibration data, if available
            objRFE.SendCommand("Cq")
            objRFE6GENCal = objRFE.GetRFE6GENCal() #Object to manage the calibration data from generator
            while (objRFE6GENCal.GetCalSize() < 0):    
                objRFE.ProcessReceivedString(True)    #Process the received configuration

            objRFE.RFGenCWFrequencyMHZ = 500;
            if(objRFE.ExpansionBoardActive):
                #Amplitude sweep
                objRFE.RFGenExpansionPowerDBM = -40
                objRFE.RFGenExpansionPowerStartDBM = -40
                objRFE.RFGenExpansionPowerStepDB = 5
                objRFE.RFGenExpansionPowerStopDBM = -20
                objRFE.RFGenStepWaitMS = 500
                sStartDBM = str(objRFE.RFGenExpansionPowerStartDBM)
                sStopDBM = str(objRFE.RFGenExpansionPowerStopDBM)
                sSteps = str(objRFE.RFGenExpansionPowerStepDB)
            else:
                objRFE.RFGenStartHighPowerSwitch = False
                objRFE.RFGenStopHighPowerSwitch = True
                objRFE.RFGenStartPowerLevel = 0
                objRFE.RFGenStopPowerLevel = 3
                objRFE.RFGenSweepSteps = 5
                objRFE.RFGenStepWaitMS = 500
                arrAmplitudeDBM = objRFE6GENCal.GetEstimatedAmplitudeArray(objRFE.RFGenCWFrequencyMHZ)
                sStartDBM = str(arrAmplitudeDBM[0]) #min 
                sStopDBM = str(arrAmplitudeDBM[len(arrAmplitudeDBM) - 1]) #max
                sSteps = str(objRFE.RFGenSweepSteps)


            print("Amplitude Sweep Settings = Start:" + sStartDBM + "dBm" + " - Stop:" + sStopDBM + "dBm" + 
                  " - Steps:" + sSteps + " - Delay:" + str(objRFE.RFGenStepWaitMS) + "ms" + " - CW:" + str(objRFE.RFGenCWFrequencyMHZ) + "MHz")

            print("Amplitude sweep ON")
            objRFE.SendCommand_GeneratorSweepAmplitude()
            time.sleep(5)
            objRFE.SendCommand_GeneratorRFPowerOFF()
            print("Amplitude sweep OFF")

            time.sleep(2)

            #Frequency sweep
            if(objRFE.ExpansionBoardActive):
                objRFE.RFGenExpansionPowerDBM = -40
                sPowerDBM = " - Power:" + str(objRFE.RFGenExpansionPowerDBM) + "dBm"               
            else:
                objRFE.RFGenHighPowerSwitch = False
                objRFE.RFGenPowerLevel = 0
                sPowerDBM = " - Power:" + str(objRFE.GetSignalGeneratorEstimatedAmplitude(objRFE.RFGenCWFrequencyMHZ)) + "dBm"
            objRFE.RFGenStartFrequencyMHZ = 495.0
            objRFE.RFGenStopFrequencyMHZ = 505.0
            objRFE.RFGenExpansionPowerDBM = -40.0
            objRFE.RFGenSweepSteps = 11
            objRFE.RFGenStepWaitMS = 500

            print("Frequency Sweep Settings = Start:" + str(objRFE.StartFrequencyMHZ) + "MHz" + " - Stop:" + str(objRFE.StopFrequencyMHZ) + "MHz" + 
                  " - Steps:" + str(objRFE.RFGenSweepSteps) + " - Delay:" + str(objRFE.RFGenStepWaitMS) + "ms" + sPowerDBM)

            print("Frequency sweep ON")
            objRFE.SendCommand_GeneratorSweepFreq()
            time.sleep(5)
            objRFE.SendCommand_GeneratorRFPowerOFF()
            print("Frequency sweep OFF")
    else:
        print("Not Connected")
except Exception as obEx:
    print("Error: " + str(obEx))

#---------------------------------------------------------
# Close object and release resources
#---------------------------------------------------------

objRFE.Close()    #Finish the thread and close port
objRFE = None 
