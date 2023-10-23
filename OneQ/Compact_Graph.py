import networkx as nx
import matplotlib.pyplot as plt
import heapq
import random

##########################################################
#                                                        #
#           Multi Layers with Dependency                 #
#                                                        #
##########################################################

NetN = 25
NetM = 25
GraphN = 10000000
SearchUpperBound = 20

def create_net(alloca_nodes):
    net = nx.Graph()
    for key in alloca_nodes.keys():
        net.add_node(alloca_nodes[key], node_val = key, pos = (alloca_nodes[key] % NetM, alloca_nodes[key] // NetM))

    # add nodes to the net
    for i in range(NetN):
        for j in range(NetM):
            if i * NetM + j not in net.nodes():
                # -GraphN - 1 means no node allocated, negative number means its auxiliary identity
                net.add_node(i * NetM + j, node_val = - GraphN - 1, pos = (j, i))
    return net

def save_net(pre_graph, net, alloca_pos, layer_index):
    colors = []
    labels = {}
    for nnode in net.nodes():
        # node already allocated but still in graph, show green color
        if nnode in alloca_pos:
            colors.append('green')
            labels[nnode] = str(pre_graph.nodes[net.nodes[nnode]['node_val']]['layer'])
            continue
        
        # unallocated node, show gray
        if net.nodes[nnode]['node_val'] == - GraphN - 1:
            colors.append('gray')
            labels[nnode] = ""
        # auxiliary node, show pink
        elif net.nodes[nnode]['node_val'] < 0:
            colors.append('pink')
            labels[nnode] = ""
        # allocated node with real value, show blue
        else:
            colors.append('blue')
            labels[nnode] = str(pre_graph.nodes[net.nodes[nnode]['node_val']]['layer'])
    
    # get nodes' positions
    pos = nx.get_node_attributes(net, 'pos')

    # show net
    plt.figure(figsize=(NetN, NetM))
    nx.draw(net, pos = pos, labels = labels, node_color = colors, node_size = 40, font_size = 40)
    # save image     
    plt.savefig("layers/layer" + str(layer_index) + ".png")
    # plt.show()
    return

def count_pos_untake(net, pos):
    index = []

    if pos - NetM >= 0 and net.nodes[pos - NetM]['node_val'] == -GraphN - 1:
        index.append(pos - NetM)

    if pos + NetM <= NetN * NetM - 1 and net.nodes[pos + NetM]['node_val'] == -GraphN - 1:
        index.append(pos + NetM)  
    
    if pos % NetM != 0 and net.nodes[pos - 1]['node_val'] == -GraphN - 1:
        index.append(pos - 1)

    if pos % NetM != NetM - 1 and net.nodes[pos + 1]['node_val'] == -GraphN - 1:
        index.append(pos + 1)
    
    return index

# used for allocate the unallocated nodes, the path is one way like
class OneWaySearchNode:
    def __init__(self, net, path):
        self.net = net.copy()
        self.path = path.copy()
        self.free_space = set()
        for pnode in path:
            for nnode in count_pos_untake(net, pnode):
                self.free_space.add(nnode)
        self.f = len(self.free_space)

    def __lt__(self, other):
        return self.f > other.f      

def find_pre_pos(net, path, pos, MaxDegree):
    if pos - NetM >= 0 and pos - NetM in path and len(list(net.neighbors(pos - NetM))) <= MaxDegree - 1:
        return pos - NetM

    if pos + NetM <= NetN * NetM - 1 and pos + NetM in path and len(list(net.neighbors(pos + NetM))) <= MaxDegree - 1:
        return pos + NetM 
    
    if pos % NetM != 0 and pos - 1 in path and len(list(net.neighbors(pos - 1))) <= MaxDegree - 1:
        return pos - 1

    if pos % NetM != NetM - 1 and pos + 1 in path and len(list(net.neighbors(pos + 1))) <= MaxDegree - 1:
        return pos + 1  
    return -1

def one_layer_map(graph, alloca_nodes, cur_layer, alloca_nodes_cache, MaxDegree):
    # recycled alloca nodes
    recycled_nodes = {}
    # initial net
    net = create_net(alloca_nodes)

    # Determine nodes for the current layer
    cur_layer_nodes = []
    # nodes on the current layer
    for gnode in graph.nodes():
        if graph.nodes[gnode]['layer'] == cur_layer:
            if gnode not in alloca_nodes_cache.keys():
                cur_layer_nodes.append(gnode)
        elif gnode in alloca_nodes.keys():
            cur_layer_nodes.append(gnode)

    
    failed_nodes = []
    for i in range(3):
        if len(list(graph.nodes())) == 0:
            return net, graph
        copy_cur_layer_nodes = cur_layer_nodes.copy()
        for cur_layer_node in copy_cur_layer_nodes:
            if cur_layer_node not in graph.nodes() or cur_layer_node in failed_nodes or len(list(graph.neighbors(cur_layer_node))) == 0:
                cur_layer_nodes.remove(cur_layer_node)
        # get the subgraph to be allocated
        cur_layer_graph = graph.subgraph(cur_layer_nodes)

        # get connected subgraph list
        subgraphs = list(nx.connected_components(cur_layer_graph))
        failed_nodes = []
        # begin mapping and routing for each subgraph
        for gnodes in subgraphs:
            # update graph after mapping
            all_nodes = list(graph.nodes()).copy() 
            for nnode in all_nodes:
                if len(list(graph.neighbors(nnode))) == 0:
                    graph.remove_node(nnode)  

            gnodes = list(gnodes)
            alloca_incomplete_nodes = []
            # check whether all nodes in this subgraph unallocated
            is_all_gnodes_unalloca = True
            for gnode in gnodes:
                if gnode in alloca_nodes.keys():
                    is_all_gnodes_unalloca = False
                    break
            
            # all nodes in gnods is unallocated
            if is_all_gnodes_unalloca:
                unallocated_net_nodes = []
                for nnode in net.nodes():
                    if net.nodes[nnode]['node_val'] == -GraphN - 1:
                        unallocated_net_nodes.append(nnode)
                if len(unallocated_net_nodes) == 0:
                    return net, graph
                alloca_pos = unallocated_net_nodes[random.randint(int((len(unallocated_net_nodes) - 1) / 4), int((len(unallocated_net_nodes) - 1) * 3 / 4))]
                # allocate the node to a random position
                net.nodes[alloca_pos]['node_val'] = gnodes[0]
                alloca_nodes[gnodes[0]] = alloca_pos
                alloca_incomplete_nodes.append(gnodes[0])
            else:
                for gnode in gnodes:
                    if gnode in alloca_nodes.keys():
                        alloca_incomplete_nodes.append(gnode)

            if len(gnodes) == 1:
                if len(list(graph.neighbors(gnodes[0]))):
                    alloca_node = gnodes[0]
                    net.nodes[alloca_nodes[alloca_node]]['node_val'] = - GraphN - 1
                    if alloca_node in cur_layer_nodes:
                        cur_layer_nodes.remove(alloca_node)
                    
                    if alloca_node not in alloca_nodes_cache.keys():
                        # print("hello")
                        alloca_nodes_cache[alloca_node] = alloca_nodes[alloca_node]
                    del alloca_nodes[alloca_node]
                continue
            
            # diffusion from allocated incomplete nodes
            while len(alloca_incomplete_nodes):
                # choose one allocated incomplete_node to diffuse
                alloca_node = alloca_incomplete_nodes[0]
                alloca_node_neighbor_size = len(list(graph.neighbors(alloca_node)))

                # make sure that it is still in the graph
                if alloca_node not in graph.nodes():
                    alloca_incomplete_nodes.remove(alloca_node)
                    continue          

                # check again whether it is incomplete
                if len(list(graph.neighbors(alloca_node))) == 0:
                    graph.remove_node(alloca_node)
                    alloca_incomplete_nodes.remove(alloca_node)
                    continue           
                
                # divide the neighbor nodes into allocated list and unallocated list
                neigh_graph_nodes_all = list(graph.neighbors(alloca_node))
                neigh_graph_nodes_alloca = []
                neigh_graph_nodes_unalloca = []
                neigh_graph_nodes_unalloca_with_one = []

                for gnode in neigh_graph_nodes_all:
                    if gnode not in list(alloca_nodes.keys()):
                        if gnode in cur_layer_nodes:
                            if graph[alloca_node][gnode]['con_qubits'][alloca_node] == 0:
                                neigh_graph_nodes_unalloca.append(gnode)
                            else:
                                neigh_graph_nodes_unalloca_with_one.append(gnode)
                    else:
                        neigh_graph_nodes_alloca.append(gnode)                

                # allocate the unallocated neighbor nodes
                neigh_graph_nodes_unalloca_size = len(neigh_graph_nodes_unalloca)

                search_set = []
                search_node = OneWaySearchNode(net, [alloca_nodes[alloca_node]])
                heapq.heappush(search_set, search_node)
                search_index = 0
                while len(search_set):
                    # reach the search times' upper bound
                    if search_index > SearchUpperBound:
                        break

                    search_index += 1
                    search_node = heapq.heappop(search_set)
                    
                    # find a available solution
                    if search_node.f >= neigh_graph_nodes_unalloca_size:
                        break

                    # keep searching
                    if search_node.f >= 1:
                        search_node_net = search_node.net
                        search_node_path = search_node.path
                        # if MaxDegree <= 4:
                        count_pos_untake_list = count_pos_untake(search_node_net, search_node_path[-1])
                        # else:
                        #     count_pos_untake_list = []

                        #     if search_node_path[-1] - NetM >= 0 and search_node_net.nodes[search_node_path[-1] - NetM]['node_val'] < 0:
                        #         count_pos_untake_list.append(search_node_path[-1] - NetM)

                        #     if search_node_path[-1] + NetM <= NetN * NetM - 1 and search_node_net.nodes[search_node_path[-1] + NetM]['node_val'] < 0:
                        #         count_pos_untake_list.append(search_node_path[-1] + NetM)  
                            
                        #     if search_node_path[-1] % NetM != 0 and search_node_net.nodes[search_node_path[-1] - 1]['node_val'] < 0:
                        #         count_pos_untake_list.append(search_node_path[-1] - 1)

                        #     if search_node_path[-1] % NetM != NetM - 1 and search_node_net.nodes[search_node_path[-1] + 1]['node_val'] < 0:
                        #         count_pos_untake_list.append(search_node_path[-1] + 1)
                        for untake_pos in count_pos_untake_list:
                            up_pos = untake_pos - NetM
                            down_pos = untake_pos + NetM
                            left_pos = untake_pos - 1
                            right_pos = untake_pos + 1

                            # check whether the path will lead to blockness
                            if up_pos >= 0 and search_node_net.nodes[up_pos]['node_val'] != - GraphN - 1 and len(count_pos_untake(search_node_net, up_pos))  <= 1 and up_pos in alloca_incomplete_nodes:
                                continue

                            if down_pos <= NetM * NetN - 1 and search_node_net.nodes[down_pos]['node_val'] != - GraphN - 1 and len(count_pos_untake(search_node_net, down_pos)) <= 2 and down_pos in alloca_incomplete_nodes:
                                continue

                            if left_pos % NetM != NetM - 1 and search_node_net.nodes[left_pos]['node_val'] != - GraphN - 1 and len(count_pos_untake(search_node_net, left_pos)) <= 2 and left_pos in alloca_incomplete_nodes:
                                continue

                            if right_pos % NetM != 0 and search_node_net.nodes[right_pos]['node_val'] != - GraphN - 1 and len(count_pos_untake(search_node_net, right_pos)) <= 2 and right_pos in alloca_incomplete_nodes:
                                continue
                            new_node_net = search_node_net.copy()
                            new_node_net.add_edge(search_node_path[-1], untake_pos)
                            new_node_net[search_node_path[-1]][untake_pos]['con_qubits'] = {}
                            new_node_net[search_node_path[-1]][untake_pos]['con_qubits'][search_node_path[-1]] = 0
                            new_node_net[search_node_path[-1]][untake_pos]['con_qubits'][untake_pos] = 1
                            new_node_net.nodes[untake_pos]['node_val'] = - alloca_node
                            new_node_path = search_node_path.copy()
                            new_node_path.append(untake_pos)
                            new_node = OneWaySearchNode(new_node_net, new_node_path)
                            heapq.heappush(search_set, new_node)
                
                # allocate node as much as possible
                if search_node.f:
                    if len(search_node.path) == 1:
                        neigh_graph_nodes_unalloca = neigh_graph_nodes_unalloca + neigh_graph_nodes_unalloca_with_one
                    net = search_node.net
                    count_pos_untake_list = list(search_node.free_space)
                    # allocate the nodes
                    while len(count_pos_untake_list) and len(neigh_graph_nodes_unalloca):
                        untake_pos = count_pos_untake_list[0]
                        count_pos_untake_list.remove(untake_pos)
                        unalloca_node = neigh_graph_nodes_unalloca[0]
                        neigh_graph_nodes_unalloca.remove(unalloca_node)
                        net.nodes[untake_pos]['node_val'] = unalloca_node
                        pre_pos = find_pre_pos(net, search_node.path, untake_pos, MaxDegree)
                        if pre_pos == -1:
                            neigh_graph_nodes_unalloca.append(unalloca_node)
                            continue
                        net.add_edge(pre_pos, untake_pos)
                        net[pre_pos][untake_pos]['con_qubits'] = {}
                        net[pre_pos][untake_pos]['con_qubits'][pre_pos] = graph[alloca_node][unalloca_node]['con_qubits'][alloca_node]
                        net[pre_pos][untake_pos]['con_qubits'][untake_pos] = graph[alloca_node][unalloca_node]['con_qubits'][unalloca_node]
                        alloca_nodes[unalloca_node] = untake_pos
                        graph.remove_edge(alloca_node, unalloca_node)

                        if len(list(graph.neighbors(unalloca_node))):
                            alloca_incomplete_nodes.append(unalloca_node)
                        else:
                            graph.remove_node(unalloca_node)

                # search path to node allocated
                while len(neigh_graph_nodes_alloca):
                    node_dest = neigh_graph_nodes_alloca[0]
                    neigh_graph_nodes_alloca.remove(node_dest)
                    src_pos = alloca_nodes[alloca_node]
                    dest_pos = alloca_nodes[node_dest]

                    # create new net to use the shortest path function
                    node_set = [src_pos, dest_pos]
                    for nnode in net.nodes():
                        # if MaxDegree <= 4:
                        if net.nodes[nnode]['node_val'] == - GraphN - 1:
                            node_set.append(nnode)
                        # else:
                        #     if net.nodes[nnode]['node_val'] < 0:
                        #         node_set.append(nnode)   

                    new_net = nx.Graph()
                    for nnode in node_set:
                        new_net.add_node(nnode)
                    
                    for nnode in node_set:
                        up_nnode = nnode - NetM
                        left_nnode = nnode - 1
                        if up_nnode in node_set and up_nnode >= 0:
                            new_net.add_edge(nnode, up_nnode)
                        if left_nnode in node_set and left_nnode % NetM != NetM - 1:
                            new_net.add_edge(nnode, left_nnode)   

                    # to make sure that there exists shortest path
                    has_shortest_path = nx.has_path(new_net, source=src_pos, target=dest_pos)
                    if has_shortest_path:
                        shortest_path = nx.shortest_path(new_net, source=src_pos, target=dest_pos)
                        path_nodes = shortest_path[1:]
                        pre_node = src_pos
                        for nnode in path_nodes:
                            if nnode != dest_pos:
                                net.nodes[nnode]['node_val'] = - alloca_node
                            net.add_edge(pre_node, nnode)
                            net[pre_node][nnode]['con_qubits'] = {}
                            if pre_node == src_pos:
                                net[pre_node][nnode]['con_qubits'][pre_node] = graph[alloca_node][node_dest]['con_qubits'][alloca_node]
                            else:
                                net[pre_node][nnode]['con_qubits'][pre_node] = 0
                            if nnode == dest_pos:
                                net[pre_node][nnode]['con_qubits'][nnode] = graph[alloca_node][node_dest]['con_qubits'][node_dest]
                            else:
                                net[pre_node][nnode]['con_qubits'][nnode] = 0
                            pre_node = nnode
                        graph.remove_edge(alloca_node, node_dest)
                        if len(list(graph.neighbors(node_dest))) == 0:
                            graph.remove_node(node_dest)  
                            if node_dest in alloca_incomplete_nodes:
                                alloca_incomplete_nodes.remove(node_dest) 
                
                alloca_incomplete_nodes.remove(alloca_node)
                alloca_pos = alloca_nodes[alloca_node]
                if len(list(net.neighbors(alloca_pos))) == 0:
                    net.nodes[alloca_nodes[alloca_node]]['node_val'] = - GraphN - 1
                    if alloca_node in cur_layer_nodes:
                        cur_layer_nodes.remove(alloca_node)
                    
                    if alloca_node not in alloca_nodes_cache.keys():
                        # print("hello")
                        alloca_nodes_cache[alloca_node] = alloca_nodes[alloca_node]
                    del alloca_nodes[alloca_node]
                if len(list(graph.neighbors(alloca_node))) != 0:
                    failed_nodes.append(alloca_node)
                        # update graph after mapping
            all_nodes = list(graph.nodes()).copy() 
            for nnode in all_nodes:
                if len(list(graph.neighbors(nnode))) == 0:
                    graph.remove_node(nnode)  
    return net, graph



def compact_graph(fgraph, MaxDegree):
    # get fgraph information
    graph = fgraph.copy()
    # number of graph nodes
    GraphN = len(list(graph.nodes()))
    
    # collect mapping nets
    net_list = []

    # identify the mapping layer number
    layer_index = 0

    alloca_nodes = {}
    
    alloca_nodes_cache = {}
    
    # map and route
    while len(list(graph.nodes())):
        # get the cur layer order in partition graph
        cur_layer = -1
        for gnode in graph.nodes():
            if gnode not in alloca_nodes_cache.keys():
                if cur_layer == -1:
                    cur_layer = graph.nodes[gnode]['layer']
                else:
                    cur_layer = min(graph.nodes[gnode]['layer'], cur_layer)
        
        alloca_nodes.clear()
        alloca_nodes_index = 0
        exit_flag = 1
        for edge in graph.edges():
            if edge[0] in alloca_nodes_cache.keys() and edge[1] in alloca_nodes_cache.keys() and alloca_nodes_cache[edge[0]] == alloca_nodes_cache[edge[1]]:
                exit_flag = exit_flag
            else:
                exit_flag = 0
                break
        if exit_flag == 1:
            break
        copy_alloca_nodes_cache = alloca_nodes_cache.copy()
        index = 0
        for alloca_node in copy_alloca_nodes_cache.keys():
            if index >= NetM * NetN // 2:
                continue
            if alloca_nodes_cache[alloca_node] in alloca_nodes.values():
                continue
            for gnode in graph.neighbors(alloca_node):
                if graph.nodes[gnode]['layer'] <= cur_layer or cur_layer == -1:
                    alloca_nodes[alloca_node] = alloca_nodes_cache[alloca_node]
                    index += 1
                    del alloca_nodes_cache[alloca_node]
                    break
        
        # reserve pre graph to show the mapping net
        pre_graph = graph.copy()
        # map and route current layer nodes 
        net, graph = one_layer_map(graph, alloca_nodes, cur_layer, alloca_nodes_cache, MaxDegree)  

        # get the alloca nodes set  
        for nnode in net.nodes():
            if net.nodes[nnode]['node_val'] > 0 and net.nodes[nnode]['node_val'] in graph.nodes():
                alloca_nodes_cache[net.nodes[nnode]['node_val']] = nnode

        net_list.append(net)
        # show the mapping net and save it
        # save_net(pre_graph, net, alloca_nodes.values(), layer_index)
        layer_index += 1  
        print(len(list(graph.nodes())))

    print(GraphN, "nodes")
    print(layer_index, "layers") 
    return net_list