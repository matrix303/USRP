import time
from collections import deque
from multiprocessing import Queue
from Queue import Empty

class AnalogPlot:
    
    # constr
    def __init__(self, data_queue, fig, maxLen):
        self.fig = fig
        self.data_q = data_queue
        self.maxLen = maxLen
        self.b = [deque([0.0]*int(self.maxLen)) for x in range(81)] ###
        self.d = [deque([0.0]*int(self.maxLen)) for x in range(81)] ###
        self.t = deque([0.0]*int(self.maxLen))
        self.t0 = time.time()
        self.timestr = time.strftime("%YY%mM%dD_%HH%MM%S")
        self.record = open(self.timestr+'.txt', 'w')

        # Create subplots
        self.s = [self.fig.add_subplot(2,5,x) for x in range(1,11)]
        self.t = [self.s[x].twinx() for x in range(10)]
        self.m = [self.s[x].twinx() for x in range(10)]
        self.fig.subplots_adjust(wspace=0.05,hspace=0.23,bottom=0.22,top=0.82,left= 0.1,right=0.87)

        # Frames
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
            self.s[x].set_xlim(0,self.maxLen-1)
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

        # Ticksflush
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
        if len(buf) < self.maxLen:
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
        print("\n")

    def update(self, frameNum):

        '''Update plot'''
        try:
            data = self.data_q.get(False)
            self.flush_data_q()
            if(len(data) == 81):
                self.add(data)
                for x in range(9): # Loop through the nine vials
                    for y in range(9): # Loop through the nine data values for each vial
                        self.d[x*9+y].set_data(range(int(self.maxLen)),self.b[x*9+y])

        except Empty:
            #print('.')
            data = None
