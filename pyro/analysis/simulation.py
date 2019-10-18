# -*- coding: utf-8 -*-
"""
Created on Fri Aug 07 11:51:55 2015

@author: agirard
"""

from collections import namedtuple

import numpy as np

import matplotlib.pyplot as plt

from scipy.integrate import odeint

from .graphical import TrajectoryPlotter

##################################################################### #####
# Simulation Objects
##########################################################################

class Trajectory():
    """Simulation data"""

    _dict_keys = ['x', 'u', 't', 'dx', 'y', 'r', 'J', 'dJ']

    def __init__(self, x, u, t, dx, y, r=None, J=None, dJ=None):
        """
        x:  array of dim = ( time-steps , sys.n )
        u:  array of dim = ( time-steps , sys.m )
        t:  array of dim = ( time-steps , 1 )
        y:  array of dim = ( time-steps , sys.p )
        """

        self.x = x
        self.u = u
        self.t = t
        self.dx = dx
        self.y = y
        self.r = r
        self.J = J
        self.dJ = dJ

        self._compute_size()

    def _asdict(self):
        return {k: getattr(self, k) for k in self._dict_keys}

    def save(self, name = 'trajectory_solution.npy' ):
        np.savez(name , **self._asdict())

    @classmethod
    def load(cls, name):
        try:
            # try to load as new format (np.savez)
            with np.load(name) as data:
                return cls(**data)

        except ValueError:
            # If that fails, try to load as "legacy" numpy object array
            data = np.load(name, allow_pickle=True)
            return cls(*data)

    def _compute_size(self):
        self.time_final = self.t.max()
        self.time_steps = self.t.size

        self.n = self.time_steps
        self.m = self.u.shape[1]

        # Check consistency between signals
        for arr in [self.x, self.y, self.u, self.dx, self.r, self.J, self.dJ]:
            if (arr is not None) and (arr.shape[0] != self.n):
                raise ValueError("Result arrays must have same length along axis 0")

    ############################
    def t2u(self, t ):
        """ get u from time """

        if t > self.time_final:
            raise ValueError("Got time t greater than final time")

            # Find time index
        i = (np.abs(self.t - t)).argmin()

        # Find associated control input
        u = self.u[i,:]

        return u

    ############################
    def t2x(self, t ):
        """ get x from time """

        # Find time index
        i = (np.abs(self.t - t)).argmin()

        # Find associated control input
        return self.x[i,:]


class Simulator:
    """Simulation Class for open-loop ContinuousDynamicalSystem

    Parameters
    -----------
    ContinuousDynamicSystem : Instance of ContinuousDynamicSystem
    u: callable
        Scalar function returning the input signal as a function of time
    tf : float
        final time for simulation
    n  : int
        number of time steps
    solver : {'ode', 'euler'}
    """
    ############################
    def __init__(
        self, ContinuousDynamicSystem, u, tf=10, n=10001, solver='ode', x0=None):

        self.cds = ContinuousDynamicSystem
        self.t0 = 0
        self.tf = tf
        self.n  = int(n)
        self.dt = ( tf + 0.0 - self.t0 ) / ( n - 1 )
        self.solver = solver
        self.x0 = np.asarray(x0).flatten()
        self.u = u

        if self.x0 is None:
            self.x0 = np.zeros( self.cds.n )

    ##############################

    def _u_wrapped(self, t):
        return np.asanyarray(self.u(t)).flatten()

    def compute(self):
        """ Integrate trought time """

        t  = np.linspace( self.t0 , self.tf , self.n )

        if self.solver == 'ode':
            # Wrap CDS f() ODE by including u(t)
            def func_u(x, t):
                return self.cds.f(x, self._u_wrapped(t), t)

            x_sol = odeint(func_u , self.x0 , t)

            # Compute inputs-output values
            y_sol = np.zeros(( self.n , self.cds.p ))
            u_sol = np.zeros((self.n,self.cds.m))
            dx_sol = np.zeros((self.n,self.cds.n))

            for i in range(self.n):
                ti = t[i]
                xi = x_sol[i,:]
                ui = self._u_wrapped(ti)

                dx_sol[i,:] = self.cds.f( xi , ui , ti )
                y_sol[i,:]  = self.cds.h( xi , ui , ti )
                u_sol[i,:]  = ui

        elif self.solver == 'euler':

            x_sol = np.zeros((self.n,self.cds.n))
            dx_sol = np.zeros((self.n,self.cds.n))
            u_sol = np.zeros((self.n,self.cds.m))
            y_sol = np.zeros((self.n,self.cds.p))

            # Initial State
            x_sol[0,:] = self.x0
            dt = ( self.tf + 0.0 - self.t0 ) / ( self.n - 1 )
            for i in range(self.n):

                ti = t[i]
                xi = x_sol[i,:]
                ui = self._u_wrapped(ti)

                if i+1<self.n:
                    dx_sol[i] = self.cds.f( xi , ui , ti )
                    x_sol[i+1,:] = dx_sol[i]*dt + xi

                y_sol[i,:] = self.cds.h( xi , ui , ti )
                u_sol[i,:] = ui

        sol = Trajectory(
            x=x_sol,
            u=u_sol,
            t=t,
            dx=dx_sol,
            y=y_sol
        )

        return sol