import networkx as nx
import matplotlib.pyplot as plt
from OneQ.Compact_Graph_Dynamic import *

def validate(net_list_copy, fgraph, MaxDegree):
    net_list = net_list_copy.copy()
    if MaxDegree <= 4:
        print("begin to validate!")
        alloca_nodes_cache = {}
        GraphN = len(list(fgraph.nodes()))
        net_index = 0
        
        for net in net_list:
            
            for nnode in net.nodes():
                # has been allocated actual nodes
                # print(alloca_nodes_cache)
                if net.nodes[nnode]['node_val'] > 0:
                    gnode = net.nodes[nnode]['node_val']
                    if gnode in alloca_nodes_cache.keys():
                        if nnode != alloca_nodes_cache[gnode]:
                            print("same node different 2D position")
                            exit()

                    adj_list = [nnode]
                    while len(adj_list):
                        new_adj_list = []
                        # print(adj_list)
                        for anode in adj_list:
                            neigh_nodes = list(net.neighbors(anode))
                            for neigh_node in neigh_nodes:
                                if net.nodes[neigh_node]['node_val'] > 0:
                                    # print("layer", net_index, nnode, neigh_node, gnode, net.nodes[neigh_node]['node_val'])
                                    fgraph.remove_edge(gnode, net.nodes[neigh_node]['node_val'])
                                    net.remove_edge(anode, neigh_node)
                                elif net.nodes[neigh_node]['node_val'] == - gnode:
                                    new_adj_list.append(neigh_node)
                                    net.nodes[neigh_node]['node_val'] = - GraphN - 1
                                    net.remove_edge(anode, neigh_node)
                        adj_list = new_adj_list
                    

                    alloca_nodes_cache[gnode] = nnode
                    # else:
                    #     if gnode in alloca_nodes_cache.keys():
                    #         del alloca_nodes_cache[gnode]
            net_index += 1

        if len(list(fgraph.edges())) != 0:
            for edge in fgraph.edges():
                # print(edge[0], edge[1], alloca_nodes_cache)
                if alloca_nodes_cache[edge[0]] != alloca_nodes_cache[edge[1]]:
                    print("mapping incomplete error")
                    return fgraph
            print("validate success!") 
            # pos = nx.spring_layout(fgraph)
            # labels = {node: str(node) for node in fgraph.nodes()}
            # nx.draw(fgraph, pos = pos, labels  = labels)
            # # plt.show()       
        else:
            print("validate success!") 
    else:
        print("begin to validate!")
        print("validate success!") 
    return fgraph

def validate_con_qubits(net_list, MaxDegree):
    net_index = 0
    for net in net_list:
        net_index += 1
        for nnode in net.nodes():
            if net.nodes[nnode]['node_val'] != -1000001:
                qubits = [1]
                for i in range(MaxDegree - 1):
                    qubits.append(0)

                neigh_nnodes = net.neighbors(nnode)
                for neigh_nnode in neigh_nnodes:
                    if net[nnode][neigh_nnode]['con_qubits'][nnode] in qubits:
                        qubits.remove(net[nnode][neigh_nnode]['con_qubits'][nnode])
                    else:
                        print("validate error!")
                        print(net_index)
                        return
    print("connect qubits validation success!")
    return

def validate_con_qubits_list(net_list, MaxDegree):
    net_index = 0
    for net in net_list:
        net_index += 1
        for nnode in net.nodes():
            if net.nodes[nnode]['node_val'] != -1000001:
                qubits = []
                for i in range(MaxDegree):
                    qubits.append(i)
                #print(qubits)
                neigh_nnodes = net.neighbors(nnode)
    
                for neigh_nnode in neigh_nnodes:
                    # print(net[nnode][neigh_nnode]['con_qubits'])
                    for con_qubit in net[nnode][neigh_nnode]['con_qubits']:
                        # print("loops")
                        if con_qubit[nnode] in qubits:
                            qubits.remove(con_qubit[nnode])
                            #print(qubits)
                        else:
                            print("validate error!")
                            if net.nodes[nnode]['node_val'] < 0:
                                print("auxiliary node")
                            else:
                                print("actual node")
                            print(net.nodes[nnode]['node_val'])
                            print(nnode)
                            print(con_qubit[nnode])
                            print(net_index)
                            return
    print("connect qubits validation success!")
    return   