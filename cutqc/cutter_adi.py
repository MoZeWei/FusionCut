from qiskit.dagcircuit.dagcircuit import DAGCircuit, DAGNode
from qiskit.circuit import Qubit,QuantumRegister
from qiskit.converters import circuit_to_dag, dag_to_circuit
import gurobipy as gp
import math
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library.standard_gates.i import IGate
from qiskit.circuit import Instruction, CircuitInstruction
from typing import Union
import numpy as np


class MIP_Model(object):
    def __init__(
        self,
        circuit,
        num_subcircuits,
        max_subcircuit_width,
         ):
        
        self.circuit_dag = circuit_to_dag(circuit)
        self.depth = self.circuit_dag.depth()
        self.num_subcirciuts = num_subcircuits
        self.max_sub_circuit_width = max_subcircuit_width
        self.num_org_circuit_width = self.circuit_dag.num_qubits()
        self.vertex = {}
        self.layers = {}
        self.layers_abs = {}
        self.layers_abs2 = {}
        self.num_vertices = self.circuit_dag.size()
        self.layer_partition = []
        self.gate_cutting = True # To be provided by the user later on. 

        self._dict_making() # New functio added by Aditya on 6/22/2023
        self._dependence() # New function added by Aditya on 6/22/2023
        self.model = gp.Model(name="cut_searching")
        self.model.params.OutputFlag = 0
        
        self._add_variables()
        self._add_constraints()

    def _dependence(self):

        """
        figure out the dependencies of each node. 
        """
        for y in range(self.layer_partition[self.depth-2]): # From the vertices in the first layer to the 2nd to last layer.
            current_vertex = self.vertex[y]
            for vertices in range(self.layer_partition[current_vertex["layer"]],self.layer_partition[current_vertex["layer"]+1]): # Next layer of vertices. 
                next_layer_vertex = self.vertex[vertices]
                if(len(current_vertex["qargs"]) == 2):
                    if(current_vertex["qargs"][0].index < current_vertex["qargs"][1].index):
                        for m in range(len(current_vertex["qargs"])): # Going over both the top and bottom wires if they are two qubits. 
                            if m == 0:
                                index_text = "Top_dependent"
                            else:
                                index_text = "Bottom_dependent"
                            for n in range(len(next_layer_vertex["qargs"])):# Going over the top and bottom qubits of next layer vertex. 
                                if current_vertex["qargs"][m].index == next_layer_vertex["qargs"][n].index:
                                    self.vertex[y][index_text] =  self.vertex[vertices]["Nid"]
                    else:
                        for m in range(len(current_vertex["qargs"])): # Going over both the top and bottom wires if they are two qubits. 
                            if m == 1:
                                index_text = "Top_dependent"
                            else:
                                index_text = "Bottom_dependent"
                            for n in range(len(next_layer_vertex["qargs"])):# Going over the top and bottom qubits of next layer vertex. 
                                if current_vertex["qargs"][m].index == next_layer_vertex["qargs"][n].index:
                                    self.vertex[y][index_text] =  self.vertex[vertices]["Nid"]
                else:
                    for m in range(len(current_vertex["qargs"])): # Going over both the top and bottom wires if they are two qubits. 
                            if m == 0:
                                index_text = "Top_dependent"
                            else:
                                index_text = "Bottom_dependent"
                            for n in range(len(next_layer_vertex["qargs"])):# Going over the top and bottom qubits of next layer vertex. 
                                if current_vertex["qargs"][m].index == next_layer_vertex["qargs"][n].index:
                                    self.vertex[y][index_text] =  self.vertex[vertices]["Nid"]
        return

    def _dict_making(self):
        
        """
        Starts the making of the dictonary to keep track of all the vertices and dependencies. 
        """
        count=0
        start_point = 0
        for i in range(self.circuit_dag.depth()):
            start_point += len(self.circuit_dag.front_layer())
            self.layer_partition.append(start_point)
            curr_vertices = self.circuit_dag.front_layer()
            for vertex in curr_vertices:
                self.vertex[count]={"Nid" : count,
                                    "layer":i,
                                    "qargs":vertex.qargs,
                                    "op" : vertex.op,
                                    }
                self.circuit_dag.remove_op_node(vertex)
                self.circuit_dag.apply_operation_back(op=vertex.op,qargs=vertex.qargs)
                count += 1
        for layers in range(self.depth):
            for circuits in range(self.num_subcirciuts):
                self.layers[layers] = {"c_%d" % (circuits):None}
                self.layers_abs[layers] = {"c_%d" % (circuits):None}
                self.layers_abs2[layers] = {"c_%d" % (circuits):None} 
        return

    def _add_variables(self):
        
        """
        Indicate if a vertex, V and its cut variables T and B are in some subcircuit C, Yv,c, Tv,c and Bv,c
        """
        for num_subcircuit in range(self.num_subcirciuts):
            for vertex in range(len(self.vertex)):
                if(len(self.vertex[vertex]["qargs"]) == 2):
                    self.vertex[vertex]["V_%d" % (num_subcircuit)]= self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("V_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["T_%d" % (num_subcircuit)]= self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("T_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["B_%d" % (num_subcircuit)]= self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("B_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["VabsTT_%d" % (num_subcircuit)] = self.model.addVar(lb= -1.5 , ub=1.5, vtype=gp.GRB.INTEGER,name=("VabsT_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["VabsBB_%d" % (num_subcircuit)] = self.model.addVar(lb= -1.5, ub=1.5, vtype=gp.GRB.INTEGER,name=("VabsB_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["VabsTB_%d" % (num_subcircuit)] = self.model.addVar(lb= -1.5 , ub=1.5, vtype=gp.GRB.INTEGER,name=("VabsT_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["VabsBT_%d" % (num_subcircuit)] = self.model.addVar(lb= -1.5, ub=1.5, vtype=gp.GRB.INTEGER,name=("VabsB_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["Vabs2TT_%d" % (num_subcircuit)] = self.model.addVar(lb= 0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("Vabs2T_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["Vabs2BB_%d" % (num_subcircuit)] = self.model.addVar(lb= 0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("Vabs2B_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["Vabs2TB_%d" % (num_subcircuit)] = self.model.addVar(lb= 0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("Vabs2T_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["Vabs2BT_%d" % (num_subcircuit)] = self.model.addVar(lb= 0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("Vabs2B_%d_%d" % (vertex,num_subcircuit)))
                else:
                    self.vertex[vertex]["D_%d" % (num_subcircuit)] = self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("D_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["Dabs_%d" % (num_subcircuit)] = self.model.addVar(lb= -1.5, ub=1.0, vtype=gp.GRB.INTEGER,name=("Dabs_%d_%d" % (vertex,num_subcircuit)))
                    self.vertex[vertex]["Dabs2_%d" % (num_subcircuit)] = self.model.addVar(lb= 0.0, ub=1.0, vtype=gp.GRB.BINARY,name=("Dabs2_%d_%d" % (vertex,num_subcircuit)))

        """
        Variable for top, Bottom, Gate and No wire cut.
        """
        for vertex in range(len(self.vertex)):
            if(len(self.vertex[vertex]["qargs"]) == 2):
                self.vertex[vertex]["Wv"] = self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY, name=("W_%d" % (vertex)))
                self.vertex[vertex]["Xv"] = self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY, name=("X_%d" % (vertex)))
                self.vertex[vertex]["Yv"] = self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY, name=("Y_%d" % (vertex)))
                self.vertex[vertex]["Uv"] = self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY, name=("U_%d" % (vertex)))

        """
        Max qubit per subcircuit. Divided up into layers Ix value. 
        """
        for layers in range(self.depth):
            for circuits in range(self.num_subcirciuts):
                self.layers[layers]["c_%d" % (circuits)] = self.model.addVar(lb=0.0, ub=self.max_sub_circuit_width+0.1,vtype=gp.GRB.INTEGER,name=("I_%d_%d" % (layers,circuits)))
                self.layers_abs[layers]["c_%d" % (circuits)] = self.model.addVar(lb=-self.max_sub_circuit_width-0.1, ub=self.max_sub_circuit_width+0.1,vtype=gp.GRB.INTEGER,name=("Iabs_%d_%d" % (layers,circuits)))
                self.layers_abs2[layers]["c_%d" % (circuits)] = self.model.addVar(lb=0.0, ub=self.max_sub_circuit_width+0.1,vtype=gp.GRB.INTEGER, name=("Iabs2_%d_%d" % (layers,circuits)))

        self.Dummy_var = self.model.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY)

        self.model.update()

    def _add_constraints(self):

        """
        The Dummy variable will always be zero. Just added it cause I dont know how to get past the none type and grb type error. Will look for it later. 
        """
        self.model.addConstr(
            self.Dummy_var,
            gp.GRB.EQUAL,
            0,
            )

        """
        If Gate cutting is disables and only circuit cutting is allowed. Added on 6/27/2023.
        """
        if(self.gate_cutting == False):
            for vertex in range(len(self.vertex)):
                if len(self.vertex[vertex]["qargs"]) == 2:
                    self.model.addConstr(self.vertex[vertex]["Yv"] == 0)

        """
        Constraits: 1) Wv + Uv <= 1
                    2) Xv + Uv <= 1
                    3) Yv + Uv <= 1
                    4) Wv + Xv + Yv + Uv >= 1
                    5) SUM(Vv,c) + Yv = 1 for all c in C.  
                    6) SUM(Tv,c) - Yv = 0 for all c in C.
                    7) SUM(Bv,c) - Yv = 0 for all c in C. 
                    8) Sum(Dv,c) = 1 for all c in C 
                    9) Tv,c + Bv,c <= 1
        """
        for vertex in range(len(self.vertex)):
            if len(self.vertex[vertex]["qargs"]) == 2:
                self.model.addConstr(self.vertex[vertex]["Wv"] + self.vertex[vertex]["Uv"],gp.GRB.LESS_EQUAL, 1) #1

                self.model.addConstr(self.vertex[vertex]["Xv"] + self.vertex[vertex]["Uv"], gp.GRB.LESS_EQUAL, 1) #2

                self.model.addConstr(self.vertex[vertex]["Yv"] + self.vertex[vertex]["Uv"], gp.GRB.LESS_EQUAL, 1) #3
                
                self.model.addConstr(self.vertex[vertex]["Yv"] + self.vertex[vertex]["Wv"] + self.vertex[vertex]["Xv"] + self.vertex[vertex]["Uv"], gp.GRB.GREATER_EQUAL, 1) #4
                
                self.model.addConstr(gp.quicksum([self.vertex[vertex]["V_%d" % (circuits)] for circuits in range(self.num_subcirciuts)]) + self.vertex[vertex]["Yv"], gp.GRB.EQUAL, 1) #5
                
                self.model.addConstr(gp.quicksum([self.vertex[vertex]["T_%d" % (circuits)] for circuits in range(self.num_subcirciuts)]) - self.vertex[vertex]["Yv"], gp.GRB.EQUAL, 0) #6

                self.model.addConstr(gp.quicksum([self.vertex[vertex]["B_%d" % (circuits)] for circuits in range(self.num_subcirciuts)]) - self.vertex[vertex]["Yv"], gp.GRB.EQUAL, 0) #7
                
                for circuits in range(self.num_subcirciuts):
                    self.model.addConstr(self.vertex[vertex]["T_%d" % (circuits)]  +   self.vertex[vertex]["B_%d" % (circuits)] <= 1) #9
            else:
                self.model.addConstr(gp.quicksum([self.vertex[vertex]["D_%d" % (circuits)] for circuits in range(self.num_subcirciuts)]), gp.GRB.EQUAL, 1) #8

        """
        Constraint: 10) Ix,c <= n 
                    11) Ix,c = SUM(for vertices in layers x)(2Vv,c + Bv,c + Tv,c + Dv,c)
        """
        for circuits in range(self.num_subcirciuts):
            start_num = 0
            for layers in range(self.depth):
                self.model.addConstr(self.layers[layers]["c_%d" % (circuits)] <= self.max_sub_circuit_width)
                grb_expression = self.Dummy_var
                for vertices in range(start_num,self.layer_partition[layers]):
                    if (len(self.vertex[vertices]["qargs"]) == 2):
                        grb_expression = grb_expression + 2 * self.vertex[vertices]["V_%d" % (circuits)] + self.vertex[vertices]["T_%d" % (circuits)] + self.vertex[vertices]["B_%d" % (circuits)]
                    else:
                         grb_expression = grb_expression + self.vertex[vertices]["D_%d" % (circuits)]
                start_num = self.layer_partition[layers]
                self.model.addConstr(grb_expression == self.layers[layers]["c_%d" % (circuits)])

        """
        Constraint: 12) Sum(Ix,c) = num_qubits for all c in a layer 
        """  
        for layers in range(self.depth):
            self.model.addConstr(gp.quicksum([self.layers[layers]["c_%d" % (circuits)] for circuits in range(self.num_subcirciuts)]) == self.num_org_circuit_width)

        
        """
        constraint: 13) --[1]--[2]-- for the following case: D2,c = D1,c
                    14) --[1]--[2]-- for the following case: 2W2 = SUMc(|D1,c - V2,c - T2,c|)
                               [2]
                        -------[2]--
                    15) -------[2]-- For the following case: 2X2 = SUMc(|D1,c - V2,c - B2,c|)
                               [2]
                        --[1]--[2]-- 
                    16) --[1]--[2]-- for the following case: V1,c = V2,c
                          [1]  [2]                         : T1,c = T2,c
                        --[1]--[2]--                       : B1,c = B2,c
                    17) --[1]--[2]-- for the following case: T1,c + V1,c = D2,c
                        --[1]
                        --[1]-------
                    18) --[1]------- for the following case: B1,c + V1,c = D2,c
                        --[1]
                        --[1]--[2]--
                    19) -------[2]-- for the following case: 2*X2 = SUMc(|V1,c + T1,c - V2,c - B2,c|)
                               [2]
                        --[1]--[2]-- 
                        --[1]
                        --[1]-------
                    20) --[1]------- for the following case: 2*W2 = SUMc(|V1,c + B1,c - V2,c - T2,c|)
                          [1]
                        --[1]--[2]--
                               [2]
                        -------[2]--
                    21) --[1]--[2]-- for the following case: 2*W2 = SUMc(|V1,c + T1,c - V2,c - T2,c|)
                          [1]  [2]
                        --[1]  [2]
                               [2]
                        -------[2]--
                    22) --[1]------- for the following case: 2*X2 = SUMc(|V1,c + B1,c - V2,c - B2,c|)
                          [1]
                          [1]  [2]
                          [1]  [2]
                        --[1]--[2]--
        """
        for vertex in range(self.layer_partition[self.depth -2]):
            if (len(self.vertex[vertex]["qargs"]) == 1):
                dependent = self.vertex[vertex]["Top_dependent"]
                if(len(self.vertex[dependent]["qargs"]) == 1): # 13--------------------------------------------------------------------------------------------------------------
                    for circuits in range(self.num_subcirciuts):
                        self.model.addConstr(self.vertex[dependent]["D_%d" % (circuits)] == self.vertex[vertex]["D_%d" % (circuits)]) 
                elif(self.vertex[vertex]["qargs"][0].index == self.vertex[dependent]["qargs"][0].index):
                    for circuits in range(self.num_subcirciuts): # 14---------------------------------------------------------------------------------------------------------------
                        self.model.addConstr(self.vertex[vertex]["Dabs_%d" % (circuits)] == 
                                             self.vertex[vertex]["D_%d" % (circuits)] - self.vertex[dependent]["V_%d" % (circuits)] - self.vertex[dependent]["T_%d" % (circuits)])
                        self.model.addConstr(self.vertex[vertex]["Dabs2_%d" % (circuits)] == gp.abs_(self.vertex[vertex]["Dabs_%d" % (circuits)]))
                    self.model.addConstr(2 * self.vertex[dependent]["Wv"] == gp.quicksum(self.vertex[vertex]["Dabs2_%d" % (circuits)] for circuits in range(self.num_subcirciuts)))
                elif(self.vertex[vertex]["qargs"][0].index == self.vertex[dependent]["qargs"][1].index):
                    for circuits in range(self.num_subcirciuts): #15--------------------------------------------------------------------------------------------------------------------
                        self.model.addConstr(self.vertex[vertex]["Dabs_%d" % (circuits)] == 
                                             self.vertex[vertex]["D_%d" % (circuits)] - self.vertex[dependent]["V_%d" % (circuits)] - self.vertex[dependent]["B_%d" % (circuits)])
                        self.model.addConstr(self.vertex[vertex]["Dabs2_%d" % (circuits)] == gp.abs_(self.vertex[vertex]["Dabs_%d" % (circuits)]))
                    self.model.addConstr(2 * self.vertex[dependent]["Xv"] == gp.quicksum(self.vertex[vertex]["Dabs2_%d" % (circuits)] for circuits in range(self.num_subcirciuts)))
            else:
                dependenttop = self.vertex[vertex]["Top_dependent"]
                dependentBottom = self.vertex[vertex]["Bottom_dependent"]
                if dependenttop == dependentBottom: #16-------------------------------------------------------------------------------------------------------------------------------------
                    for circuits in range(self.num_subcirciuts):
                        self.model.addConstr(self.vertex[dependenttop]["V_%d" % (circuits)] == self.vertex[vertex]["V_%d" % (circuits)])
                        self.model.addConstr(self.vertex[dependenttop]["T_%d" % (circuits)] == self.vertex[vertex]["T_%d" % (circuits)])
                        self.model.addConstr(self.vertex[dependenttop]["B_%d" % (circuits)] == self.vertex[vertex]["B_%d" % (circuits)])
                else:
                    if(len(self.vertex[dependenttop]["qargs"]) == 1): # 17------------------------------------------------------------------------------------------------------------------------
                        for circuits in range(self.num_subcirciuts):
                            self.model.addConstr(self.vertex[dependenttop]["D_%d" % (circuits)] == self.vertex[vertex]["V_%d" % (circuits)] + self.vertex[vertex]["T_%d" % (circuits)])
                    elif(self.vertex[vertex]["qargs"][0].index == self.vertex[dependenttop]["qargs"][1].index): # 19----------------------------------------------------------------------------------
                        for circuits in range(self.num_subcirciuts): 
                            self.model.addConstr(self.vertex[vertex]["VabsTB_%d" % (circuits)] == 
                                                self.vertex[vertex]["V_%d" % (circuits)] + self.vertex[vertex]["T_%d" % (circuits)]
                                                - self.vertex[dependenttop]["V_%d" % (circuits)] - self.vertex[dependenttop]["B_%d" % (circuits)])
                            self.model.addConstr(self.vertex[vertex]["Vabs2TB_%d" % (circuits)] == gp.abs_(self.vertex[vertex]["VabsTB_%d" % (circuits)]))
                        self.model.addConstr(2 * self.vertex[dependenttop]["Xv"] == gp.quicksum(self.vertex[vertex]["Vabs2TB_%d" % (circuits)] for circuits in range(self.num_subcirciuts)))
                    else: # 21----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                        for circuits in range(self.num_subcirciuts): 
                            self.model.addConstr(self.vertex[vertex]["VabsTT_%d" % (circuits)] == 
                                                self.vertex[vertex]["V_%d" % (circuits)] + self.vertex[vertex]["T_%d" % (circuits)]
                                                - self.vertex[dependenttop]["V_%d" % (circuits)] - self.vertex[dependenttop]["T_%d" % (circuits)])
                            self.model.addConstr(self.vertex[vertex]["Vabs2TT_%d" % (circuits)] == gp.abs_(self.vertex[vertex]["VabsTT_%d" % (circuits)]))
                        self.model.addConstr(2 * self.vertex[dependenttop]["Wv"] == gp.quicksum(self.vertex[vertex]["Vabs2TT_%d" % (circuits)] for circuits in range(self.num_subcirciuts)))

                    if(len(self.vertex[dependentBottom]["qargs"]) == 1): # 18------------------------------------------------------------------------------------------------------------------------
                        for circuits in range(self.num_subcirciuts):
                            self.model.addConstr(self.vertex[dependentBottom]["D_%d" % (circuits)] == self.vertex[vertex]["V_%d" % (circuits)] + self.vertex[vertex]["B_%d" % (circuits)])
                    elif(self.vertex[vertex]["qargs"][1].index == self.vertex[dependentBottom]["qargs"][0].index): # 20-----------------------------------------------------------------------------------
                        for circuits in range(self.num_subcirciuts): 
                            self.model.addConstr(self.vertex[vertex]["VabsBT_%d" % (circuits)] == 
                                                self.vertex[vertex]["V_%d" % (circuits)] + self.vertex[vertex]["B_%d" % (circuits)]
                                                - self.vertex[dependentBottom]["V_%d" % (circuits)] - self.vertex[dependentBottom]["T_%d" % (circuits)])
                            self.model.addConstr(self.vertex[vertex]["Vabs2BT_%d" % (circuits)] == gp.abs_(self.vertex[vertex]["VabsBT_%d" % (circuits)]))
                        self.model.addConstr(2 * self.vertex[dependentBottom]["Wv"] == gp.quicksum(self.vertex[vertex]["Vabs2BT_%d" % (circuits)] for circuits in range(self.num_subcirciuts)))
                    else: # 22--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                        for circuits in range(self.num_subcirciuts): 
                            self.model.addConstr(self.vertex[vertex]["VabsBB_%d" % (circuits)] == 
                                                self.vertex[vertex]["V_%d" % (circuits)] + self.vertex[vertex]["B_%d" % (circuits)]
                                                - self.vertex[dependentBottom]["V_%d" % (circuits)] - self.vertex[dependentBottom]["B_%d" % (circuits)])
                            self.model.addConstr(self.vertex[vertex]["Vabs2BB_%d" % (circuits)] == gp.abs_(self.vertex[vertex]["VabsBB_%d" % (circuits)]))
                        self.model.addConstr(2 * self.vertex[dependentBottom]["Xv"] == gp.quicksum(self.vertex[vertex]["Vabs2BB_%d" % (circuits)] for circuits in range(self.num_subcirciuts)))

        """
        Additional Constraints to limit the cut size from balloning too much. 
        """
        grb_expression_gate_limit = self.Dummy_var
        grb_expression_wire_limit = self.Dummy_var
        for vertex in range(len(self.vertex)):
            if(len(self.vertex[vertex]["qargs"]) == 2):
                grb_expression_wire_limit += self.vertex[vertex]["Xv"] + self.vertex[vertex]["Wv"]
                grb_expression_gate_limit += self.vertex[vertex]["Yv"]
        self.model.addConstr(grb_expression_gate_limit, gp.GRB.LESS_EQUAL, 60)
        self.model.addConstr(grb_expression_wire_limit, gp.GRB.LESS_EQUAL, 30)


        """
        Symmetry-breaking constraints (12)
        Force small-numbered vertices into small-numbered subcircuits:
            v0: in subcircuit 0
            v1: in subcircuit_0 or subcircuit_1
            v2: in subcircuit_0 or subcircuit_1 or subcircuit_2
            ...
        
        for vertex in range(self.num_subcirciuts - 1):
            if(len(self.vertex[vertex]["qargs"]) == 2):
                self.model.addConstr(gp.quicksum([self.vertex[vertex]["V_%d" % (circuits)] for circuits in range(vertex+1,self.num_subcirciuts)]) == 0)  
            else:
                self.model.addConstr(gp.quicksum([self.vertex[vertex]["D_%d" % (circuits)] for circuits in range(vertex+1,self.num_subcirciuts)]) == 0)
        
        """
        objective_fun = self.Dummy_var
        for vertices in range(len(self.vertex)):
            if len(self.vertex[vertices]["qargs"]) == 2:
                    objective_fun += 3 * self.vertex[vertices]["Wv"] + 3 * self.vertex[vertices]["Xv"] + 5 * self.vertex[vertices]["Yv"]
        
        #print("Objective function is :",objective_fun)
        self.model.setObjective(objective_fun, gp.GRB.MINIMIZE)
        self.model.update()

    def check_graph(self, n_vertices, edges):
        # 1. edges must include all vertices
        # 2. all u,v must be ordered and smaller than n_vertices
        vertices = set([i for (i, _) in edges])
        vertices |= set([i for (_, i) in edges])
        assert vertices == set(range(n_vertices))
        for u, v in edges:
            assert u < v
            assert u < n_vertices

    def solve(self):
        print('solving for %d subcircuits'%self.num_subcirciuts)
        print('model has %d variables, %d linear constraints,%d quadratic constraints, %d general constraints'
        % (self.model.NumVars,self.model.NumConstrs, self.model.NumQConstrs, self.model.NumGenConstrs))

        try:
            self.model.params.threads = 48
            self.model.Params.TimeLimit = 1200
            self.model.optimize() # This is where you are running the optimizer. 
        except (gp.GurobiError, AttributeError, Exception) as e:
            print("Caught: " + e.message)
        if self.model.solcount > 0:
            print("There are %d solutions" % (self.model.solcount))
            print("Model Objective value is ",self.model.objVal,"\n")
            print("Model Runtime is ",self.model.Runtime,"\n")
            feasible = True
        else:
            feasible = False

        """
        gate_count = 0
        wire_count = 0
        print("Model Objective value is ",self.model.objVal,"\n")
        print("Model Runtime is ",self.model.Runtime,"\n")
        for vertex in range(len(self.vertex)):
            if(len(self.vertex[vertex]["qargs"]) == 2):
                if(self.vertex[vertex]["Wv"].X >= 0.5):
                    print(" for vertex", vertex)
                    print("Acting on qubits %d and %d" % (self.vertex[vertex]["qargs"][0].index,self.vertex[vertex]["qargs"][1].index))
                    print("This vertex has been Wv cut")
                    wire_count += 1
                    print("\n")
                if(self.vertex[vertex]["Xv"].X >= 0.5):
                    print(" for vertex", vertex)
                    print("Acting on qubits %d and %d" % (self.vertex[vertex]["qargs"][0].index,self.vertex[vertex]["qargs"][1].index))
                    print("This vertex has been Xv cut")
                    wire_count += 1
                    print("\n")
                if(self.vertex[vertex]["Yv"].X >= 0.5):
                    print(" for vertex", vertex)
                    print("Acting on qubits %d and %d" % (self.vertex[vertex]["qargs"][0].index,self.vertex[vertex]["qargs"][1].index))
                    print("This vertex has been Gate cut")
                    gate_count += 1
                    print("\n")
                #if(self.vertex[vertex]["Uv"].X == 1.0):
                #    print("This vertex has not been cut")
                for circuits in range(self.num_subcirciuts):
                    if(self.vertex[vertex]["V_%d"%(circuits)].X >= 0.5):
                        print("The vertex V_%d_%d has been chosen" % (vertex,circuits))
                        print("Acting on qubits %d and %d" % (self.vertex[vertex]["qargs"][0].index,self.vertex[vertex]["qargs"][1].index))
                        print("\n")
                    if(self.vertex[vertex]["T_%d"%(circuits)].X >= 0.5):
                        print("The vertex T_%d_%d has been chosen" % (vertex,circuits))
                        print("Acting on qubits %d and %d" % (self.vertex[vertex]["qargs"][0].index,self.vertex[vertex]["qargs"][1].index))
                        print("\n")
                    if(self.vertex[vertex]["B_%d"%(circuits)].X >= 0.5):
                        print("The vertex B_%d_%d has been chosen" % (vertex,circuits))
                        print("Acting on qubits %d and %d" % (self.vertex[vertex]["qargs"][0].index,self.vertex[vertex]["qargs"][1].index))
                        print("\n")
                
        print("The gate_cut count is %d and wire_cut count is %d" % (gate_count,wire_count))
       
            else:
                print(" for vertex", vertex)
                print("Acting on qubits %d" % (self.vertex[vertex]["qargs"][0].index))
                for circuits in range(self.num_subcirciuts):
                    if(self.vertex[vertex]["D_%d"%(circuits)].X == 1.0):
                        print("The vertex D_%d_%d has been chosen" % (vertex,circuits))
                print("\n")
        
        print("Layers values according to subcircuits")
        for layers in range(self.depth):
            for circuits in range(self.num_subcirciuts):
                print("For layer %d for subcicuit %d, the layer value is %d, layerabs value %d and layerabs2 %d" % (layers, circuits, 
                                                                                                                    self.layers[layers]["c_%d" % (circuits)].X,
                                                                                                                    self.layers_abs[layers]["c_%d" % (circuits)].X, 
                                                                                                                    self.layers_abs2[layers]["c_%d" % (circuits)].X ))
            print("\n")
        """
        return feasible

class Placeholder(Instruction):
    def __init__(self, num_qubits, Vertex_id, label, label2): # Group: Mid circut measurment, initilization, Gate Cut, Label: H gate, Sdg, X gate, Top, Bottom, 
        self.name = "placeholder"
        self.vertex_id = Vertex_id
        self.label2 = label2 # Weather is control or target. Not revelant for single qubit gates. 
        super().__init__(self.name, num_qubits, 0, [], label=label)
    
    def replace(self, placeholder_label, instruction: Union[Instruction, QuantumCircuit]):
        if isinstance(instruction, QuantumCircuit):
            instruction = instruction.to_instruction()
        self._data = [CircuitInstruction(instruction, _inst[1], _inst[2]) if _inst[0].name == 'placeholder' and _inst[0].label == placeholder_label else _inst for _inst in self._data]

def Generic_subcircuit_generator(model:MIP_Model):

    # Cut Solution parameters
    subcircuits = {} #1
    gate_cuts = 0 #2
    wire_cuts = 0 #3
    
    # Getting the Number of Subcircuits, gate cuts and wire cuts.
    sub_circuit_count = []
    for circuits in range(model.num_subcirciuts):
        vertex_in_circuit_count = 0
        for vertex in range(len(model.vertex)):
            if(len(model.vertex[vertex]["qargs"]) == 2):
                if circuits == 0 :
                    if(model.vertex[vertex]["Wv"].X >= 0.5):
                        wire_cuts += 1
                    if(model.vertex[vertex]["Xv"].X >= 0.5):
                        wire_cuts += 1
                    if(model.vertex[vertex]["Yv"].X >= 0.5):
                        gate_cuts += 1
                if(model.vertex[vertex]["V_%d" % (circuits)].X >= 0.5):
                    vertex_in_circuit_count += 1
        sub_circuit_count.append(vertex_in_circuit_count)
    sub_count = np.count_nonzero(sub_circuit_count) #4 
    
    vertex_list = model.vertex
    list_qubits_per_subcircuit = []
    for circuits in range(model.num_subcirciuts):
        qubit_list = []
        subcircuits[circuits] = {"Sub_%d" % (circuits) : None}
        if sub_circuit_count[circuits] != 0:# Ensuring that there is atleast one two qubit vertex in a sub-circuit. 
            subcircuits[circuits]["Sub_%d" % (circuits)] = DAGCircuit()
            for vertex in model.vertex: # Figuring out which qubit belongs to which subcircuits. 
                if len(model.vertex[vertex]["qargs"]) == 2:
                    if model.vertex[vertex]["V_%d" % (circuits)].x >= 0.5:
                        if model.vertex[vertex]["qargs"][0].index not in qubit_list:
                            qubit_list.append(model.vertex[vertex]["qargs"][0].index)
                        if model.vertex[vertex]["qargs"][0].index not in qubit_list:
                            qubit_list.append(model.vertex[vertex]["qargs"][1].index)
                    elif model.vertex[vertex]["T_%d" % (circuits)].x >= 0.5:
                        if model.vertex[vertex]["qargs"][0].index not in qubit_list:
                            qubit_list.append(model.vertex[vertex]["qargs"][0].index)
                    elif model.vertex[vertex]["B_%d" % (circuits)].x >= 0.5:
                        if model.vertex[vertex]["qargs"][1].index not in qubit_list:
                            qubit_list.append(model.vertex[vertex]["qargs"][1].index)
                else:
                    if model.vertex[vertex]["D_%d" % (circuits)].x >= 0.5:
                        if model.vertex[vertex]["qargs"][0].index not in qubit_list:
                            qubit_list.append(model.vertex[vertex]["qargs"][0].index)
            
            qubit_list.sort() #Sorting all the qubits in decending order.
            #print(qubit_list)
            
            if len(qubit_list) <= model.max_sub_circuit_width: # Making the new sub-circuits with qubits upto max_subcircuit_width.
                register = QuantumRegister(size=len(qubit_list),name="Sub_%d" % (circuits))
                subcircuits[circuits]["Sub_%d" % (circuits)].add_qreg(register)
            else:
                register = QuantumRegister(size=model.max_sub_circuit_width,name="Sub_%d" % (circuits))
                subcircuits[circuits]["Sub_%d" % (circuits)].add_qreg(register)
           
            available_qubits = [x for x in range(model.max_sub_circuit_width)]
            qubit_map = [None]*model.max_sub_circuit_width
            for vertex in model.vertex: #Assigning the index for the vertices.
                #print(model.vertex[vertex]["op"].name)
                if len(qubit_list) <= model.max_sub_circuit_width: # If the number of qubits in subcircuit is less than the device size.  
                    if len(model.vertex[vertex]["qargs"]) == 2:
                        if model.vertex[vertex]["V_%d" % (circuits)].x >= 0.5: #If the gate is uncut.                        
                            qubit_1 = qubit_list.index(model.vertex[vertex]["qargs"][0].index)
                            qubit_2 = qubit_list.index(model.vertex[vertex]["qargs"][1].index)
                            index = [Qubit(register=register,index=qubit_1), Qubit(register=register,index=qubit_2)]                               
                        elif model.vertex[vertex]["T_%d" % (circuits)].x >= 0.5: # If the gate is cut for the top half
                            if model.vertex[vertex]["qargs"][0].index < model.vertex[vertex]["qargs"][1].index:
                                qubit_1 = qubit_list.index(model.vertex[vertex]["qargs"][0].index)
                                name = "Control"
                            else:
                                qubit_1 = qubit_list.index(model.vertex[vertex]["qargs"][1].index)
                                name = "Target"
                            index = [Qubit(register=register,index=qubit_1)]
                            subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,model.vertex[vertex]["Nid"],"Top",name),qargs=index)
                            continue
                        elif model.vertex[vertex]["B_%d" % (circuits)].x >= 0.5: # If the gate is cut for the top half
                            if model.vertex[vertex]["qargs"][0].index < model.vertex[vertex]["qargs"][1].index:
                                qubit_1 = qubit_list.index(model.vertex[vertex]["qargs"][1].index)
                                name = "Target"
                            else:
                                qubit_1 = qubit_list.index(model.vertex[vertex]["qargs"][0].index)
                                name = "Control"
                            index = [Qubit(register=register,index=qubit_1)]
                            subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,model.vertex[vertex]["Nid"],"Bottom",name),qargs=index)
                            continue
                        else: # The Vertex Does not belong to this Sub_Circuit. 
                            continue
                    
                    else: # For Single qubit gates. 
                        if model.vertex[vertex]["D_%d" % (circuits)].x >= 0.5:
                            qubit_1 = qubit_list.index(model.vertex[vertex]["qargs"][0].index)
                            index = [Qubit(register=register,index=qubit_1)]
                        else:
                            continue
                    
                    if len(model.vertex[vertex]["qargs"]) == 2:# Initilization After a Cut.   
                        if model.vertex[vertex]["V_%d" % (circuits)].x >= 0.5:
                            if model.vertex[vertex]["Wv"].x >= 0.5: # All measurments have ID of -1 and Initilization has ID -2. 
                                if model.vertex[vertex]["qargs"][0].index < model.vertex[vertex]["qargs"][1].index:
                                    subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-2,"initialization","initialization"),qargs=[index[0]])
                                else:
                                    subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-2,"initialization","initialization"),qargs=[index[1]])
                            if model.vertex[vertex]["Xv"].x >= 0.5: # All measurments have ID of -1 and Initilization has ID -2. 
                                if model.vertex[vertex]["qargs"][0].index < model.vertex[vertex]["qargs"][1].index:
                                    subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-2,"initialization","initialization"),qargs=[index[1]])
                                else:
                                    subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-2,"initialization","initialization"),qargs=[index[0]])
                
                    if model.vertex[vertex]["op"].name != "id":
                        subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=model.vertex[vertex]["op"],qargs=index) #Adding vertex to the sub_circuit.
                    
                    if (vertex < model.layer_partition[model.depth-2]): #Measurment before a cut. 
                        #print(vertex)
                        if (len(model.vertex[vertex]["qargs"]) == 2) :  
                            if (model.vertex[vertex]["V_%d" % (circuits)].x >= 0.5) :
                                if len(model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"]) == 2:
                                    if (model.vertex[model.vertex[vertex]["Top_dependent"]]["Xv"].x >= 0.5) or (model.vertex[model.vertex[vertex]["Top_dependent"]]["Wv"].x >= 0.5) :
                                        X = bool(model.vertex[vertex]["qargs"][0].index < model.vertex[vertex]["qargs"][1].index)
                                        Y = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"][0].index < model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"][1].index)
                                        W = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["Xv"].x >= 0.5)
                                        U = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["Wv"].x >= 0.5)
                                        Z_1 = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"][1].index == model.vertex[vertex]["qargs"][0].index)
                                        Z_2 = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"][1].index == model.vertex[vertex]["qargs"][1].index)
                                        if (X and W and ((Y and Z_1) or ((not Y) and (not Z_1)))) or ((X and U and ((Y and (not Z_1)) or ((not Y) and Z_1)))):
                                            subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-1,"measurment","measurment"),qargs=[index[0]])   
                                        elif ((not X) and W or ((Y and Z_2) or ((not Y) and (not Z_2)))) or ((not X) and U or (((not Y) and Z_2) or (Y and (not Z_2)))):
                                            subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-1,"measurment","measurment"),qargs=[index[1]])
                                if len(model.vertex[model.vertex[vertex]["Bottom_dependent"]]["qargs"]) == 2:
                                    if (model.vertex[model.vertex[vertex]["Bottom_dependent"]]["Xv"].x >= 0.5) or (model.vertex[model.vertex[vertex]["Bottom_dependent"]]["Wv"].x >= 0.5) :
                                        X = bool(model.vertex[vertex]["qargs"][0].index < model.vertex[vertex]["qargs"][1].index)
                                        Y = bool(model.vertex[model.vertex[vertex]["Bottom_dependent"]]["qargs"][0].index < model.vertex[model.vertex[vertex]["Bottom_dependent"]]["qargs"][1].index)
                                        W = bool(model.vertex[model.vertex[vertex]["Bottom_dependent"]]["Xv"].x >= 0.5)
                                        U = bool(model.vertex[model.vertex[vertex]["Bottom_dependent"]]["Wv"].x >= 0.5)
                                        Z_1 = bool(model.vertex[model.vertex[vertex]["Bottom_dependent"]]["qargs"][1].index == model.vertex[vertex]["qargs"][0].index)
                                        Z_2 = bool(model.vertex[model.vertex[vertex]["Bottom_dependent"]]["qargs"][1].index == model.vertex[vertex]["qargs"][1].index)
                                        if (X and W and ((Y and Z_1) or ((not Y) and (not Z_1)))) or ((X and U and ((Y and (not Z_1)) or ((not Y) and Z_1)))):
                                            subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-1,"measurment","measurment"),qargs=[index[1]])   
                                        elif ((not X) and W or ((Y and Z_2) or ((not Y) and (not Z_2)))) or ((not X) and U or (((not Y) and Z_2) or (Y and (not Z_2)))):
                                            subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-1,"measurment","measurment"),qargs=[index[0]])
                        else:
                            if (model.vertex[vertex]["D_%d" % (circuits)].x >= 0.5):
                                if len(model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"]) == 2:
                                    if (model.vertex[model.vertex[vertex]["Top_dependent"]]["Xv"].x >= 0.5) or (model.vertex[model.vertex[vertex]["Top_dependent"]]["Wv"].x >= 0.5):
                                        Y = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"][0].index < model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"][1].index)
                                        W = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["Xv"].x >= 0.5)
                                        U = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["Wv"].x >= 0.5)
                                        Z = bool(model.vertex[model.vertex[vertex]["Top_dependent"]]["qargs"][0].index == model.vertex[vertex]["qargs"][0].index)
                                        if (U and ((Y and Z) or ((not Y) and (not Z)))) or ((W and ((Y and (not Z)) or ((not Y) and Z)))):
                                            subcircuits[circuits]["Sub_%d" % (circuits)].apply_operation_back(op=Placeholder(1,-1,"measurment","measurment"),qargs=[index[0]])   
                else: # When there is qubit reuse in the sub_circuit and additional replaceable gates  needs to be added to be added. TO DO TONIGHT. 
                    if len(model.vertex[vertex]["qargs"]) == 2:
                        sub_qubit2 = model.vertex[vertex]["qargs"][1].index
                        if model.vertex[vertex]["qargs"][0].index < model.max_sub_circuit_width:
                            qubit_1 = qubit_list.index(model.vertex[vertex]["qargs"][0].index)
                    continue
                
                
                # Add Additional gates here if the vertex infront has been cut. 
        list_qubits_per_subcircuit.append(qubit_list)
    
    print(list_qubits_per_subcircuit,wire_cuts, gate_cuts)
    print(dag_to_circuit(subcircuits[0]["Sub_%d" % (0)]))
    print(dag_to_circuit(subcircuits[1]["Sub_%d" % (1)]))

    return subcircuits,gate_cuts,wire_cuts,sub_count

