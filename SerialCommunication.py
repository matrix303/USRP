import serial.tools.list_ports
from time import sleep
import sys
import atexit

class SerialCom:

    def __init__(self, data_queue, vial_list, vial_q):
        self.data_q = data_queue
        self.vial_list = vial_list
        self.vial_q = vial_q

        ports = list(serial.tools.list_ports.comports()) # Detect arduino serial port
        for p in ports:
            SERIAL = p[0]
        print('Reading from serial port %s...' % SERIAL)
        self.ser = serial.Serial(SERIAL, 9600)
        atexit.register(self.shutdown) # on exit, resets the arduino, putting it back into standby mode

    def setup_serial(self, mode, temperature, sensor_value):

        self.ser.setDTR(False) # pulsing DTR resets the arduino
        sleep(0.022)
        self.ser.setDTR(True)
        self.ser.flushInput() # discard any serial previously sent by the arduino
        sleep(5) # wait for initialization

        for x in range(0, 9):
            if int(sensor_value[x])<100 and int(sensor_value[x])>9:
                sensor_value[x]= str(str(0) + str(sensor_value[x]))
            elif int(sensor_value[x])<10:
                sensor_value[x]= str(str(0) + str(0) + str(sensor_value[x]))
        ser_write = 'r' + 'm' + str(int(mode.value))
        for x in range(0, 9):
            ser_write = ser_write + 't' + str(x) + str(int(temperature[x])) + 'v' + str(x) + str(sensor_value[x])
        self.ser.write(ser_write)
        sleep(2)


    def arduino(self,mode,new_mode,temperature,new_temperature,sensor_value,new_sensor_value,heat,new_heat,stir,new_stir,pump_in,new_pump_in,pump_out,new_pump_out,led_od,new_led_od):
        self.setup_serial(mode,temperature,sensor_value)
        while True:
            if self.ser.inWaiting():
                line = self.ser.readline()
                self.ser.flushInput()
                #data = [float(val) for val in line.split()]
                data = line.split()
                #print('Receiving:')
                #print(data)
                sleep(0.1)
                if (len(data) == 10):
                    print data
                    self.vial_q.put(data)
                    if(int(data[0]) == 1):
                        print ('1 temperature sensor detected.')
                    else:
                        print (str(int(data[0])) + ' temperature sensors detected.')
                    for x in range(9):
                        if (str(data[x+1]) != '0000000000000000'):
                            print('    Vial ' + str(x) + ' Address:  ' + str(data[x+1]))
                else:
                    self.data_q.put(data) # save data in the queue

                    ser_write = '0'
                    if (mode.value != new_mode.value):
                        mode.value = new_mode.value
                        ser_write = 'm' + str(int(mode.value))
                    for x in range(0, 9):
                        if (temperature[x] != new_temperature[x]):
                            temperature[x] = new_temperature[x]
                            ser_write = ser_write + 't' + str(x) + str(int(temperature[x]))
                        if (sensor_value[x] != new_sensor_value[x]):
                            sensor_value[x] = new_sensor_value[x]
                            ser_write = ser_write + 'v' + str(x) + str(int(sensor_value[x]))
                        if (heat[x] != new_heat[x]):
                            heat[x] = new_heat[x]
                            ser_write = ser_write + 'h' + str(x) + str(int(heat))
                        if (stir[x] != new_stir[x]):
                            stir[x] = new_stir[x]
                            ser_write = ser_write + 's' + str(x) + str(int(stir[x]))
                        if (pump_in[x] != new_pump_in[x]):
                            pump_in[x] = new_pump_in[x]
                            ser_write = ser_write + 'i' + str(x) + str(int(pump_in[x]))
                        if (pump_out[x] != new_pump_out[x]):
                            pump_out[x] = new_pump_out[x]
                            ser_write = ser_write + 'o' + str(x) + str(int(pump_out[x]))
                        if (led_od[x] != new_led_od[x]):
                            led_od[x] = new_led_od[x]
                            ser_write = ser_write + 'l' + str(x) + str(int(led_od[x]))
                    if (ser_write != '0'):
                        #print('Sending:')
                        #print(ser_write)
                        #print('Length: ' + str(len(ser_write)))
                        self.ser.write(ser_write) # send serial
                        sleep(2)



    def shutdown(self):
        self.ser.setDTR(False) # pulsing DTR resets the arduino
        sleep(0.022)
        self.ser.setDTR(True)
