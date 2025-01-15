import networkx as nx
from itertools import combinations
import copy
import settings
import json

class haqa():
    def __init__(self, needed_p_qubit_num:int, p_edges:list, p_edge_cx_err:dict,
                 p_qubit_read_err:list, node_err:list, w:float=settings.w):
        self.static_node_err = node_err
        self.static_p_qubit_read_err = p_qubit_read_err
        self.static_p_edge_cx_err = {p_edge: p_edge_cx_err[p_edge] for p_edge in p_edges}
        self.w = w
        self.needed_p_qubit_num = needed_p_qubit_num
        self.p_edges = p_edges
        self.G_physical = nx.Graph()
        self.G_physical.add_edges_from(p_edges)
        self.static_G_physical = copy.deepcopy(self.G_physical)
        self.communities = [{node} for node in self.G_physical.nodes()]
        self.tree = []
    def run(self, num_seeds):
        print(f'Determining best areas...')
        best_communities_list = []
        best_area_list = []
        while len(best_communities_list)<num_seeds and len(self.G_physical.nodes)>=self.needed_p_qubit_num:
            communities = self.communities
            while all(len(com) < self.needed_p_qubit_num for com in communities):
                communities = self.properly_combine_two_communities(communities)
            best_communities_list.append(communities)
            community = [com for com in communities if len(com) >= self.needed_p_qubit_num][0]
            best_area_list.append(community)
            if len(best_communities_list)>=num_seeds:
                break
            # print(f'Currently found best areas: {best_area_list}')
            target_physical_qubit = self.find_last_important_qubit_in_community(community)
            for i, p_edge in enumerate(self.p_edges):
                if target_physical_qubit in p_edge:
                    del self.p_edges[i]
            self.G_physical = nx.Graph()
            self.G_physical.add_edges_from(self.p_edges)
            self.communities = [{node} for node in self.G_physical.nodes()]
        # save self.tree
        info = {}
        for i, tre in enumerate(self.tree):
            max_qubit_num = max([len(bb) for bb in tre])
            if max_qubit_num not in info.keys():
                info[max_qubit_num] = tre
        with open(fr'tree_{settings.platform}_{settings.day}.json', 'w') as json_file:
            for key, value in info.items():
                json_file.write(f'"{key}": {json.dumps(value)}\n')

        self.tree_structure = info

        return best_area_list


    def calculate_Q(self,communities):
        m = self.G_physical.number_of_edges()
        if m == 0:
            return 0
        A = nx.to_numpy_array(self.G_physical)
        temp_pi = [node for node in self.G_physical.nodes()]
        degrees = dict(self.G_physical.degree())
        Q = 0.0
        for community in communities:
            for u, v in combinations(community, 2):
                u_index,v_index = temp_pi.index(u),temp_pi.index(v)
                if u != v:
                    A_uv = A[u_index, v_index]
                    k_u = degrees[u]
                    k_v = degrees[v]
                    Q += (A_uv - k_u * k_v / (2 * m))
        Q = Q / (2 * m)
        return Q

    def calculate_wEV(self,com_i,com_j):
        cross_p_edge_cx_err = []
        for index, (p1,p2) in enumerate(self.p_edges):
            if p1 in com_i and p2 in com_j:
                cross_p_edge_cx_err.append(self.static_p_edge_cx_err[(p1, p2)])
            elif p1 in com_j and p2 in com_i:
                cross_p_edge_cx_err.append(self.static_p_edge_cx_err[(p1, p2)])
        if len(cross_p_edge_cx_err) == 0:
            avg_cross_p_edge_cx_err = 1
        else:
            avg_cross_p_edge_cx_err = sum(cross_p_edge_cx_err)/len(cross_p_edge_cx_err)
        E = 1- avg_cross_p_edge_cx_err
        wEV = self.w * E
        return wEV

    def properly_combine_two_communities(self, communities):
        new_communities_list = []
        new_communities_Q_plus_wEV_list = []
        # 对于每一对社区
        for i in range(len(self.communities)):
            for j in range(i + 1, len(communities)):
                # combine to new community
                new_communities = communities[:i] + communities[i+1:j] + communities[j+1:] + [communities[i] | communities[j]]
                # cal Q and wEV
                Q = self.calculate_Q(new_communities)
                wEV = self.calculate_wEV(communities[i],communities[j])
                Q_plus_wEV = Q + wEV
                new_communities_list.append(new_communities)
                new_communities_Q_plus_wEV_list.append(Q_plus_wEV)
        # sort
        combined = sorted(zip(new_communities_Q_plus_wEV_list, new_communities_list), key=lambda x: x[0], reverse=True)
        # get sorted new_communities_Q_plus_wEV_list and new_communities_list
        new_communities_Q_plus_wEV_list, new_communities_list = zip(*combined)
        aaa = new_communities_list[0]
        aaa = [list(kk) for kk in aaa]
        print(f'find partition = {aaa}')
        bbb = max(aaa, key=len)
        self.tree.append(aaa)
        for Q_plus_wEV, new_communities in zip(new_communities_Q_plus_wEV_list, new_communities_list):
            max_size = max(len(community) for community in new_communities)
            largest_communities = [list(community) for community in new_communities if len(community) == max_size][0]
            subgraph = self.static_G_physical.subgraph(largest_communities)
            # check connectivity
            # if less than 2 nodes, set to connected
            if len(subgraph) < 2:
                connected = True
            else:
                connected = nx.is_connected(subgraph)
            if connected:
                return new_communities

    def find_last_important_qubit_in_community(self,community):
        # calculate degree
        community = list(community)
        p_qubit_degrees = [self.static_G_physical.degree(p_qubit) for p_qubit in community]
        min_degree = min(p_qubit_degrees)  # min degree
        min_degree_p_qubits = [p_qubit for p_qubit,p_degree  # physical nodes with minimal degree
                              in zip(community,p_qubit_degrees) if p_degree==min_degree]
        # output
        if len(min_degree_p_qubits) == 1:
            return min_degree_p_qubits[0]
        else:
            target_p_qubit = None
            avg_err = 0
            for p_qubit in min_degree_p_qubits:
                # cal avg cx error
                err = []
                for i, p_edge in enumerate(self.p_edges):
                    if p_qubit in p_edge:
                        err.append(self.static_p_edge_cx_err[p_edge])
                current_avg_err = sum(err)/len(err)
                if current_avg_err > avg_err:
                    target_p_qubit = p_qubit
                    avg_err = current_avg_err
            return target_p_qubit


