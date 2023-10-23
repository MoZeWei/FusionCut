from OneQ.Fusion import *
from OneQ.Graph_State import *
from OneQ.Compact_Graph_Dynamic import *
from OneQ.Compact_Graph_Dynamic_List import *
from OneQ.Compact_Graph_Dynamic_General import *
from OneQ.Compact_Graph import *
from OneQ.Validate import *
from OneQ.Construct_Test_Circuit import *
from OneQ.Determine_Dependency import *
from OneQ.Partition import *
from OneQ.Add_Round import *
from OneQ.Z_Measure_Notify import *
from OneQ.Generate_State import *

import sys
import os

NQubit = 5 #30
Depth = 5 #300
MaxDegree = 3 #16
StarStructure = False
DynamicSchedule = True
SpecialFusion = True
GeneralState = True

def to_undirected(gs):
    undirected_graph = nx.Graph()
    for nnode in gs.nodes():
        undirected_graph.add_node(nnode)
        if StarStructure or MaxDegree <= 4:
            undirected_graph.nodes[nnode]['phase'] = gs.nodes[nnode]['phase']
        else:
            if not GeneralState:
                undirected_graph.nodes[nnode]['phase'] = []
                undirected_graph.nodes[nnode]['phase'].append(gs.nodes[nnode]['phase'])
            else:
                undirected_graph.nodes[nnode]['phase'] = {}
                undirected_graph.nodes[nnode]['phase'][0] = []
                undirected_graph.nodes[nnode]['phase'][0].append(gs.nodes[nnode]['phase'])                
        # if not Generalized_Flow_Flag:
        if not DynamicSchedule:
            undirected_graph.nodes[nnode]['layer'] = gs.nodes[nnode]['layer']

    for edge in gs.edges():
        if edge not in undirected_graph.edges():
            undirected_graph.add_edge(edge[0], edge[1])
            undirected_graph[edge[0]][edge[1]]['con_qubits'] = {}
        if GeneralState:
            undirected_graph[edge[0]][edge[1]]['con_qubits'][edge[0]] = 1
            undirected_graph[edge[0]][edge[1]]['con_qubits'][edge[1]] = 1    
            # print("general state")
        else:
            undirected_graph[edge[0]][edge[1]]['con_qubits'][edge[0]] = 0
            undirected_graph[edge[0]][edge[1]]['con_qubits'][edge[1]] = 0                       
    return undirected_graph

