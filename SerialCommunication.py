import serial.tools.list_ports
from time import sleep
import sys
import atexit

class SerialCom:
    
    def __init__(self, data_queue, sensor_value):
        self.data_q = data_queue
        self.sensor_value = sensor_value

        ports = list(serial.tools.list_ports.comports()) # Detect arduino serial port
        for p in ports:
            SERIAL = p[0]
        print('Reading from serial port %s...' % SERIAL)
        self.ser = serial.Serial(SERIAL, 9600)
        atexit.register(self.shutdown) # on exit, resets the arduino, putting it back into standby mode

    def setup_serial(self, temperature, mode):
        
        self.ser.setDTR(False) # pulsing DTR resets the arduino
        sleep(0.022)
        self.ser.setDTR(True)
        self.ser.flushInput() # discard any serial previously sent by the arduino
        sleep(5) # wait for initialization

        for x in range(0, 9):
            if int(self.sensor_value[x])<100 and int(self.sensor_value[x])>9:
                self.sensor_value[x]= str(str(0) + str(self.sensor_value[x]))
            elif int(self.sensor_value[x])<10:
                self.sensor_value[x]= str(str(0) + str(0) + str(self.sensor_value[x]))
        ser_write = str(int(mode.value))
        for x in range(0, 9):
            ser_write = ser_write + str(int(temperature[x])) + str(self.sensor_value[x])
        self.ser.write(ser_write)
        sleep(2)


    def arduino(self,temperature,mode):
        self.setup_serial(temperature, mode)
        #flag = 0
        while True:
            ''' For testing the mode select
            flag = flag + 1
            if (flag >= 100):
                flag = 0
                if (mode.value == 1):
                    mode.value = 0
                else:
                    mode.value = 1
            '''
            if self.ser.inWaiting():
                #print('Receiving:')
                line = self.ser.readline()
                self.ser.flushInput()
                #data = [float(val) for val in line.split()]
                data = line.split()
                sleep(0.1)
                if (len(data) == 10):
                    if(int(data[0]) == 1):
                        print ('1 temperature sensor detected.')
                    else:
                        print (str(int(data[0])) + ' temperature sensors detected.')
                    for x in range(9):
                        if (str(data[x+1]) != '0000000000000000'):
                            print('    Vial ' + str(x) + ' Address:  ' + str(data[x+1]))
                else:
                    self.data_q.put(data)
                    ser_write = str(int(mode.value))
                    for x in range(0, 9):
                        ser_write = ser_write + str(int(temperature[x])) + str(self.sensor_value[x])
                    #print('Sending:')
                    #print(ser_write)
                    #print('Length: ' + str(len(ser_write)))
                    self.ser.write(ser_write)
                    sleep(2)

    def shutdown(self):
        self.ser.setDTR(False) # pulsing DTR resets the arduino
        sleep(0.022)
        self.ser.setDTR(True)
