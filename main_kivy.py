# to hide cursor, go to /home/pi, show hidden files, .kivy,
# config.ini, and delete the line 'touchring = show_cursor=true'
# under [modules]

# to show the plot data, you need to go to .kivy/garden/garden.graph/
# __init__.py and add False to line 176:
# 'self._fbo = Fbo(size=self.size, with_stencilbuffer=False)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.garden.graph import MeshLinePlot, SmoothLinePlot, MeshStemPlot, LinePlot
from threading import Thread
from kivy.clock import Clock
from time import sleep
from kivy.uix.progressbar import ProgressBar
# import argparse
import sys
from time import sleep
from multiprocessing import Queue, Process, Value, Array, Event
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from ctypes import c_char_p
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

empty_list = [0, 0, 0, 0, 0, 0, 0, 0, 0] # initial values for below arrays
vial_addresses = ['99','0000000000000000','0000000000000000','0000000000000000','0000000000000000','0000000000000000','0000000000000000','0000000000000000','0000000000000000','0000000000000000']
# Values stored in shared memory, which can be accessed inside of any parallel process
mode = Value('d', Chemostat_Mode)
new_mode = Value('d', Chemostat_Mode)
temperature = Array('i', Temperature_Set)
new_temperature = Array('i', Temperature_Set)
sensor_value = Array('i', empty_list)
new_sensor_value = Array('i', empty_list)
heat = Array('i', empty_list)
new_heat = Array('i', empty_list)
stir = Array('i', empty_list)
new_stir = Array('i', empty_list)
pump_in = Array('i', empty_list)
new_pump_in = Array('i', empty_list)
pump_out = Array('i', empty_list)
new_pump_out = Array('i', empty_list)
led_od = Array('i', empty_list)
new_led_od = Array('i', empty_list)
vial_list = Array(c_char_p,vial_addresses)
vial_q = Queue()

'''
# Use to test serial communication - temperature set point should spike up and down
def serialTest (new_temperature):
    while True:
        for x in range(9):
            if ( new_temperature[x] > 44 ):
                new_temperature[x] = 37
            else:
                new_temperature[x] = new_temperature[x] + 1
        sleep(2)
'''

exp_pressed = 0 # 1 when experiment is running, 0 when stopped

def get_data():
    data = 0
    global levels
    levels = []
    while True:
        if (data >= 25):
            data = 0
        else:
            data = data + 1
        if len(levels) >= 100:
            levels.pop()
        levels.insert(0, data)
        sleep(0.2)

class SetupScreen(Screen):

    #start progress bar by initiating clock schedule
    def setup_process(self):
        Clock.schedule_interval(self.progress_loop,0.12)
        serialcom = SerialCommunication.SerialCom(data_q,vial_list,vial_q)
        global arduino_process
        arduino_process = Process(target = serialcom.arduino, args = (mode,new_mode,temperature,new_temperature,sensor_value,new_sensor_value,heat,new_heat,stir,new_stir,pump_in,new_pump_in,pump_out,new_pump_out,led_od,new_led_od,))
        arduino_process.start()

    #progress bar schedule function
    def progress_loop(self,dt):
        setup_progress = self.ids.setup_progress

        #Check if progress bar is @ max; if not increase progress by 1
        if setup_progress.value >= setup_progress.max:
            Clock.unschedule(self.progress_loop) #Stops loop
            self.vial_detector()
            self.ids.cont.disabled = False
        else:
            setup_progress.value += 1

    def vial_detector(self):
        vials_label = self.ids.vials_label
        addresses_label = self.ids.vial_addresses
        while (vial_q.empty()):
            pass
        vial_list = vial_q.get()
        if (vial_list[0] == '1'):
            vials_label.text = "1 Vial Detected"
        else:
            vials_label.text = vial_list[0] + " Vials Detected"
        addresses_label.text = "Vial Addresses: "
        for x in range (1,9):
            if(str(vial_list[x]) != '0000000000000000'):
                addresses_label.text = addresses_label.text + "\nVial " + str(x) + " Address:  " + str(vial_list[x])



