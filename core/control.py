# -*- coding: utf-8 -*-
"""
Created on Mon Oct 22 08:40:31 2018

@author: alxgr
"""

import numpy as np

###########################################################################################
# Mother Controller class
###########################################################################################

class StaticController:
    """ 
    Mother class for memoryless controllers
    ---------------------------------------
    r  : reference signal vector  k x 1
    y  : sensor signal vector     p x 1
    u  : control inputs vector    m x 1
    t  : time                     1 x 1
    ---------------------------------------
    u = c( y , r , t )
    
    """
    
    ###########################################################################################
    # The two following functions needs to be implemented by child classes
    ###########################################################################################
    
    
    ############################
    def __init__(self):
        """ """
        
        # System parameters to be implemented
        
        # Dimensions
        self.k = 1   
        self.m = 1   
        self.p = 1
        
        # default constant reference
        self.rbar = np.zeros(self.k)
        
        raise NotImplementedError
        
    
    #############################
    def c( self , y , r , t = 0 ):
        """ 
        Feedback static computation u = c(y,r,t)
        
        INPUTS
        y  : sensor signal vector     p x 1
        r  : reference signal vector  k x 1
        t  : time                     1 x 1
        
        OUPUTS
        u  : control inputs vector    m x 1
        
        """
        
        u = np.zeros(self.m) # State derivative vector
        
        raise NotImplementedError
        
        return u
    
    
    #########################################################################
    # No need to overwrite the following functions for child classes
    #########################################################################
    
    #############################
    def cbar( self , y , t = 0 ):
        """ 
        Feedback static computation u = c( y, r = rbar, t) for
        default reference
        
        INPUTS
        y  : sensor signal vector     p x 1
        t  : time                     1 x 1
        
        OUPUTS
        u  : control inputs vector    m x 1
        
        """
        
        u = self.c( y , self.rbar , t )
        
        return u
    
    
    
    
'''
#################################################################
##################          Main                         ########
#################################################################
'''


if __name__ == "__main__":     
    """ MAIN TEST """
    
    pass

    
