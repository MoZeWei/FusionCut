import pyzx as zx
import random
from OneQ.JCZCircuit import *


def generate_circuit(nqubit, depth):
    circuit = zx.generate.CNOT_HAD_PHASE_circuit(qubits=nqubit,depth=depth,clifford=False)
    # zx.draw(circuit)
    # circuit = zx.optimize.basic_optimization(circuit.to_basic_gates())
    # zx.draw(circuit)
    # print(circuit.gates)
    qubits = []
    for i in range(nqubit):
        qubits.append(i)
    jcz_circuit = JCZCircuit()
    jcz_circuit.qubits_init(qubits)
    for gate in circuit.gates:
        # print(gate)
        if gate.name == "HAD":
            jcz_circuit.add_H(int(str(gate)[4:-1]))
        elif gate.name == "CNOT":
            gate_split = str(gate).split(',')
            qubit1 = int(gate_split[0][5:])
            qubit2 = int(gate_split[1][0:-1])
            jcz_circuit.add_CNOT(qubit1, qubit2)
        elif gate.name == "T":
            jcz_circuit.add_T(int(str(gate)[2:-1]))

    # zx.draw(circuit)
    # gates_list = [CZGate(0, 2), JGate(0, 1), CZGate(0, 1), CZGate(0, 1), CZGate(0, 1), JGate(1, 3), JGate(1, 2)]

    return  jcz_circuit.gates, nqubit

##NOTE: This can be used in the cutting, but not in the re-ordering
def construct_qft(nqubit):
    jcz_circuit = JCZCircuit()
    for target in range(nqubit - 1):
        jcz_circuit.add_H(target)
        for control in range(target + 1, nqubit):
            phase = random.randint(0, 7)
            jcz_circuit.add_CRz(control, target, phase)
    jcz_circuit.add_H(nqubit - 1)
    return jcz_circuit.gates, nqubit

##NOTE: This can be used in the cutting, but not in the re-ordering
def construct_qaoa(nqubit, average_gate_num, sort=True, ver=True, draw=False):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_J(qubit, random.randint(0, 7)) for qubit in range(nqubit)]
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    
    all_possible_gates = [(i,j) for i in range(nqubit) for j in range(i+1, nqubit)]
    gates = list(set(random.choices(all_possible_gates,
                                    k= int(len(all_possible_gates)*average_gate_num))))
    if sort:
        gates.sort() 

    for gate in gates:
        jcz_circuit.add_CNOT(gate[1], gate[0])
        jcz_circuit.add_Rz(gate[0], random.randint(0, 7))
        jcz_circuit.add_CNOT(gate[1], gate[0])
    return jcz_circuit.gates, nqubit

#Note: If there is no H gate following a multi-gate operation, 
# the output node is the gate node. Or it has dependent output node
# construct_star_sample_overdegree and construct_substar_sample_underdegree correspond to the MICRO-1 benchmark

def construct_star_sample_overdegree(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_J(qubit, random.randint(0, 7)) for qubit in range(nqubit)]
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]

    #qubit 0 will have (nqubit - 1) degree
    for target in range(1,nqubit):
        jcz_circuit.add_CNOT(0,target)
        jcz_circuit.add_CNOT(0,target)
        jcz_circuit.add_CNOT(0,target)
        jcz_circuit.add_CNOT(0,target)
        jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
    # jcz_circuit.add_CNOT(1,2)
    # jcz_circuit.add_CNOT(1,3)
    # jcz_circuit.add_CNOT(1,4)
    # jcz_circuit.add_CNOT(2,3)
    # jcz_circuit.add_CNOT(2,4)
    # jcz_circuit.add_CNOT(3,4)
    return jcz_circuit.gates, nqubit

def construct_substar_sample_underdegree(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_J(qubit, random.randint(0, 7)) for qubit in range(nqubit)]
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]

    for target in range(1,nqubit):
        jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
        # jcz_circuit.add_CNOT(0,target)
    jcz_circuit.add_CNOT(1,2)
    # jcz_circuit.add_CNOT(1,3)
    # jcz_circuit.add_CNOT(1,4)
    # jcz_circuit.add_CNOT(2,3)
    # jcz_circuit.add_CNOT(2,4)
    # jcz_circuit.add_CNOT(3,4)
    return jcz_circuit.gates, nqubit

def construct_benchmark_sample(nqubit, name):
    if name == "MICRO-1":
        return construct_star_sample_overdegree(nqubit)

def construct_benchmark_cutted_sample(nqubit, name):
    if name == "MICRO-1":
        return construct_substar_sample_underdegree(nqubit)

