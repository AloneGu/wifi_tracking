import numpy as np
from sklearn.neighbors import KNeighborsClassifier

TEST_DATA_ROWS = 20
SRC_FILE = '../calibration_data/bssidlist_2016111.txt'


def parse_txt():
    place_set = set()
    f = open(SRC_FILE)
    content = f.readlines()

    # key: zone name, value: lists of signal strength list. like {'A':[[-22,-23,-44],[-34,-23,-33]]}
    data_dict = {}
    bssid_list = ['9c:d9:17:88:77:93', '9c:d9:17:86:63:97', '14:1a:a3:d4:3c:19']
    print 'bssid_list', bssid_list  # use the most common bssids to build the map

    # parse the data according to the bssid list
    for row in content:
        first_colon_index = row.find(':')
        place = row[:first_colon_index]
        place_set.add(place)
        data = eval(row[first_colon_index + 1:])

        for k in data.keys():
            if k not in bssid_list:
                del (data[k])  # deleted the signal strength of other bssids
        for bssid in bssid_list:
            if bssid not in data:
                data[bssid] = '-100'  # set the default signal strength -100

        # print place,data
        tmp_x_data = [int(data[bssid]) for bssid in bssid_list]

        if place not in data_dict:
            data_dict[place] = []
        data_dict[place].append(tmp_x_data)

    return data_dict


def build_x_y_data(data_dict):
    x_data = []
    y_data = []
    # key: path like ('A','B'), value: int like 1
    path_int_dict = {}
    start_int = 1
    places = data_dict.keys()
    print 'zones', places
    places_cnt = len(places)
    for i in range(places_cnt - 1):
        for j in range(i + 1, places_cnt, 1):
            place_a = places[i]
            place_b = places[j]
            # A to B
            for end_sn_list in data_dict[place_b]:
                for start_sn_list in data_dict[place_a]:
                    tmp_x_data = [x - y for (x, y) in zip(end_sn_list, start_sn_list)]  # signal difference from A to B
                    tmp_path = (place_a, place_b)
                    if tmp_path not in path_int_dict:
                        path_int_dict[tmp_path] = start_int
                        start_int += 1
                    tmp_y_data = path_int_dict[tmp_path]
                    # added to training data
                    x_data.append(tmp_x_data)
                    y_data.append(tmp_y_data)

            # B to A
            for end_sn_list in data_dict[place_a]:
                for start_sn_list in data_dict[place_b]:
                    tmp_x_data = [x - y for (x, y) in zip(end_sn_list, start_sn_list)]  # signal difference from B to A
                    tmp_path = (place_b, place_a)
                    if tmp_path not in path_int_dict:
                        path_int_dict[tmp_path] = start_int
                        start_int += 1
                    tmp_y_data = path_int_dict[tmp_path]
                    # added to training data
                    x_data.append(tmp_x_data)
                    y_data.append(tmp_y_data)

    return x_data, y_data, places_cnt, path_int_dict


def get_model():
    data_dict = parse_txt()
    x_data, y_data, places_cnt, path_int_dict = build_x_y_data(data_dict)
    # start to train, change list type to numpy.array
    x_data = np.array(x_data)
    y_data = np.array(y_data)
    knn = KNeighborsClassifier()
    knn.fit(x_data, y_data)  # work
    return knn, path_int_dict


def main_process():
    data_dict = parse_txt()
    x_data, y_data, places_cnt, path_int_dict = build_x_y_data(data_dict)
    print 'data counts', len(x_data), len(y_data)
    print 'zone names counts', places_cnt
    print 'path counts', len(path_int_dict)

    # start to train, change list type to numpy.array
    x_data = np.array(x_data)
    y_data = np.array(y_data)

    knn = KNeighborsClassifier()

    indices = np.random.permutation(len(x_data))
    x_train = x_data
    y_train = y_data
    x_test = x_data[indices[-TEST_DATA_ROWS:]]
    y_test = y_data[indices[-TEST_DATA_ROWS:]]
    knn.fit(x_train, y_train)  # work

    test_result = knn.predict(x_test)  # test
    proba_test_result = knn.predict_proba(x_test)

    # no duplicate value, so reverse this dictionary
    int_path_dict = dict(zip(path_int_dict.values(), path_int_dict.keys()))

    print 'predict result:', test_result
    print [int_path_dict[x] for x in test_result]  # test result
    print 'ground truth:', y_test
    print [int_path_dict[y] for y in y_test]  # ground truth
    print 'probability', proba_test_result
    compare_result = [test_result[i] == y_test[i] for i in range(TEST_DATA_ROWS)]
    print 'accurate rate', sum(compare_result) * 1.0 / TEST_DATA_ROWS


if __name__ == '__main__':
    main_process()