def circuit_stripping(circuit):
    
    # Remove all single qubit gates and barriers in the circuit
    dag = circuit_to_dag(circuit)
    stripped_dag = DAGCircuit()
    modified_dag = DAGCircuit()

    [stripped_dag.add_qreg(x) for x in circuit.qregs] # adding qubits to the DAG circuit.
    [modified_dag.add_qreg(x) for x in circuit.qregs] # adding qubits to the DAG circuit.
    
    
    for vertex in dag.topological_op_nodes():
        if vertex.op.name != "barrier":
            stripped_dag.apply_operation_back(op=vertex.op, qargs=vertex.qargs)

    depth = stripped_dag.depth()
    register = QuantumRegister(size=modified_dag.num_qubits(),name='q')
    for layer in range(depth):
        layer_x = stripped_dag.front_layer()
        is_full = 0
        for vertex in range(len(layer_x)):
            is_full += len(layer_x[vertex].qargs) 
            stripped_dag.remove_op_node(layer_x[vertex])
            modified_dag.apply_operation_back(op=layer_x[vertex].op, qargs=layer_x[vertex].qargs)
        if(is_full == modified_dag.num_qubits()):
            continue
        else: # Add single qubit gates to the unused qubits. 
            list_qubits = []
            for vertex in range(len(layer_x)):
                if len(layer_x[vertex].qargs) == 2:
                    arg1 = layer_x[vertex].qargs[0]
                    arg2 = layer_x[vertex].qargs[1]
                    if(arg1.index not in list_qubits):
                        list_qubits.append(arg1.index)
                    if(arg2.index not in list_qubits):
                        list_qubits.append(arg2.index)
                else:
                    arg1 = layer_x[vertex].qargs[0]
                    if(arg1.index not in list_qubits):
                        list_qubits.append(arg1.index)
        for num_qubit in range(stripped_dag.num_qubits()):
            if(num_qubit not in list_qubits):
                modified_dag.apply_operation_back(op=IGate(),qargs=[Qubit(register=register,index=num_qubit)])
    print(dag_to_circuit(modified_dag))
    return dag_to_circuit(modified_dag)

