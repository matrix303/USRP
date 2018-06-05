import sys, serial, argparse
import numpy as np
import time
from time import sleep
from collections import deque
from multiprocessing import Queue, Process
from Queue import Empty
import matplotlib as mpl 
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import serial.tools.list_ports
import math


'''User Inputs______________________________________________________________________________________________________________________________________________

Vial #:            [0] [1] [2] [3] [4] [5] [6] [7] [8]'''
Nonereading_LB  = [716,840,704,900,900,900,900,900,900]
OD_value        = [0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8]     # desired OD sensor value (3 digits, 0.1-2.0)
temperature     = [ 37, 37, 37, 37, 37, 37, 37, 37, 37]     # desired vial temperature (2 digits)

maxLen = 100 # length of x-axis on plots
mode   = 1   # 1 for experiment, 2 for pump, 3 for test

'''_________________________________________________________________________________________________________________________________________________________'''


class Calibrations:

    def __init__(self):
        self.c_water=0.0584
        self.c_lb=-0.011
        self.c_empty=-0.1519

    def OD_to_Reading(self, Nonereading, OD):
        self.nonreading=Nonereading
        self.OD=OD
        self.b=int(self.nonreading/math.pow(10, 0.1757*self.OD*(self.OD+1)+self.c_lb))
    
        return self.b

    def Reading_to_OD(self, Nonereading, reading):
        self.nonreading=Nonereading
        self.reading=reading
        self.c=(math.sqrt((1+4*(np.log10(self.nonreading/self.reading)-self.c_lb)/0.1757))-1)/2

        return self.c

class SerialCom:
    
    def __init__(self, data_queue, sensor_value):
        self.data_q = data_queue
        self.sensor_value = sensor_value

    def setup_serial(self):
        ports = list(serial.tools.list_ports.comports()) #detect arduino serial port
        for p in ports:
            SERIAL = p[0]
        print('Reading from serial port %s...' % SERIAL)
        self.ser = serial.Serial(SERIAL, 9600)
        self.ser.setDTR(False) # pulsing DTR resets the arduino
        sleep(0.022)
        self.ser.setDTR(True)
        
        time.sleep(5) #wait for initialization

        for x in range(0, 9):
            if int(self.sensor_value[x])<100 and int(self.sensor_value[x])>9:
                self.sensor_value[x]= str(str(0) + str(self.sensor_value[x]))
            elif int(self.sensor_value[x])<10:
                self.sensor_value[x]= str(str(0) + str(0) + str(self.sensor_value[x]))

        ser_write = str(mode)
        for x in range(0, 9):
            ser_write = ser_write + str(temperature[x]) + str(self.sensor_value[x])
        self.ser.write(ser_write)
        time.sleep(2)


    def arduino(self):
        self.setup_serial()
        while True:
            if self.ser.inWaiting():
                line = self.ser.readline()
                #data = [float(val) for val in line.split()]
                data = line.split()
                if (len(data) == 10):
                    print (str(int(data[0])) + ' temperature sensors detected.')
                    for x in range(9):
                        if (str(data[x+1]) != '0000000000000000'):
                            print('    Vial ' + str(x) + ' Address:  ' + str(data[x+1]))
                else:
                    self.data_q.put(data)
            else:
                ser_write = str(mode)
                for x in range(0, 9):
                    ser_write = ser_write + str(temperature[x]) + str(self.sensor_value[x])
                self.ser.write(ser_write)
                

