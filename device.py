
import os
import csv
import re
import copy
import networkx as nx


class qdevice():
    def __init__(self, device_name, **kwargs):
        if 'adjust_mapping_to_natural_nums_from_zero' in kwargs:
            self.adjust_mapping_to_natural_nums_from_zero = kwargs['adjust_mapping_to_natural_nums_from_zero']

        self.device_name = device_name

        if device_name == 'ibm_eagle':
            self.coupling_map, self.available_pqubits = self.get_coupling(device_name)
            self.pqubit_number = self.get_qubit_num(device_name)
            self.get_basis_gates(device_name)

            self.G_coupling_nx = nx.Graph()
            self.G_coupling_nx.add_edges_from(self.coupling_map)
            self.coupling_map_max_degree = max(dict(self.G_coupling_nx.degree()).values())
            # distance matrix
            self.distance_matrix = self._get_distance_matrix(self.G_coupling_nx)

            # calculate average degree
            self.pqubit_avg_degree = 2 * len(self.coupling_map) / self.pqubit_number

            # ------ noise data ------ #
            if 'noise_file_dir' in kwargs:
                noise_file_dir = kwargs['noise_file_dir']
                self._search_noise_files(noise_file_dir)

            if 'computer_name' in kwargs and 'day' in kwargs and 'day_num' in kwargs:
                self.computer_name = kwargs['computer_name']
                self.day = kwargs['day']
                self.day_num = kwargs['day_num']
                self.get_error(self.computer_name, self.day, self.day_num)

        elif device_name == 'ibm_heron':
            self.coupling_map, self.available_pqubits = self.get_coupling(device_name)
            self.pqubit_number = self.get_qubit_num(device_name)
            self.get_basis_gates(device_name)

            self.G_coupling_nx = nx.Graph()
            self.G_coupling_nx.add_edges_from(self.coupling_map)
            self.coupling_map_max_degree = max(dict(self.G_coupling_nx.degree()).values())
            # distance matrix
            self.distance_matrix = self._get_distance_matrix(self.G_coupling_nx)

            # calculate average degree
            self.pqubit_avg_degree = 2 * len(self.coupling_map) / self.pqubit_number

            # ------ noise data ------ #
            if 'noise_file_dir' in kwargs:
                noise_file_dir = kwargs['noise_file_dir']
                self._search_noise_files(noise_file_dir)

            if 'computer_name' in kwargs and 'day' in kwargs and 'day_num' in kwargs:
                self.computer_name = kwargs['computer_name']
                self.day = kwargs['day']
                self.day_num = kwargs['day_num']
                self.get_error(self.computer_name, self.day, self.day_num)
            pass


    def get_coupling(self, device_name):
        coupling_graphs = {
                         "ibm_eagle": [(1, 0), (2, 1), (3, 2), (4, 5), (4, 3), (4, 15), (6, 7), (6, 5), (7, 8), (8, 9),
                                       (10, 11), (10, 9), (11, 12), (12, 17), (13, 12), (14, 0), (14, 18), (15, 22),
                                       (16, 26), (16, 8), (17, 30), (18, 19), (20, 33), (20, 19), (21, 20), (21, 22),
                                       (22, 23), (24, 34), (24, 23), (25, 24), (26, 25), (27, 26), (28, 35), (28, 27),
                                       (28, 29), (30, 31), (30, 29), (31, 32), (32, 36), (33, 39), (34, 43), (35, 47),
                                       (36, 51), (37, 38), (39, 38), (40, 41), (40, 39), (41, 53), (42, 41), (42, 43),
                                       (43, 44), (44, 45), (46, 45), (46, 47), (48, 47), (48, 49), (50, 51), (50, 49),
                                       (52, 37), (52, 56), (53, 60), (54, 45), (54, 64), (55, 49), (55, 68), (56, 57),
                                       (57, 58), (58, 71), (58, 59), (59, 60), (60, 61), (62, 61), (62, 63), (62, 72),
                                       (63, 64), (65, 64), (65, 66), (67, 66), (67, 68), (69, 68), (69, 70), (73, 66),
                                       (74, 70), (74, 89), (75, 90), (76, 75), (77, 78), (77, 71), (77, 76), (79, 80),
                                       (79, 78), (80, 81), (81, 82), (81, 72), (82, 83), (83, 92), (84, 83), (85, 84),
                                       (85, 73), (85, 86), (86, 87), (87, 88), (88, 89), (91, 79), (92, 102), (93, 87),
                                       (93, 106), (94, 90), (94, 95), (95, 96), (97, 98), (97, 96), (98, 91), (99, 98),
                                       (100, 99), (100, 110), (101, 102), (101, 100), (102, 103), (104, 103), (105, 106),
                                       (105, 104), (107, 106), (108, 107), (108, 112), (109, 96), (110, 118), (111, 104),
                                       (112, 126), (113, 114), (114, 115), (114, 109), (116, 117), (116, 115), (117, 118),
                                       (118, 119), (120, 119), (121, 120), (122, 111), (122, 123), (122, 121), (124, 123),
                                       (125, 126), (125, 124)],
                         'ibm_heron':  [(0, 15), (0, 1), (1, 2), (1, 0), (2, 3), (2, 1), (3, 2), (3, 4), (4, 16),
                                        (4, 3), (4, 5), (5, 6), (5, 4), (6, 7), (6, 5), (7, 6), (7, 8), (8, 17), (8, 7),
                                        (8, 9), (9, 10), (9, 8), (10, 11), (10, 9), (11, 10), (11, 12), (12, 18),
                                        (12, 11), (12, 13), (13, 14), (13, 12), (14, 13), (15, 19), (15, 0), (16, 23),
                                        (16, 4), (17, 27), (17, 8), (18, 31), (18, 12), (19, 15), (19, 20), (20, 19),
                                        (20, 21), (21, 34), (21, 22), (21, 20), (22, 23), (22, 21), (23, 16), (23, 22),
                                        (23, 24), (24, 23), (24, 25), (25, 35), (25, 26), (25, 24), (26, 27), (26, 25),
                                        (27, 17), (27, 26), (27, 28), (28, 27), (28, 29), (29, 36), (29, 30), (29, 28),
                                        (30, 31), (30, 29), (31, 18), (31, 30), (31, 32), (32, 31), (32, 33), (33, 37),
                                        (33, 32), (34, 40), (34, 21), (35, 44), (35, 25), (36, 48), (36, 29), (37, 52),
                                        (37, 33), (38, 53), (38, 39), (39, 40), (39, 38), (40, 34), (40, 41), (40, 39),
                                        (41, 40), (41, 42), (42, 54), (42, 41), (42, 43), (43, 44), (43, 42), (44, 35),
                                        (44, 45), (44, 43), (45, 44), (45, 46), (46, 55), (46, 45), (46, 47), (47, 48),
                                        (47, 46), (48, 36), (48, 49), (48, 47), (49, 48), (49, 50), (50, 56), (50, 49),
                                        (50, 51), (51, 52), (51, 50), (52, 37), (52, 51), (53, 57), (53, 38), (54, 61),
                                        (54, 42), (55, 65), (55, 46), (56, 69), (56, 50), (57, 53), (57, 58), (58, 57),
                                        (58, 59), (59, 72), (59, 60), (59, 58), (60, 61), (60, 59), (61, 54), (61, 60),
                                        (61, 62), (62, 61), (62, 63), (63, 73), (63, 64), (63, 62), (64, 65), (64, 63),
                                        (65, 55), (65, 64), (65, 66), (66, 65), (66, 67), (67, 74), (67, 68), (67, 66),
                                        (68, 69), (68, 67), (69, 56), (69, 68), (69, 70), (70, 69), (70, 71), (71, 75),
                                        (71, 70), (72, 78), (72, 59), (73, 82), (73, 63), (74, 86), (74, 67), (75, 90),
                                        (75, 71), (76, 91), (76, 77), (77, 78), (77, 76), (78, 72), (78, 79), (78, 77),
                                        (79, 78), (79, 80), (80, 92), (80, 79), (80, 81), (81, 82), (81, 80), (82, 73),
                                        (82, 83), (82, 81), (83, 82), (83, 84), (84, 93), (84, 83), (84, 85), (85, 86),
                                        (85, 84), (86, 74), (86, 87), (86, 85), (87, 86), (87, 88), (88, 94), (88, 87),
                                        (88, 89), (89, 90), (89, 88), (90, 75), (90, 89), (91, 95), (91, 76), (92, 99),
                                        (92, 80), (93, 103), (93, 84), (94, 107), (94, 88), (95, 91), (95, 96), (96, 95),
                                        (96, 97), (97, 110), (97, 98), (97, 96), (98, 99), (98, 97), (99, 92), (99, 98),
                                        (99, 100), (100, 99), (100, 101), (101, 111), (101, 102), (101, 100), (102, 103),
                                        (102, 101), (103, 93), (103, 102), (103, 104), (104, 103), (104, 105), (105, 112),
                                        (105, 106), (105, 104), (106, 107), (106, 105), (107, 94), (107, 106), (107, 108),
                                        (108, 107), (108, 109), (109, 113), (109, 108), (110, 116), (110, 97), (111, 120),
                                        (111, 101), (112, 124), (112, 105), (113, 128), (113, 109), (114, 129), (114, 115),
                                        (115, 116), (115, 114), (116, 110), (116, 117), (116, 115), (117, 116), (117, 118),
                                        (118, 130), (118, 117), (118, 119), (119, 120), (119, 118), (120, 111), (120, 121),
                                        (120, 119), (121, 120), (121, 122), (122, 131), (122, 121), (122, 123), (123, 124),
                                        (123, 122), (124, 112), (124, 125), (124, 123), (125, 124), (125, 126), (126, 132),
                                        (126, 125), (126, 127), (127, 128), (127, 126), (128, 113), (128, 127), (129, 114),
                                        (130, 118), (131, 122), (132, 126)],
                           }

        coupling_map = coupling_graphs[device_name]


        available_pqubits = []
        for (i,j) in coupling_graphs[device_name]:
            if i not in available_pqubits:
                available_pqubits.append(i)
            if j not in available_pqubits:
                available_pqubits.append(j)

        return coupling_map, available_pqubits

    def get_qubit_num(self, device_name):
        qubit_nums = {
                    "ibm_eagle": 127,
                    'ibm_heron': 133,
                    }
        return qubit_nums[device_name]


    def get_basis_gates(self, device_name):
        basis_gates = {
            "ibm_eagle": ['ECR','ID','RZ','SX','X'],
            'ibm_heron': ['CZ','ID','RZ','SX','X']
        }
        self.basis_gates = basis_gates.get(device_name, None)

    def get_error(self,
                  computer_name,
                  day:str,
                  num):

        def get_1qu_column_info(target_csv, col_index, store_list):
            with open(target_csv, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) > col_index:
                        store_list.append(row[col_index])

            store_list.pop(0)
            store_list = [float(ele) for ele in store_list]
            return store_list

        def get_2qu_column_info(target_csv, col_index):
            column_contents = []
            with open(target_csv, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row[col_index] != '' and len(row) > col_index:
                        column_contents.append(row[col_index])

            pattern_xy = r"(\d+_\d+)"
            pattern_z = r"(\d+\.\d+)"
            p_edge_feature_dict = {}
            for item in column_contents:
                matches_xy = re.findall(pattern_xy, item)
                matches_z = re.findall(pattern_z, item)
                # add xy and z to result
                for xy, z in zip(matches_xy, matches_z):
                    x_str, y_str = xy.split('_')
                    # trans to integer
                    x = int(x_str)
                    y = int(y_str)
                    z = float(z)
                    p_edge_feature_dict[(x, y)] = z
                if ';' in item:
                    parts = item.split(';')
                    for part in parts:
                        matches_xy_part = re.findall(pattern_xy, part)
                        matches_z_part = re.findall(pattern_z, part)
                        for xy, z in zip(matches_xy_part, matches_z_part):
                            x_str, y_str = xy.split('_')
                            x = int(x_str)
                            y = int(y_str)
                            z = float(z)
                            p_edge_feature_dict[(x, y)] = z

            new_ecr_error = copy.deepcopy(p_edge_feature_dict)
            for key, value in p_edge_feature_dict.items():
                # swap elements
                new_key = (key[1], key[0])
                # add new key-value
                new_ecr_error[new_key] = value
            return new_ecr_error

        target_csvs = [file for file in self.csv_files if computer_name in file and day in file]
        target_csv = target_csvs[num]

        self.computer_name = computer_name
        self.day = day

        # single qubit info
        t1,t2,frequcncy,readout_error,id_error,rz_error,sx_error,paulix_error = [],[],[],[],[],[],[],[]

        t1 = get_1qu_column_info(target_csv=target_csv, col_index=1, store_list=t1)
        t2 = get_1qu_column_info(target_csv=target_csv, col_index=2, store_list=t2)
        frequcncy = get_1qu_column_info(target_csv=target_csv, col_index=3, store_list=frequcncy)
        readout_error = get_1qu_column_info(target_csv=target_csv, col_index=5, store_list=readout_error)
        id_error = get_1qu_column_info(target_csv=target_csv, col_index=9, store_list=id_error)
        rz_error = get_1qu_column_info(target_csv=target_csv, col_index=10, store_list=rz_error)
        sx_error = get_1qu_column_info(target_csv=target_csv, col_index=11, store_list=sx_error)
        paulix_error = get_1qu_column_info(target_csv=target_csv, col_index=12, store_list=paulix_error)

        t1 = {index: value for index, value in enumerate(t1)}
        t2 = {index: value for index, value in enumerate(t2)}
        frequcncy = {index: value for index, value in enumerate(frequcncy)}
        readout_error = {index: value for index, value in enumerate(readout_error)}
        id_error = {index: value for index, value in enumerate(id_error)}
        rz_error = {index: value for index, value in enumerate(rz_error)}
        sx_error = {index: value for index, value in enumerate(sx_error)}
        paulix_error = {index: value for index, value in enumerate(paulix_error)}

        ecr_error = get_2qu_column_info(target_csv, 13)
        gate_time = get_2qu_column_info(target_csv, 14)

        self.t1, self.t2, self.frequency, self.readout_error, self.id_error, self.rz_error, self.sx_error, self.paulix_error, self.ecr_error, self.gate_time = \
        t1, t2, frequcncy, readout_error, id_error, rz_error, sx_error, paulix_error, ecr_error, gate_time


    def _search_noise_files(self, noise_file_dir):
        csv_files = []
        for root, _, files in os.walk(noise_file_dir):
            for file in files:
                if file.endswith(".csv") or file.endswith(".xlsx"):
                    csv_files.append(os.path.join(root, file))
        self.csv_files = sorted(csv_files)

    def _get_distance_matrix(self, g_nx):
        large_distance = 100000
        nodes = list(g_nx.nodes)
        distances = {}
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                try:
                    distance = nx.shortest_path_length(g_nx, source=node1, target=node2)
                except nx.NetworkXNoPath:
                    distance = large_distance
                distances[(node1, node2)] = distance
                distances[(node2, node1)] = distance

        return distances