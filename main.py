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

    def setup_process(self):
        progress = self.ids.setup_progress
        for x in range(100):
            progress.value = progress.value + 1
            sleep(0.05)

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
        vial_label = self.ids.vial_number
        vial_label.text = str(vial_number)

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
    Window.clearcolor = (0.5, 0.5, 0.5, 1) # sets background colour
    get_data_thread = Thread(target = get_data)
    get_data_thread.daemon = True
    get_data_thread.start()
    MainApp().run()
