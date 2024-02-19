
import random
import numpy as np

from models import *


#
# Add your Filtering / Smoothing approach(es) here
#
class HMMFilter:
    def __init__(self, probs, tm, om, sm):
        self.__tm = tm
        self.__om = om
        self.__sm = sm
        self.__f = probs
        
        
    def filter(self, sensorR) :
        #print( self.__f)
        
        #...
        Od = self.__om.get_o_reading(sensorR)
        T = self.__tm.get_T_transp()
        self.__f = Od @ T @ self.__f
        self.__f /= np.sum(self.__f)
        return self.__f
    
    def forwardBackwardSmoothing(self, sensorR):
        #...
        forwardEstimate = self.filter(sensorR.pop(0))
        backwards = np.ones(self.__sm.get_num_of_states())
        for i in reversed(sensorR):
            Od = self.__om.get_o_reading(i)
            T = self.__tm.get_T()
            backwards = T @ Od @ backwards
        smooth = forwardEstimate * backwards
        smooth /= np.sum(smooth)

        return smooth

        
        
        
