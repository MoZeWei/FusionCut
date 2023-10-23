def is_measurable(gs, measured_nodes, cur_node):
    pre_nodes_layer_order = []
    pre_nodes = []
    visited_nodes = []
    visited = {}
    for nnode in gs.nodes():
        visited[nnode] = 0
    visited[cur_node] = 1
    visited_nodes.append(cur_node)
    for i in range(2):
        if not len(visited_nodes):
            break
        visited_nodes_copy = visited_nodes.copy()
        visited_nodes.clear()
        # print("visited_ndoes_copy", visited_nodes_copy)
        for nnode in visited_nodes_copy:
            for pre_node in gs.predecessors(nnode):
                if visited[pre_node] == 0:
                    if pre_node in gs.successors(nnode):
                        visited_nodes.append(pre_node)
                        # else:
                        #     pre_nodes_layer_order.append(gs.nodes[pre_node]['layer'])
                        #     pre_nodes.append(pre_node)
                    else:
                        if pre_node not in measured_nodes:
                            # print("false pre_node", pre_node)
                            return False, pre_nodes_layer_order, pre_nodes
                        else:
                            pre_nodes_layer_order.append(gs.nodes[pre_node]['layer'] + 1)       
                            pre_nodes.append(pre_node)    
                    visited[pre_node] = 1 

    return True, pre_nodes_layer_order, pre_nodes


# def teleportation(gs, cur_node, unmeasured_nodes):
#     for pre_node in gs.predecessors(cur_node):
#         if pre_node in gs.successors(cur_node):
#             if pre_node in unmeasured_nodes:
#                 gs.nodes[pre_node]['layer'] = max(gs.nodes[pre_node]['layer'], gs.nodes[cur_node]['layer'])
#     return gs

def partition(gs, input_nodes):    
    measured_nodes = []
    unmeaured_nodes = list(gs.nodes()).copy()

    for nnode in unmeaured_nodes:
        gs.nodes[nnode]['layer'] = 0
    
    # for input_node in input_nodes:
    #     measured_nodes.append(input_node)
    #     unmeaured_nodes.remove(input_node)

    while len(unmeaured_nodes):
        # print("unmeasured length", len(unmeaured_nodes))
        unmeasured_nodes_copy = unmeaured_nodes.copy()
        for nnode in unmeasured_nodes_copy:
            is_measurabled, pre_nodes_layer_order, pre_nodes = is_measurable(gs, measured_nodes, nnode)
            # print("nnode", nnode)
            # print(is_measurabled, pre_nodes)
            if is_measurabled:
                for pre_node_layer_order in pre_nodes_layer_order :
                    # if pre_node in gs.successors(nnode):
                    #     gs.nodes[nnode]['layer'] = max(gs.nodes[nnode]['layer'], pre_node)
                    # else:
                    #     gs.nodes[nnode]['layer'] = max(gs.nodes[nnode]['layer'], gs.nodes[pre_node]['layer'] + 1)
                    gs.nodes[nnode]['layer'] = max(gs.nodes[nnode]['layer'], pre_node_layer_order)
                measured_nodes.append(nnode)
                unmeaured_nodes.remove(nnode)
                # teleportation(gs, nnode, unmeaured_nodes)
    return gs
