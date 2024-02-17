
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

        
        
        
