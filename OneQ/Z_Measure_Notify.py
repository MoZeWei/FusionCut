def z_measure_notify(net_list, max_degree):
    for net in net_list:
        for nnode in net.nodes():
            if net.nodes[nnode]['node_val'] > 0:
                avail_nodes = []
                for i in range(max_degree):
                    avail_nodes.append(i)
                neigh_nodes = list(net.neighbors(nnode))
                end_con_qubit  = 0
                for neigh_node in neigh_nodes:
                    for con_qubit in net[nnode][neigh_node]['con_qubits']:
                        if con_qubit[nnode] in avail_nodes:
                            if con_qubit[nnode] == max_degree - 1:
                                end_con_qubit = con_qubit
                                end_neigh_node = neigh_node
                            avail_nodes.remove(con_qubit[nnode])
                        else:
                            print("error")
                            return net_list
                for i in range(max_degree):
                    index = 0
                    phase_pos = 0
                    if i in avail_nodes:
                        if index < len(net.nodes[nnode]['phase']):
                            net.nodes[nnode][i] = net.nodes[nnode]['phase'][index]
                            phase_pos = i
                            index += 1
                        else:
                            break
                    else:
                        net.nodes[nnode][i] = -1
                phase_pos = max(phase_pos + 2, avail_nodes[0] + 1)
                net.nodes[nnode][phase_pos - 1] = -1
                for i in range(phase_pos, max_degree):
                    net.nodes[nnode][i] = 'z'
                
                if end_con_qubit != 0:
                    net[nnode][end_neigh_node]['con_qubits'].remove(end_con_qubit)
                    net[nnode][end_neigh_node]['con_qubits'].append({nnode: phase_pos + 1, end_neigh_node: end_con_qubit[end_neigh_node]})
            elif net.nodes[nnode]['node_val'] != -1000001:
                avail_nodes = []
                for i in range(max_degree):
                    avail_nodes.append(i)
                neigh_nodes = list(net.neighbors(nnode))
                for neigh_node in neigh_nodes:
                    for con_qubit in net[nnode][neigh_node]['con_qubits']:
                        if con_qubit[nnode] in avail_nodes:
                            if con_qubit[nnode] == max_degree - 1:
                                end_con_qubit = con_qubit
                                end_neigh_node = neigh_node
                            avail_nodes.remove(con_qubit[nnode])
                        else:
                            print("error")
                            return net_list
                for i in range(max_degree):
                    phase_pos = 0
                    if i in avail_nodes:
                        net.nodes[nnode][i] = 'z'
                    else:
                        net.nodes[nnode][i] = -1
                        
    return net_list