def empty_folder(folder_path):
    if os.path.exists(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                empty_folder(item_path)
        print(f"Folder '{folder_path}' has been emptied.")
    else:
        print(f"Folder '{folder_path}' does not exist.")

def generate_fusion(gates_list, qubits, gs, input_nodes, colors, resource_state):
    if DynamicSchedule:
        # causal flow
        dgraph = determine_dependency(gs)
        # gs = schedule(gs, dgraph)
        # gs = partition(gs, input_nodes)
        # pos = nx.get_node_attributes(gs, 'pos')
        undirected_graph = to_undirected(gs)
        print("The graph is:")
        nx.draw(undirected_graph)
        # plt.show()

        # # generalized flow
        # if Generalized_Flow_Flag:
        #     undirected_graph = generalized_flow(undirected_graph, input_nodes)
        #     labels = {node: str(undirected_graph.nodes[node]['layer']) for node in undirected_graph.nodes()}
        #     nx.draw(undirected_graph, pos = pos, labels = labels, node_size = 30, font_size = 10)


        # fusion
        if GeneralState:
            fgraph = fusion_dynamic_general(undirected_graph, resource_state.copy())
            while fgraph == -1:
                resource_state = generate_state(MaxDegree)
                fgraph = fusion_dynamic_general(undirected_graph, resource_state.copy())
            print("resource state used for this circuit:")
            nx.draw(resource_state)
            # plt.show()
        else:
            fgraph, added_nodes = fusion_graph_dynamic(undirected_graph, MaxDegree, StarStructure, SpecialFusion)
        
        # add rounds
        # fgraph = add_round(fgraph, 1)
        
        # map and route
        if GeneralState:
            net_list = compact_graph_dynamic_general(fgraph, dgraph.copy(), resource_state)
        elif StarStructure or MaxDegree <= 4:
            net_list = compact_graph_dynamic(fgraph, dgraph, MaxDegree)
        else:
            # if SpecialFusion:
            #     net_list = compact_graph_dynamic_list_special_fusion(fgraph, dgraph, MaxDegree)
            # else:
            net_list = compact_graph_dynamic_list(fgraph, dgraph, MaxDegree, SpecialFusion)
    else:
        gs = partition(gs, input_nodes)
        undirected_graph = to_undirected(gs)
        fgraph, added_nodes = fusion_graph(undirected_graph, MaxDegree, StarStructure)
        fgraph = add_round(fgraph, 1)
        net_list = compact_graph(fgraph, MaxDegree)
    
    if not GeneralState and not StarStructure:
        net_list = z_measure_notify(net_list, MaxDegree)
    # show result
    fusions = 0
    for net in net_list:
        fusions += len(list(net.edges()))
    # print("fusion:", fusions)
    
    if GeneralState:
        validate_con_qubits_list(net_list, MaxDegree) 
    elif StarStructure or MaxDegree <= 4:
        validate_con_qubits(net_list, MaxDegree)
        fgraph = validate(net_list, fgraph, MaxDegree) 
    else:
        validate_con_qubits_list(net_list, MaxDegree)  
    return fusions

def fusion_win(original, optimized):
    if(original > optimized):
        print(f"Original Fushion: '{original}'")
        print(f"Optimized Fushion: '{optimized}'")
        print(f"Fusion reduced by '{1 - optimized / original}' after optimization")
    else:
        print(f"Original Fushion: '{original}'")
        print(f"Optimized Fushion: '{optimized}'")
        print("Optimization failed")

def main():
    empty_folder("layers/")

    resource_state = generate_state(MaxDegree)
    print("The resource state is")
    nx.draw(resource_state)
    # plt.show()
    
    # construct circuit
    # gates_list, qubits = generate_circuit(NQubit, Depth)
    # gates_list, qubits = construct_qaoa(NQubit, 0.5)
    # generate graph state
    # gs, input_nodes, colors = generate_graph_state(gates_list, qubits)
    # generate_fusion(gates_list, qubits, gs, input_nodes, colors)

    #Cutting one circuit into two and measure their #fusions
    print("Star Structure circuit info:")
    star_gates_list, star_qubits = construct_star_sample_overdegree(5)     #NQubit should 2n+1
    star_gs, star_input_nodes, star_colors = generate_graph_state(star_gates_list, star_qubits)
    original_fusion = generate_fusion(star_gates_list, star_qubits, star_gs, star_input_nodes, star_colors, resource_state)

    print("Sub-Star Structure circuit info:")
    substar_gates_list, substar_qubits = construct_substar_sample_underdegree(4)
    substar_gs, substar_input_nodes, substar_colors = generate_graph_state(substar_gates_list, substar_qubits)
    sub_fusion = generate_fusion(substar_gates_list, substar_qubits, substar_gs, substar_input_nodes, substar_colors, resource_state)

    fusion_win(original_fusion, sub_fusion)

    #Reorder one sample circuit and measure their #fusions
    # print("Reorderable circuit info:")
    # to_order_gates_list, to_order_qubits = generate_reorderable_circuit(6)     #NQubit should 2n+1
    # to_order_gs, to_order_input_nodes, to_order_colors = generate_graph_state(to_order_gates_list, to_order_qubits)
    # original_fusion = generate_fusion(to_order_gates_list, to_order_qubits, to_order_gs, to_order_input_nodes, to_order_colors, resource_state)

    # print("Reordered circuit info:")
    # reordered_gates_list, reordered_qubits = generate_reordered_circuit(6)
    # reordered_gs, reordered_input_nodes, reordered_colors = generate_graph_state(reordered_gates_list, reordered_qubits)
    # reordered_fusion = generate_fusion(reordered_gates_list, reordered_qubits, reordered_gs, reordered_input_nodes, reordered_colors, resource_state)

    # fusion_win(original_fusion, reordered_fusion)

    #Multiple Overdegree scenario
    # overdegree_gates_list, overdegree_qubits = generate_overdegree_circuit(4)
    # overdegree_gs, overdegree_input_nodes, overdegree_colors = generate_graph_state(overdegree_gates_list, overdegree_qubits)
    # generate_fusion(overdegree_gates_list, overdegree_qubits, overdegree_gs, overdegree_input_nodes, overdegree_colors)
    return
'''
    if DynamicSchedule:
        # causal flow
        dgraph = determine_dependency(gs)
        # gs = schedule(gs, dgraph)
        # gs = partition(gs, input_nodes)
        # pos = nx.get_node_attributes(gs, 'pos')
        undirected_graph = to_undirected(gs)
        print("The graph is:")
        nx.draw(undirected_graph)
        # plt.show()

        # # generalized flow
        # if Generalized_Flow_Flag:
        #     undirected_graph = generalized_flow(undirected_graph, input_nodes)
        #     labels = {node: str(undirected_graph.nodes[node]['layer']) for node in undirected_graph.nodes()}
        #     nx.draw(undirected_graph, pos = pos, labels = labels, node_size = 30, font_size = 10)


        # fusion
        if GeneralState:
            resource_state = generate_state(MaxDegree)
            print("The resource state is")
            nx.draw(resource_state)
            # plt.show()
            fgraph = fusion_dynamic_general(undirected_graph, resource_state.copy())
            while fgraph == -1:
                resource_state = generate_state(MaxDegree)
                fgraph = fusion_dynamic_general(undirected_graph, resource_state.copy())                
        else:
            fgraph, added_nodes = fusion_graph_dynamic(undirected_graph, MaxDegree, StarStructure, SpecialFusion)
        
        # add rounds
        # fgraph = add_round(fgraph, 1)
        
        # map and route
        if GeneralState:
            net_list = compact_graph_dynamic_general(fgraph, dgraph.copy(), resource_state)
        elif StarStructure or MaxDegree <= 4:
            net_list = compact_graph_dynamic(fgraph, dgraph, MaxDegree)
        else:
            # if SpecialFusion:
            #     net_list = compact_graph_dynamic_list_special_fusion(fgraph, dgraph, MaxDegree)
            # else:
            net_list = compact_graph_dynamic_list(fgraph, dgraph, MaxDegree, SpecialFusion)
    else:
        gs = partition(gs, input_nodes)
        undirected_graph = to_undirected(gs)
        fgraph, added_nodes = fusion_graph(undirected_graph, MaxDegree, StarStructure)
        fgraph = add_round(fgraph, 1)
        net_list = compact_graph(fgraph, MaxDegree)
    
    if not GeneralState and not StarStructure:
        net_list = z_measure_notify(net_list, MaxDegree)
    # show result
    fusions = 0
    for net in net_list:
        fusions += len(list(net.edges()))
    print("fusion:", fusions)
    
    if GeneralState:
        validate_con_qubits_list(net_list, MaxDegree) 
    elif StarStructure or MaxDegree <= 4:
        validate_con_qubits(net_list, MaxDegree)
        fgraph = validate(net_list, fgraph, MaxDegree) 
    else:
        validate_con_qubits_list(net_list, MaxDegree)  
    return
'''

if __name__ == '__main__':
    main()