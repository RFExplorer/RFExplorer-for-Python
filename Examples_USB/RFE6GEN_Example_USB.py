#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except, R0801
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

#=====================================================================================
#This is an example code for RF Explorer RF6GEN Signal Generator python functionality. 
#Set frequency and power level to generate a frequency SWEEP and CW signal 
#in RFE6GEN Signal Generator.
#In order to avoid USB issues, connect only RF Explorer Signal Generator to run this example.
#It is not suggested to connect RF Explorer Spectrum Analyzer at the same time
#=====================================================================================

import time
import RFExplorer


#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

SERIALPORT = None    #serial port identifier, use None to autodetect 
BAUDRATE = 500000

objRFEGenerator = RFExplorer.RFECommunicator()     #Initialize object and thread

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

try:
    #Find and show valid serial ports
    objRFEGenerator.GetConnectedPorts()    

    #Connect to available port
    if (objRFEGenerator.ConnectPort(SERIALPORT, BAUDRATE)):
        #Reset the unit to start fresh
        objRFEGenerator.SendCommand("r")
        #Wait for unit to notify reset completed
        while(objRFEGenerator.IsResetEvent):
            pass
        #Wait for unit to stabilize
        time.sleep(3)
        
        #Request RF Explorer Generator configuration
        objRFEGenerator.SendCommand_RequestConfigData()
        #Wait to receive configuration and model details
        while(objRFEGenerator.ActiveModel == RFExplorer.RFE_Common.eModel.MODEL_NONE):
            objRFEGenerator.ProcessReceivedString(True)    #Process the received configuration

        #If object is a generator, we can continue the example
        if (objRFEGenerator.IsGenerator()):  
            #request internal calibration data, if available
            objRFEGenerator.SendCommand("Cq")
            objRFE6GENCal = objRFEGenerator.GetRFE6GENCal() #Object to manage the calibration data from generator
            while (objRFE6GENCal.GetCalSize() < 0):    
                objRFEGenerator.ProcessReceivedString(True)    #Process the received configuration
              
            #----------- Frequency Sweep Test Section -----------
            #Set Sweep Setting
            print("# New SWEEP settings...")
            objRFEGenerator.RFGenStartFrequencyMHZ = 400   
            objRFEGenerator.RFGenStopFrequencyMHZ = 450
            objRFEGenerator.RFGenSweepSteps = 25
            objRFEGenerator.RFGenStepWaitMS = 200
            print("SWEEP Settings = Start:" + str(objRFEGenerator.StartFrequencyMHZ) + "MHz" + " - Stop:" + str(objRFEGenerator.StopFrequencyMHZ) + "MHz" + 
                  " - Steps:" + str(objRFEGenerator.RFGenSweepSteps) + " - Delay:" + str(objRFEGenerator.RFGenStepWaitMS) + "ms" + " - Power:" + str(objRFEGenerator.GetSignalGeneratorEstimatedAmplitude(objRFEGenerator.RFGenCWFrequencyMHZ)) + "dBm")
            #Start Frequency Sweep
            objRFEGenerator.SendCommand_GeneratorSweepFreq()    
            #wait 5 seconds
            time.sleep(5)   
            #Stop Frequency Sweep
            objRFEGenerator.SendCommand_GeneratorRFPowerOFF()   
            print("Stop SWEEP")

            #----------- CW Test Section -----------
            #Set CW settings
            print("# New CW settings...")
            objRFEGenerator.RFGenCWFrequencyMHZ = 500
            objRFEGenerator.RFGenHighPowerSwitch = False
            objRFEGenerator.RFGenPowerLevel = 3
            print("Change CW settings --> Start:" + str(objRFEGenerator.RFGenCWFrequencyMHZ) + "MHz" + " - Power:" + str(objRFEGenerator.GetSignalGeneratorEstimatedAmplitude(objRFEGenerator.RFGenCWFrequencyMHZ)) + "dBm")
            #Start CW
            objRFEGenerator.SendCommand_GeneratorCW()
            time.sleep(5)
            #Change CW power
            print("# New CW power...")
            objRFEGenerator.RFGenPowerLevel = 0
            print("Change CW power = Start:" + str(objRFEGenerator.RFGenCWFrequencyMHZ) + "MHz" + " - Power:" + str(objRFEGenerator.GetSignalGeneratorEstimatedAmplitude(objRFEGenerator.RFGenCWFrequencyMHZ)) + "dBm")
            #Start new CW
            objRFEGenerator.SendCommand_GeneratorCW()
            time.sleep(5)
            #Change CW Frequency
            print("# New CW frequency...")
            objRFEGenerator.RFGenCWFrequencyMHZ = 510
            print("Change CW frequency = Start:" + str(objRFEGenerator.RFGenCWFrequencyMHZ) + "MHz" + " - Power:" + str(objRFEGenerator.GetSignalGeneratorEstimatedAmplitude(objRFEGenerator.RFGenCWFrequencyMHZ)) + "dBm")
            #Start new CW
            objRFEGenerator.SendCommand_GeneratorCW()
            time.sleep(5)
        else:
            print("Error: Device connected is a Spectrum Analyzer. \nPlease, connect a Signal Generator")
    else:
        print("Not Connected")
except Exception as obEx:
    print("Error: " + str(obEx))

#---------------------------------------------------------
# Close object and release resources
#---------------------------------------------------------

objRFEGenerator.Close()    #Finish the thread and close port
objRFEGenerator = None 
