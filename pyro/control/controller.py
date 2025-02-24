# -*- coding: utf-8 -*-
"""
Created on Mon Oct 22 08:40:31 2018

@author: alxgr
"""

import numpy as np

from pyro.dynamic import system

from pyro.analysis import phaseanalysis
from pyro.analysis import simulation
from pyro.analysis import graphical
from pyro.analysis import costfunction

###############################################################################
# Mother Controller class
###############################################################################

class StaticController():
    """ 
    Mother class for memoryless controllers
    ---------------------------------------
    r  : reference signal vector       k x 1
    y  : sensor signal vector          p x 1
    u  : control inputs vector         m x 1
    t  : time                          1 x 1
    ---------------------------------------
    u = c( y , r , t )
    
    """
    
    ###########################################################################
    # The two following functions needs to be implemented by child classes
    ###########################################################################
    
    
    ############################
    def __init__(self, k=1, m=1, p=1):
        """ """
        
        # Dimensions
        self.k = k   
        self.m = m   
        self.p = p
        
        # Label
        self.name = 'Static Controller'
        
        # Reference signal info
        self.ref_label = []
        self.ref_units = []
        
        for i in range(k):
            self.ref_label.append('Ref. '+str(i))
            self.ref_units.append('')
        
        self.r_ub = np.zeros(self.k) + 10 # upper bounds
        self.r_lb = np.zeros(self.k) - 10 # lower bounds
        
        # default constant reference
        self.rbar = np.zeros(self.k)
        
    
    #############################
    def c( self , y , r , t = 0 ):
        """ 
        Feedback static computation u = c( y, r, t)
        
        INPUTS
        y  : sensor signal vector          p x 1
        r  : reference signal vector       k x 1
        t  : time                          1 x 1
        
        OUTPUTS
        u  : control inputs vector         m x 1
        
        """
        
        u = np.zeros(self.m) # State derivative vector
        
        raise NotImplementedError
        
        return u
    
    #########################################################################
    # Default methods that can be overloaded in child classes
    #########################################################################
    
    #############################
    def t2r( self , t ):
        """ 
        Reference signal fonction u = t2u(t)
        
        INPUTS
        t  : time                     1 x 1
        
        OUTPUTS
        r  : controller reference vector    m x 1
        
        Defaul is a constant signal equal to self.rbar, can overload the
        with a more complexe reference signal time-function 
        
        """
        
        #Default is a constant signal
        r = self.rbar
        
        return r
    
    
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
        
        OUTPUTS
        u  : control inputs vector    m x 1
        
        """
        
        u = self.c( y , self.rbar , t )
        
        return u
    
    
    #############################
    def __add__(self, sys):
        """ 
        closed_loop_system = controller + dynamic_system
        """
        
        cl_sys = ClosedLoopSystem( sys , self )
        
        return cl_sys
    



###############################################################################
# Mother "Static controller + dynamic system" class
###############################################################################

class ClosedLoopSystem( system.ContinuousDynamicSystem ):
    """ 
    Dynamic system connected with a static controller
    ---------------------------------------------
    NOTE: 
    Ignore any feedthough in the plant to avoid creating algebraic loops
    This is only valid if the output function h is not a fonction of u
    New equations assume y = h(x,u,t) -- > y = h(x,t)

    """
    ############################
    def __init__(self, ContinuousDynamicSystem , StaticController ):
        """ """
        
        self.plant      = ContinuousDynamicSystem
        self.controller = StaticController
        
        ######################################################################
        # Check dimensions match
        if not (self.plant.m == self.controller.m ):
            raise NameError('Dimension mismatch between controller and' + 
            ' dynamic system for the input signal u')
        elif not (self.plant.p == self.controller.p ):
            raise NameError('Dimension mismatch between controller and' + 
            ' dynamic system for the output signal y')
        ######################################################################
        
        # Dimensions of global closed-loop dynamic system
        self.n = self.plant.n
        self.m = self.controller.k 
        self.p = self.plant.p
        
        # Labels
        self.name = ('Closed-Loop ' + self.plant.name + 
                     ' with ' + self.controller.name )
        self.state_label  = self.plant.state_label
        self.input_label  = self.controller.ref_label
        self.output_label = self.plant.output_label
        
        # Units
        self.state_units  = self.plant.state_units
        self.input_units  = self.controller.ref_units
        self.output_units = self.plant.output_units
        
        # Define the domain
        self.x_ub = self.plant.x_ub
        self.x_lb = self.plant.x_lb
        self.u_ub = self.controller.r_ub
        self.u_lb = self.controller.r_lb
        
        # Default State and inputs        
        self.xbar = self.plant.xbar
        self.ubar = self.controller.rbar
        
        ################################
        # Variables
        ################################
        
        # Initial value for simulations
        self.x0   = self.plant.x0
        
        # Result of last simulation
        self.traj = None
        
        # Cost function for evaluation
        # default is a quadratic cost function with diag Q and R matrices
        self.cost_function = costfunction.QuadraticCostFunction.from_sys(self)
        
    
    ###########################################################################
    def f( self , x , u , t ):
        """ 
        Continuous time foward dynamics evaluation dx = f(x,u,t)
        
        INPUTS
        x  : state vector             n x 1
        u  : control inputs vector    m x 1
        t  : time                     1 x 1
        
        OUTPUTS
        dx : state derivative vector  n x 1
        
        """
        
        dx = np.zeros(self.n) # State derivative vector
        
        r = u # input of closed-loop global sys is ref of the controller
        
        # Compute output signal
        y = self.plant.h( x, self.plant.ubar, t)
        
        # Compute control inputs
        u = self.controller.c( y, r, t)
        
        # Compute state derivatives
        dx = self.plant.f( x, u, t)
        
        return dx
    

    ###########################################################################
    def h( self , x , u , t ):
        """ 
        Output fonction y = h(x,u,t)
        
        INPUTS
        x  : state vector             n x 1
        u  : control inputs vector    m x 1
        t  : time                     1 x 1
        
        OUTPUTS
        y  : output derivative vector o x 1
        
        """
        
        #y = np.zeros(self.p) # Output vector
        
        # Using u = ubar to avoid algeabric loops
        
        y = self.plant.h( x , self.plant.ubar , t )
        
        return y
    
    
    ###########################################################################
    def t2u( self , t ):
        """ 
        Reference signal fonction u = t2u(t)
        
        INPUTS
        t  : time                     1 x 1
        
        OUTPUTS
        u  : control inputs vector    m x 1
        
        Defaul is a constant signal equal to self.ubar, can overload the
        with a more complexe reference signal time-function 
        
        """
        
        # Input of closed-loop global sys is ref of the controller
        u = self.controller.t2r(t)
        
        return u
    
    
    ###########################################################################
    def plot_phase_plane_closed_loop(self , x_axis = 0 , y_axis = 1 ):
        """ 
        Plot Phase Plane vector field of the system
        ------------------------------------------------
        
        blue arrows for the open-loop behavior
        red arrows  for the closed-loop behavior
        
        """

        pp = phaseanalysis.PhasePlot( self , x_axis , y_axis )
        
        pp.compute_grid()
        pp.plot_init()
        
        # Closed-loop Behavior
        pp.color = 'r'
        pp.compute_vector_field()
        pp.plot_vector_field()
        
        # Open-Loop Behavior
        pp.f     = self.plant.f
        pp.ubar  = self.plant.ubar
        pp.color = 'b'
        pp.compute_vector_field()
        pp.plot_vector_field()
        
        pp.plot_finish()
        
        return pp
        
    
    #############################
    def compute_trajectory(
        self, tf=10, n=10001, solver='ode'):
        """ 
        Simulation of time evolution of the system
        ------------------------------------------------
        tf : final time
        n  : time steps
        """

        sim = simulation.CLosedLoopSimulator(self, tf, n, solver)
        
        self.traj = sim.compute()

        return self.traj


    #############################################
    # Make graph function use the internal sys
    #############################################

    def get_plotter(self):
        return self.plant.get_plotter()

    def get_animator(self):
        return self.plant.get_animator()
    

    ###########################################################################
    def show(self, q , x_axis = 0 , y_axis = 1 ):
        """ Plot figure of configuration q """
        
        system.ContinuousDynamicSystem.show( self.plant , q , 
                                            x_axis = 0 , y_axis = 1  )
        
    
    ###########################################################################
    def show3(self, q ):
        """ Plot figure of configuration q """
        
        system.ContinuousDynamicSystem.show3( self.plant, q )
        
        
    ###########################################################################
    def plot_phase_plane_trajectory_closed_loop(self, x_axis=0, y_axis=1):
        """ 
        Plot Phase Plane vector field of the system and the trajectory
        ------------------------------------------------
        
        blue arrows for the open-loop behavior
        red arrows  for the closed-loop behavior
        
        
        """
        
        plotter = self.get_plotter()
        plotter.phase_plane_trajectory_closed_loop( self.traj, x_axis, y_axis)




###############################################################################
class DynamicController( StaticController ):
    """
    
    Mother class for controller with internal states and dynamics (memory)
    
    ex: integral action of a PID

    ----------------------------------------
    z  : controller internal states    l x 1
    r  : reference signal vector       k x 1
    y  : sensor signal vector          p x 1
    u  : control inputs vector         m x 1
    t  : time                          1 x 1
    -----------------------------------------
    
    Control law
    u  = c( z, y, r, t)
    
    Internal dynamic
    dz / dt  = b( z, y, r, t)
    
    """
    
    #############################
    def __init__(self, k, l, m, p):
        
        self.l = l
        self.m = m
        self.p = p
        self.k = k

        self.name = "Dynamic Controller"
        
        ############################
        # Reference signal info
        self.ref_label = []
        self.ref_units = []
        
        for i in range(k):
            self.ref_label.append('Ref. '+str(i))
            self.ref_units.append('')
        
        self.r_ub = np.zeros(self.k) + 10 # upper bounds
        self.r_lb = np.zeros(self.k) - 10 # lower bounds
        
        # default constant reference
        self.rbar = np.zeros(self.k)
        
        ###########################
        # Internal states info
        self.internal_state_label = []
        self.internal_state_units = []
        
        for i in range(l):
            self.internal_state_label.append('Internal state ' +str(i))
            self.internal_state_units.append('')
        
        self.z_ub = np.zeros(self.l) + 10 # upper bounds
        self.z_lb = np.zeros(self.l) - 10 # lower bounds
        
        # default constant reference
        self.zbar = np.zeros(self.l)
        
        # initial internal controller states
        self.z0   = np.zeros(self.l)
        
        

    #############################
    def c(self, z, y, r, t):
        """ 
        CONTROL LAW
        u = c( z, y, r, t)
        
        INPUTS
        z  : internal states               l x 1
        y  : sensor signal vector          p x 1
        r  : reference signal vector       k x 1
        t  : time                          1 x 1
        
        OUTPUTS
        u  : control inputs vector         m x 1
        
        """
        
        u = np.zeros( self.m ) 
        
        return u

    
    #############################
    def b(self, z, y, r, t):
        """ 
        INTERNAL CONTROLLER DYNAMIC
        dz/dt = b( z, y, r, t)
        
        INPUTS
        z  : internal states               l x 1
        y  : sensor signal vector          p x 1
        r  : reference signal vector       k x 1
        t  : time                          1 x 1
        
        OUTPUTS
        d z / dt  : time derivative of internal states        l x 1
        """
        
        dz = np.zeros( self.l )
        
        return dz
    
    
    #############################
    def cbar( self , y , t = 0 ):
        """ 
        Feedback static computation u = c( z = zbar, y, r = rbar, t) for
        default reference and internal states
        
        INPUTS
        y  : sensor signal vector     p x 1
        t  : time                     1 x 1
        
        OUTPUTS
        u  : control inputs vector    m x 1
        
        """
        
        u = self.c( self.zbar, y , self.rbar , t )
        
        return u
        
    
    #############################
    def __add__(self, sys):
        
        return DynamicClosedLoopSystem( sys, self)
    
        

##############################################################################
class DynamicClosedLoopSystem( ClosedLoopSystem ):
    """
    Closed loop system with Dynamic controller
    --------------------------------------------
    
    Global closed-loop system with physical plant states and virtual
    controller internal states
    
    x_global = [ x_plant ; z_controller ]
    
    """
    
    #######################################
    def __init__(self, plant, controller):
        
        # Check dimensions
        if plant.p != controller.p:
            raise ValueError("Controller inputs do not match system outputs")
        if plant.m != controller.m:
            raise ValueError("Controller outputs do not match system inputs")
            
            
        ########################
        #Remove cost funtion
        ########################
        
        plant.cost_function = None
        
        ClosedLoopSystem.__init__( self, plant, controller)

        # Add extra states that represent system memory
        self.n = self.plant.n + self.controller.l
        
        self.state_label = ( self.plant.state_label +
                             self.controller.internal_state_label )
        self.state_units = ( self.plant.state_units +
                             self.controller.internal_state_units )
        
        self.x_ub = np.concatenate([ self.plant.x_ub,
                                     self.controller.z_ub
                                    ], axis=0)
        self.x_lb = np.concatenate([ self.plant.x_lb,
                                     self.controller.z_lb
                                    ], axis=0)
        self.xbar = np.concatenate([ self.plant.xbar,
                                     self.controller.zbar
                                    ], axis=0)
        
        ################################
        # Variables
        ################################
        
        # Initial value for simulations
        self.x0   = np.concatenate([ self.plant.x0,
                                     self.controller.z0
                                    ], axis=0)
        
        # Result of last simulation
        self.traj = None
        
        # Cost function for evaluation
        # default is a quadratic cost function with diag Q and R matrices
        self.cost_function = None #costfunction.QuadraticCostFunction.from_sys(self)
        
            
    ######################################
    def f(self, x, u, t):
        """ 
        Continuous time foward dynamics evaluation dx = f(x,u,t)
        
        INPUTS
        x  : state vector             n x 1
        u  : control inputs vector    m x 1
        t  : time                     1 x 1
        
        OUTPUTS
        dx : state derivative vector  n x 1
        
        """
        
        x, z = self._split_states( x )

        # Input to global system interpreted as reference signal
        r = u

        # Eval current system output. Assume there is no feedforward term,
        # as it would cause an algebraic loop
        y = self.plant.h( x, self.plant.ubar, t)

        # input u to dynamic system evaluated by controller
        u = self.controller.c( z, y, r, t)
        
        # Time derivative of states
        dx = self.plant.f( x, u, t)
        dz = self.controller.b( z, y, r, t)

        dx = np.concatenate([ dx, dz], axis=0)
        assert dx.shape == (self.n,)
        
        return dx
    
    
    ######################################
    def fzbar(self, x_plant , u, t = 0):
        """ 
        Continuous time foward dynamics evaluation dx = f(x,u,t)
        
        with 
        z = zbar
        r = u
        
        INPUTS
        x  : state vector             plant.n x 1
        t  : time                     1 x 1
        
        OUTPUTS
        dx : state derivative vector  n x 1
        
        """
        
        # Input to global system interpreted as reference signal
        r = u

        # Eval current system output. Assume there is no feedforward term,
        # as it would cause an algebraic loop
        y = self.plant.h( x_plant, self.plant.ubar, t)

        # input u to dynamic system evaluated by controller
        u = self.controller.c( self.controller.zbar, y, r, t)
        
        # Time derivative of states
        dx = self.plant.f( x_plant, u, t)
        
        return dx
    
    
    ##########################################
    def h(self, x, u, t):
        """ 
        Output fonction y = h(x,u,t)
        
        INPUTS
        x  : state vector             n x 1
        u  : control inputs vector    m x 1
        t  : time                     1 x 1
        
        OUTPUTS
        y  : output derivative vector p x 1
        
        """
        
        x, z = self._split_states( x )
        
        y    = self.plant.h( x, u, t)
        
        return y
    
    
    #######################################
    def _split_states(self, x):
        """
        Separate full state vector into system and controller states
        
        """
        
        x_sys, x_ctl = x[:self.plant.n], x[self.plant.n:]
        assert x_ctl.shape == (self.controller.l,)
        
        return (x_sys, x_ctl)
    
    
    #############################
    def xut2q( self, x , u , t ):
        """ Compute configuration variables ( q vector ) """
        
        x , z = self._split_states( x )
        
        # Use the plant function
        q = self.plant.xut2q( x, u, t)
        
        return q
    
    
    #############################
    def compute_trajectory(
        self, tf=10, n=10001, solver='ode'):
        """ 
        Simulation of time evolution of the system
        ------------------------------------------------
        tf : final time
        n  : time steps
        """
        
        sim = simulation.DynamicCLosedLoopSimulator( self, tf, n, solver)
        
        self.traj = sim.compute()

        return self.traj
    
    
    #############################
    def plot_trajectory_with_internal_states(self, plot='x', **kwargs):
        """
        Plot time evolution of a simulation of this system
        ------------------------------------------------
        note: will call compute_trajectory if no simulation data is present

        """
        
        # Check if trajectory is already computed
        if self.traj == None:
            self.compute_trajectory()
            
        plotter = graphical.TrajectoryPlotter( self )
        plotter.plot( self.traj, plot, **kwargs)
        
    #############################
    def plot_internal_states_5(self, plot='z5', **kwargs):
        """
        Plot time evolution of a simulation of this system
        ------------------------------------------------
        note: will call compute_trajectory if no simulation data is present

        """
        
        # Check if trajectory is already computed
        if self.traj == None:
            self.compute_trajectory()
               
        plotter = graphical.TrajectoryPlotter( self )
        plotter.plot( self.traj, plot, **kwargs)
        
    #############################
    def plot_internal_states_8(self, plot='z8', **kwargs):
        """
        Plot time evolution of a simulation of this system
        ------------------------------------------------
        note: will call compute_trajectory if no simulation data is present

        """
        
        # Check if trajectory is already computed
        if self.traj == None:
            self.compute_trajectory()
               
        plotter = graphical.TrajectoryPlotter( self )
        plotter.plot( self.traj, plot, **kwargs)  
    
    ###########################################################################
    def plot_phase_plane_closed_loop( self , x_axis = 0 , y_axis = 1 ):
        """ 
        Plot Phase Plane vector field of the system
        ------------------------------------------------
        
        blue arrows for the open-loop behavior
        red arrows  for the closed-loop behavior
        
        """

        pp = phaseanalysis.PhasePlot( self.plant , x_axis , y_axis )
        
        pp.compute_grid()
        pp.plot_init()
        
        # Closed-loop Behavior
        pp.color = 'b'
        pp.compute_vector_field()
        pp.plot_vector_field()
        
        # Open-Loop Behavior
        pp.f     = self.fzbar    # assume default internal states
        pp.ubar  = self.ubar
        pp.color = 'r'
        pp.compute_vector_field()
        pp.plot_vector_field()
        
        pp.plot_finish()
        
        return pp


'''
#################################################################
##################          Main                         ########
#################################################################
'''


if __name__ == "__main__":     
    """ MAIN TEST """
    
    pass

    
