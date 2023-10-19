## Made by Aditya on 3/16/2023

import numpy as np
from qiskit.circuit.random import *
from qiskit import *
from qiskit.tools.visualization import plot_histogram
from qiskit.tools.visualization import plot_bloch_multivector
from qiskit.tools.monitor import job_monitor
import qiskit.providers.aer.noise as NoiseModel
import time 
from math import pi
from qiskit.tools.monitor import job_monitor
from qiskit.opflow import CircuitOp, CircuitStateFn
from qiskit.opflow.state_fns import StateFn
from qiskit.opflow.expectations import PauliExpectation
from qiskit.opflow.converters import CircuitSampler
from qiskit.transpiler import CouplingMap

class CUSTCOM_Circ:
    def __init__(self):

        self.circ = QuantumCircuit(4)

    def gen_circ(self):
        
        """
        An instance of the supremacy circuit. 
        """
        self.circ.h(0)
        self.circ.h(1)
        self.circ.h(2)
        self.circ.h(3)

        self.circ.cz(0,1)
        self.circ.t(2)
        self.circ.t(3)

        self.circ.rx(theta=pi/2,qubit=0)
        self.circ.rx(theta=pi/2,qubit=1)

        self.circ.t(0)
        self.circ.t(1)

        self.circ.cz(0,2)

        self.circ.rx(pi/2,0)
        self.circ.cz(3,2)

        self.circ.t(0)
        self.circ.ry(pi/2,2)
        self.circ.ry(pi/2,3)

        self.circ.h(0)
        self.circ.t(2)
        self.circ.t(3)

        #self.circ.cz(1,3)

        self.circ.h(1)
        self.circ.h(2)
        self.circ.h(3)


        """
        ## Circuit number 4 with 4 qubits for gate cutting example
        self.circ.h(0)

        #self.circ.cx(0,1)
        #self.circ.rz(phi=pi/2,qubit=0)
        #self.circ.rx(theta=pi/2,qubit=1)
        self.circ.reset(0)
        #self.circ.x(0)
        #self.circ.rx(theta=pi,qubit=1)

        self.circ.cx(1,2)
        self.circ.cx(0,1)
        #self.circ.cx(2,3)
        #self.circ.cx(1,2)
        #self.circ.cx(3,4)        
        """
############################################################################################
        """
        ## Circuit number 3 with 3 qubits. 

        self.circ.cx(0,1)
        self.circ.cx(1,2)
        self.circ.cx(1,0)
        
        """
##############################################################################################
        """
        ## Circuit number 1 with 6 qubits.

        ## Layer 1
        self.circ.x(1)
        self.circ.u(2.68,2.82,0,4)

        ## Layer 2
        self.circ.i(1)
        self.circ.rzz(3.33,2,5)

        ## Layer 3
        self.circ.crz(1.49,0,3)
        self.circ.ry(0.119,4)
        self.circ.ry(5.64,5)

        ## Layer 4
        self.circ.rzz(pi/2,0,2)
        self.circ.u(4.68,0,0,3)
        self.circ.s(5)

        ## Layer 5
        self.circ.cu(1.96,1.2,4.44,0,0,3)
        self.circ.tdg(3)

        ## Layer 6
        self.circ.x(0)
        self.circ.crz(5.07,2,4)

        ## Layer 7
        self.circ.rzz(6.22,1,2)
        self.circ.h(3)
        self.circ.cnot(5,4)

        #self.circ.measure_all()
        """

###################################################################################################

        """
        ## Circuit #2 with 4 qubits. 
        # First Layer
        ######################################
        self.circ.h(0)
        self.circ.cx(2,1)
        self.circ.h(1)
        self.circ.cx(2,1)
        self.circ.h(2)
        self.circ.cx(2,3)
        self.circ.h(3)
        self.circ.cx(2,3)
        self.circ.h(2)
        self.circ.cx(2,0)
        self.circ.h(1)
        self.circ.cx(2,0)
        self.circ.h(0)
        self.circ.cx(1,0)
        self.circ.h(3)
        self.circ.cx(1,0)
        self.circ.h(0)
        self.circ.cx(1,3)
        self.circ.h(3)
        self.circ.cx(1,3)
        self.circ.h(2)
        #self.circ.cx(0,3)
        self.circ.h(1)
        #self.circ.cx(0,3)
        self.circ.h(0)
        #######################################

        """
        
        return self.circ