class HomeScreen(Screen):

    def __init__(self,**kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.temp_plot = SmoothLinePlot(color=[1, 0, 0, 1])
        self.temp_set_plot = MeshLinePlot(color=[0.7, 0, 0, 1])
        self.od_plot = SmoothLinePlot(color=[1, 0.5, 0, 1])
        self.od_set_plot = MeshLinePlot(color=[0.7, 0.3, 0, 1])
        self.led_plot = MeshLinePlot(color=[1, 1, 0, 1])
        self.peltier_plot = MeshLinePlot(color=[1, 0, 0.5, 1])
        self.stir_plot = MeshLinePlot(color=[0, 1, 0, 1])
        self.mot_in_plot = MeshLinePlot(color=[0, 0, 1, 1])
        self.mot_out_plot = MeshLinePlot(color=[0, 1, 1, 1])

    def toggle_exp(self, *args):
        exp = self.ids.experiment_button
        global exp_pressed
        if (exp_pressed == 0):
            exp_pressed = 1
            exp.background_color = [0.8,0,0,1] # changes button to red
            exp.text = "Stop Experiment"
            self.ids.graph.add_plot(self.temp_plot)
            self.ids.graph.add_plot(self.temp_set_plot)
            self.ids.graph.add_plot(self.od_plot)
            self.ids.graph.add_plot(self.od_set_plot)
            self.ids.graph.add_plot(self.led_plot)
            self.ids.graph.add_plot(self.peltier_plot)
            self.ids.graph.add_plot(self.stir_plot)
            self.ids.graph.add_plot(self.mot_in_plot)
            self.ids.graph.add_plot(self.mot_out_plot)
            Clock.schedule_interval(self.get_value, 0.2) # starts plotting values
        else:
            exp_pressed = 0
            exp.background_color = [0,0.8,0,1]
            exp.text = "Start Experiment"
            Clock.unschedule(self.get_value)

    def get_value(self, dt):
        self.temp_plot.points = [(i, j) for i, j in enumerate(levels)]
        self.temp_set_plot.points = [(i, j+5) for i, j in enumerate(levels)]
        self.od_plot.points = [(i, j/2) for i, j in enumerate(levels)]
        self.od_set_plot.points = [(i, j/2+5) for i, j in enumerate(levels)]
        self.led_plot.points = [(i, j+30) for i, j in enumerate(levels)]
        self.peltier_plot.points = [(i, j+40) for i, j in enumerate(levels)]
        self.stir_plot.points = [(i, j+10) for i, j in enumerate(levels)]
        self.mot_in_plot.points = [(i, j+15) for i, j in enumerate(levels)]
        self.mot_out_plot.points = [(i, j+20) for i, j in enumerate(levels)]

    def vial(self, vial_number): # changes the active vial
        self.ids.vial_number.text = str(vial_number)

    def exit(self):
        arduino_process.terminate()
        App.get_running_app().stop()

class ManualScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class ScreenManagement(ScreenManager):
    pass

class VialButton(Button):
    pass

class MainButton(Button):
    pass

class DataLabel(Label):
    pass

class MainApp(App):
    pass

if __name__ == "__main__":



    sensor_value = [100,100,100,100,100,100,100,100,100] # Initailize sensor_value array

    #test_process = Process(target = serialTest, args = (new_temperature,))
    #test_process.start()

    Cali = Calibrations.Calibrations()
    for i in range(0,9):
        sensor_value[i] = Cali.OD_to_Reading(Nonereading_LB[i],OD_value[i]) # Setup population level

    data_q = Queue() # Queue that holds all data from arduino

    Window.clearcolor = (0.5, 0.5, 0.5, 1) # sets background colour
    get_data_thread = Thread(target = get_data)
    get_data_thread.daemon = True
    get_data_thread.start()
    MainApp().run()
    print 'Goodbye :)'