# plot class
class AnalogPlot:
    
    # constr
    def __init__(self, data_queue, fig):
        self.fig = fig
        self.data_q = data_queue
        self.b = [deque([0.0]*maxLen) for x in range(81)] ###
        self.d = [deque([0.0]*maxLen) for x in range(81)] ###
        self.t = deque([0.0]*maxLen)
        self.t0 = time.time()
        self.timestr = time.strftime("%YY%mM%dD_%HH%MM%S")
        self.record = open(self.timestr+'.txt', 'w')

        #create subplots
        self.s = [self.fig.add_subplot(2,5,x) for x in range(1,11)]
        self.t = [self.s[x].twinx() for x in range(10)]
        self.m = [self.s[x].twinx() for x in range(10)]
        self.fig.subplots_adjust(wspace=0.05,hspace=0.23,bottom=0.22,top=0.82,left= 0.1,right=0.87)

        # Frams
        for x in range(0,10):
            for axis in ['top','bottom','left','right']:
                self.s[x].spines[axis].set_color('gray')
                self.s[x].spines[axis].set_linewidth(2)
                self.m[x].spines[axis].set_color('gray')
                self.m[x].spines[axis].set_linewidth(2)
            self.s[x].set_axis_bgcolor('black')
            self.s[x].spines['right'].set_color('r')
            self.s[x].spines['left'].set_color('orange')
            self.m[x].spines['left'].set_color('orange')
            self.s[x].set_xlim(0,maxLen-1)
            self.s[x].set_ylim(0,1100) # OD reading
            self.t[x].set_ylim(20,45)   # Temperture axes
            self.m[x].set_ylim(0,5)  # motor on off
            self.m[x].set_yticks(range(0, 0, 1))
            self.s[x].tick_params(axis='y', color='orange', labelcolor='orange', width=1.5, length=4)
            self.s[x].tick_params(axis='x', color='gray', labelcolor='gray', width=1.5, length=4)
            self.t[x].tick_params(axis='y', color='r', labelcolor='r', width=1.5, length=4)   # Temperture color
            self.m[x].tick_params(axis='y', color='gray', labelcolor='gray', width=1.5,length=4) 
            self.s[x].grid(color='dimgray', linestyle='-', linewidth=0.5)

        # Left and Right Labels
        for x in range(0,2):   
            self.s[x*5].set_ylabel('OD Reading', color='orange')
            self.t[x*5+4].set_ylabel('Temperature (Celcius)',color='r')
            self.m[x*5+4].spines['right'].set_position(('axes', 1.3))
            self.m[x*5+4].spines['right'].set_color('gray')
            self.m[x*5+4].patch.set_visible(False)
            self.m[x*5+4].set_frame_on(True)
            self.m[x*5+4].set_ylabel('State', color='gray',y=0.1)
            self.m[x*5+4].set_yticks(range(0, 2, 1))
            self.m[x*5+4].spines['right'].set_bounds(0, 1)
            self.m[x*5+4].set_yticklabels(['OFF', 'ON'])
        
        # Plots
        for x in range(0,9):

            self.d[x*9], =self.s[x].plot([],[],'orange', label='OD')
            self.d[x*9+1], =self.s[x].plot([],[],'orange', ls='dashed', label='OD Set Point')
            self.d[x*9+2], =self.t[x].plot([],[],'r',label='Temperature')
            self.d[x*9+3], =self.t[x].plot([],[],'r', ls='dashed', label='Temperature Set Point')
            self.d[x*9+4], =self.m[x].plot([],[],'orange',label='LED')
            self.d[x*9+5], =self.m[x].plot([],[],'r',label='Heater')
            self.d[x*9+6], =self.m[x].plot([],[],'g',label='Stir Fan')
            self.d[x*9+7], =self.m[x].plot([],[],'b',label='Pump In')
            self.d[x*9+8], =self.m[x].plot([],[],'y',label='Pump Out')
            
            self.s[x].set_title('Vial '+ str(x), color='gray')

        self.s[7].set_xlabel('Time', color='gray', size=15)

        # Ticks
        a=[1,2,3,4,6,7,8,9]
        b=[0,1,2,3,5,6,7,8]
        c=[0,1,2,3,4]
        for x in range (len(a)):
            self.s[a[x]].set_yticklabels([])
            self.t[b[x]].set_yticklabels([])
            if x < 5 :
                self.t[c[x]].set_xticklabels([])

        # legends
        legend1=self.s[5].legend(bbox_to_anchor=(0.35, -0.29), loc=2, borderaxespad=0.)
        legend2=self.t[6].legend(bbox_to_anchor=(0.5, -0.29), loc=2, borderaxespad=0.)
        legend3=self.m[8].legend([self.d[76],self.d[77]],['Led','Heater'],bbox_to_anchor=(0, -0.29), loc=2, borderaxespad=0.)
        legend4=self.m[9].legend([self.d[78],self.d[79],self.d[80]],['Stir Fan','Pump In','Pump Out'], bbox_to_anchor=(0.05, -0.66), loc=3, borderaxespad=0.)
        legend=[legend1,legend2,legend3,legend4]
        for x in range (0,4):
            legend[x].get_frame().set_facecolor('black')
            for text in legend[x].get_texts():
                text.set_color('gray')

    def addToBuf(self, buf, val):
        if len(buf) < maxLen:
            buf.append(val)
        else:
            buf.pop()
            buf.appendleft(val)

    def add(self, data):
        for x in range(0,81):
            self.addToBuf(self.b[x], data[x])
        self.write_to_file(data)

    def flush_data_q(self):
        while not self.data_q.empty():
            self.data_q.get()

    def write_to_file(self, data):
        T = time.time() - self.t0
        print("Time:\t" + str(T) + "\n")
        for x in range(0,9):
            if (data[x*9] != '0'):
                self.record.write(str(T)+"\t"+str(x)+"\t"+str(data[x*9])+"\t"+str(data[x*9+1])+"\t"+str(data[x*9+2])+"\t"
                                  +str(data[x*9+3])+"\t"+str(data[x*9+4])+"\t"+str(data[x*9+5])+"\t"+str(data[x*9+6])+"\t"+str(data[x*9+7])+"\t"+str(data[x*9+8])+"\n")
                print("Vial " + str(x) + ":\t" + str(data[x*9])+"\t"+str(data[x*9+1])+"\t"+str(data[x*9+2])+"\t"
                                  +str(data[x*9+3])+"\t"+str(data[x*9+4])+"\t"+str(data[x*9+5])+"\t"+str(data[x*9+6])+"\t"+str(data[x*9+7])+"\t"+str(data[x*9+8])+"\n")

    def update(self, frameNum):

        '''Update plot'''
        try:
            data = self.data_q.get(False)
            self.flush_data_q()
            if(len(data) == 81):
                self.add(data)
                for x in range(9):
                    self.d[x*9].set_data(range(maxLen),self.b[x*9])
                    self.d[x*9+1].set_data(range(maxLen),self.b[x*9+1])
                    self.d[x*9+2].set_data(range(maxLen),self.b[x*9+2])
                    self.d[x*9+3].set_data(range(maxLen),self.b[x*9+3])
                    self.d[x*9+4].set_data(range(maxLen),self.b[x*9+4])
                    self.d[x*9+5].set_data(range(maxLen),self.b[x*9+5])
                    self.d[x*9+6].set_data(range(maxLen),self.b[x*9+6])
                    self.d[x*9+7].set_data(range(maxLen),self.b[x*9+7])
                    self.d[x*9+8].set_data(range(maxLen),self.b[x*9+8])

        except Empty:
            print('.')
            data = None
      
# main() function
if __name__ == '__main__':

    sensor_value=[100,100,100,100,100,100,100,100,100] # initailize sensor_value array


    for i in range(0,9):   # setup population level
        Cali=Calibrations()
        sensor_value[i]=Cali.OD_to_Reading(Nonereading_LB[i],OD_value[i])


    #ports = list(serial.tools.list_ports.comports()) #detect arduino serial port
    #for p in ports:
    #    SERIAL = p[0]
    
    #print('Reading from serial port %s...' % SERIAL)


    data_q = Queue() #queue that holds all data from arduino
  
    serialcom = SerialCom(data_q,sensor_value)
    arduino_process = Process(target = serialcom.arduino, args = ())
    arduino_process.start()

    # plot parameters
    #with mpl.rc_context({'toolbar':False}): 
    fig = plt.figure(facecolor='black',figsize=(16,9))
    fig.suptitle('Turbidostat Mode', fontsize=20,  color='gray',y=0.93)
    
    analogPlot = AnalogPlot(data_q, fig)

    print('plotting data...')
    
    time.sleep(10)

    print('starting animation...')


    anim = animation.FuncAnimation(fig, analogPlot.update, interval = 10)

    # show plot
    plt.show()

    print('exiting.')
    plt.close()