#A simple sample to see how reorder can gain benefit on #Fusion
def generate_overdegree_circuit(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    jcz_circuit.add_CNOT(1,2)
    jcz_circuit.add_CNOT(0,1)
    jcz_circuit.add_CNOT(2,3)
    jcz_circuit.add_CNOT(1,2)
    # jcz_circuit.add_CZ(1,2)
    return jcz_circuit.gates, nqubit

#A sample to show benefit from pure re-order
def generate_reorderable_circuit(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    jcz_circuit.add_CZ(0,1)
    jcz_circuit.add_H(1)
    # jcz_circuit.add_CZ(0,1)
    jcz_circuit.add_CZ(1,3)
    jcz_circuit.add_H(3)
    jcz_circuit.add_CZ(1,4)
    jcz_circuit.add_H(4)
    jcz_circuit.add_CZ(1,5)
    jcz_circuit.add_H(5)
    return jcz_circuit.gates, nqubit

def generate_reordered_circuit(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    jcz_circuit.add_CZ(1,3)
    jcz_circuit.add_H(3)
    # jcz_circuit.add_CZ(0,1)
    jcz_circuit.add_CZ(0,1)
    jcz_circuit.add_H(1)
    jcz_circuit.add_CZ(1,4)
    jcz_circuit.add_H(4)
    jcz_circuit.add_CZ(1,5)
    jcz_circuit.add_H(5)
    return jcz_circuit.gates, nqubit

#NOTE: There is no qubits acting as the input for multiple multi-qubit gates
def generate_bv5_original_circuit(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    jcz_circuit.add_Z(4)
    for control in range(nqubit-1):
        jcz_circuit.add_CNOT(control,nqubit-1)
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    return jcz_circuit.gates, nqubit
#TODO: Can we use a reversal pair to generate different state between multiple multi-qubit gates for one qubit,
#so that we can reduct fusion by re-order

def generate_gs10_original_circuit(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    jcz_circuit.add_CZ(0,1)
    jcz_circuit.add_CZ(0,7)
    jcz_circuit.add_CZ(0,9)
    jcz_circuit.add_CZ(2,5)
    jcz_circuit.add_CZ(2,4)
    jcz_circuit.add_CZ(2,6)
    jcz_circuit.add_CZ(4,8)
    jcz_circuit.add_CZ(3,7)
    return jcz_circuit.gates, nqubit

def generate_hlf10_original_circuit(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    jcz_circuit.add_CZ(0,1)
    jcz_circuit.add_CZ(0,7)
    jcz_circuit.add_CZ(0,9)
    jcz_circuit.add_CZ(2,5)
    jcz_circuit.add_CZ(2,4)
    jcz_circuit.add_CZ(2,6)
    jcz_circuit.add_CZ(4,8)
    jcz_circuit.add_CZ(3,7)
    jcz_circuit.add_H(0)
    jcz_circuit.add_H(1)
    jcz_circuit.add_S(2)
    jcz_circuit.add_H(2)
    jcz_circuit.add_H(3)
    jcz_circuit.add_H(4)
    jcz_circuit.add_H(5)
    jcz_circuit.add_H(6)
    jcz_circuit.add_H(7)
    jcz_circuit.add_S(8)
    jcz_circuit.add_H(8)
    jcz_circuit.add_H(9)
    return jcz_circuit.gates, nqubit

#Between two Hardmard layers, we can add commutative gates in any order
#TODO: Build a nice one
def generate_iqp10_original_circuit(nqubit):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    jcz_circuit.add_CP(0,2,4)
    jcz_circuit.add_CP(0,3,4)
    jcz_circuit.add_CP(0,4,4)
    jcz_circuit.add_CP(0,5,4)
    jcz_circuit.add_CP(0,7,4)
    jcz_circuit.add_CP(0,8,4)
    jcz_circuit.add_CP(1,4,4)
    jcz_circuit.add_CP(1,5,4)
    jcz_circuit.add_CP(1,6,4)
    jcz_circuit.add_CP(1,9,4)
    # jcz_circuit.add_CP(2,3,4)
    # jcz_circuit.add_CP(2,5,4)
    # jcz_circuit.add_CP(2,6,4)
    # jcz_circuit.add_CP(2,7,4)
    # jcz_circuit.add_CP(2,8,4)
    # jcz_circuit.add_CP(2,9,4)
    # jcz_circuit.add_CP(3,4,4)
    # jcz_circuit.add_CP(3,5,4)
    # jcz_circuit.add_CP(3,6,4)
    # jcz_circuit.add_CP(3,7,4)
    # jcz_circuit.add_CP(4,5,4)
    # jcz_circuit.add_CP(4,6,4)
    # jcz_circuit.add_CP(4,7,4)
    # jcz_circuit.add_CP(4,8,4)
    # jcz_circuit.add_CP(4,9,4)
    # jcz_circuit.add_CP(5,6,4)
    # jcz_circuit.add_CP(5,7,4)
    # jcz_circuit.add_CP(5,8,4)
    # jcz_circuit.add_CP(5,9,4)
    # jcz_circuit.add_CP(6,7,4)
    # jcz_circuit.add_CP(6,8,4)
    # jcz_circuit.add_CP(6,9,4)
    # jcz_circuit.add_CP(7,8,4)
    # jcz_circuit.add_CP(8,9,4)
    jcz_circuit.add_H(0)
    jcz_circuit.add_P(1)
    jcz_circuit.add_H(1)
    jcz_circuit.add_P(2)
    jcz_circuit.add_H(2)
    jcz_circuit.add_P(3)
    jcz_circuit.add_H(3)
    jcz_circuit.add_P(4)
    jcz_circuit.add_H(4)
    jcz_circuit.add_P(5)
    jcz_circuit.add_H(5)
    jcz_circuit.add_H(6)
    jcz_circuit.add_P(7)
    jcz_circuit.add_H(7)
    jcz_circuit.add_P(8)
    jcz_circuit.add_H(8)
    jcz_circuit.add_H(9)
    return jcz_circuit.gates, nqubit


def generate_from_gate_list(gate_list, nqubit):
    jcz_circuit = JCZCircuit()
    for gate in gate_list:
        if gate['name'] == 'cx':    #CX in qiskit means the CNOT
            jcz_circuit.add_CNOT(gate['qubit'][0], gate['qubit'][1])
        elif gate['name'] == 'h':
            jcz_circuit.add_H(gate['qubit'][0])

    return jcz_circuit.gates, nqubit