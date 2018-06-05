import math

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
