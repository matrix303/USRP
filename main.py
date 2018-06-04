# import argparse
import sys
from time import sleep
from multiprocessing import Queue, Process, Value, Array
import matplotlib as mpl 
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import Calibrations
import SerialCommunication
import AnalogPlot

'''User Inputs______________________________________________________________________________________________________________________________________________

Vial #:            [0] [1] [2] [3] [4] [5] [6] [7] [8]'''
Nonereading_LB  = [716,840,704,900,900,900,900,900,900]
OD_value        = [0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8]     # desired OD sensor value (3 digits, 0.1-2.0)
Temperature_Set = [ 37, 37, 37, 37, 37, 37, 37, 37, 37]     # desired vial temperature (2 digits)

maxLen          = 100   # length of x-axis on plots
Chemostat_Mode  = 1     # 1 for experiment, 2 for pump, 3 for test

'''_________________________________________________________________________________________________________________________________________________________'''

'''
# Use to test serial communication - temperature set point should spike up and down
def serialTest (temperature):
    while True:
        for x in range(9):
            if ( temperature[x] > 44 ):
                temperature[x] = 37
            else:
                temperature[x] = temperature[x] + 1
        sleep(1)
'''

def loading_status():
    sleep(9.5)
    print("Locating Vials - 25%")
    sleep(9.5)
    print("Locating Vials - 50%")
    sleep(9.5)
    print("Locating Vials - 75%")

if __name__ == '__main__':

    temperature = Array('i', Temperature_Set) # Stores values in shared memory, which can be accessed inside of any parallel process 
    mode = Value('d', Chemostat_Mode)

    sensor_value = [100,100,100,100,100,100,100,100,100] # Initailize sensor_value array

    #test_process = Process(target = serialTest, args = (temperature,))
    #test_process.start()

    Cali = Calibrations.Calibrations()
    for i in range(0,9):
        sensor_value[i] = Cali.OD_to_Reading(Nonereading_LB[i],OD_value[i]) # Setup population level

    data_q = Queue() # Queue that holds all data from arduino
  
    serialcom = SerialCommunication.SerialCom(data_q,sensor_value)
    arduino_process = Process(target = serialcom.arduino, args = (temperature,mode,))
    arduino_process.start()
    

    # Plot parameters
    #with mpl.rc_context({'toolbar':False}): 
    fig = plt.figure(facecolor='black',figsize=(16,9))
    fig.suptitle('Turbidostat Mode', fontsize=20,  color='gray',y=0.93)
    
    analogPlot = AnalogPlot.AnalogPlot(data_q, fig, maxLen)

    print('plotting data...')
    
    sleep(10)

    print('starting animation...')

    Process(target = loading_status).start()

    anim = animation.FuncAnimation(fig, analogPlot.update, interval = 10)

    # show plot
    plt.ion()
    plt.show()

    print("Exiting...")
    print("Goodbye :)")
