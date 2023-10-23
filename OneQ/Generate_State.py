import networkx as nx
import matplotlib.pyplot as plt
import random

def generate_state(nqubit):
    G = nx.gnp_random_graph(nqubit, 0.1) #0.2
    return G

# G = generate_state(10)
# nx.draw(G)
# # plt.show()