def find_cuts(
    circuit,
    max_subcircuit_width,
    max_cuts,
    num_subcircuits,
    verbose,
):
    modified_circ = circuit_stripping(circuit=circuit)
    num_qubits = circuit.num_qubits
    cut_solution = {}

    for num_subcircuit in num_subcircuits: # Basic checking to enusre that there are enough circuit for the most simple solution. 
        if (num_subcircuit * max_subcircuit_width < num_qubits or num_subcircuit > num_qubits or max_cuts + 1 < num_subcircuit):
            if verbose:
                print("%d subcircuits : IMPOSSIBLE" % (num_subcircuit))
            continue
        
        kwargs = dict(  circuit=modified_circ,
                        num_subcircuits=num_subcircuit,
                        max_subcircuit_width=max_subcircuit_width)

        mip_model = MIP_Model(**kwargs)
        feasible = mip_model.solve()
        if feasible: #Generating Subcircuits and Meta data from the cut solution.  
            subcircuits,gate_cuts,wire_cuts,sub_count = Generic_subcircuit_generator(model=mip_model)
            cut_solution = {"subcircuits": subcircuits,
                            "subcirc_count": sub_count,
                            "wire_cuts": wire_cuts,
                            "gate_cuts": gate_cuts}
        elif verbose:
            print("%d subcircuits : NO SOLUTIONS" % (num_subcircuit))
    
    if verbose and len(cut_solution) > 0: # Printing of Results.
        print("-" * 20)
        print_cutter_result(num_cuts=cut_solution["num_cuts"], subcircuits=cut_solution["subcircuits"], counter=cut_solution["counter"])
        print("Model objective value = %.2e" % (mip_model.objective), flush=True)
        print("MIP runtime:", mip_model.runtime, flush=True)
        if mip_model.optimal:
            print("OPTIMAL, MIP gap =", mip_model.mip_gap, flush=True)
        else:
            print("NOT OPTIMAL, MIP gap =", mip_model.mip_gap, flush=True)
        print("-" * 20, flush=True)

    return #cut_solution

def print_cutter_result(num_cuts, subcircuits, counter):
    print("Cutter result:")
    print("%d subcircuits, %d cuts" % (len(subcircuits), num_cuts))

    for subcircuit_idx in range(len(subcircuits)):
        print("subcircuit %d" % subcircuit_idx)
        print(
            "\u03C1 qubits = %d, O qubits = %d, width = %d, effective = %d, depth = %d, size = %d"
            % (
                counter[subcircuit_idx]["rho"],
                counter[subcircuit_idx]["O"],
                counter[subcircuit_idx]["d"],
                counter[subcircuit_idx]["effective"],
                counter[subcircuit_idx]["depth"],
                counter[subcircuit_idx]["size"],
            )
        )
        print(subcircuits[subcircuit_idx])
  