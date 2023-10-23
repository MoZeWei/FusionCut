import numpy as np
import math

def add_round(fgraph, nround):
    def get_layer(data):
        layer_list = []
        for d in data:
            layer_list.append(fgraph.nodes[d]['layer'])
        return layer_list
    gnodes = np.array(list(fgraph.nodes()))
    sorted_indices = np.argsort(get_layer(gnodes))
    sorted_gnodes = gnodes[sorted_indices]
    upper_bound = math.ceil(len(sorted_gnodes) / nround)
    layer_index = 0
    index = 0
    for gnode in sorted_gnodes:
        if index < upper_bound:
            index += 1
            fgraph.nodes[gnode]['layer'] = layer_index
        else:
            index = 0
            fgraph.nodes[gnode]['layer'] = layer_index + 1
            layer_index += 1
    return fgraph
