import numpy as np
from sklearn.neighbors import KNeighborsClassifier

# Auto generate the bssidlist

PALO_ALTO_FLAG = 1
AUTO_BSSID_LIST_FLAG = 0
TRAINING_DATA = '../calibration_data/bssidlist_palto_2016119.txt' if PALO_ALTO_FLAG else '../calibration_data/bssidlist.txt'

TEST_DATA_ROWS = 20


def parse_txt():
    bssid_cnt = {}
    place_set = set()
    f = open(TRAINING_DATA)
    content = f.readlines()
    x_data, y_data = [], []
    zone_int_dict = {}
    start_int = 1

    for row in content:
        first_colon_index = row.find(':')
        data = eval(row[first_colon_index + 1:])
        for k in data.keys():
            if k not in bssid_cnt:
                bssid_cnt[k] = 0
            bssid_cnt[k] += 1

    if AUTO_BSSID_LIST_FLAG:
        import operator
        sorted_result = sorted(bssid_cnt.items(), key=operator.itemgetter(1))
        print 'sort keys', sorted_result
        bssid_list = [x[0] for x in sorted_result[-5:]]
    else:
        # bssid_list = ['6c:72:20:11:12:60','74:d0:2b:5d:40:0a','00:0f:13:39:21:25'] # china office
        # bssid_list = ['2c:5d:93:3b:40:58','f2:14:24:07:bf:90','c0:a0:bb:c5:61:56','80:ea:96:f3:7d:e8','f0:99:bf:07:24:14'] # palo alto office
        # bssid_list = ['9c:d9:17:88:77:93','9c:d9:17:86:63:97','14:1a:a3:d4:3c:19'] # 3 device hotspot
        bssid_list = ['90:68:c3:3e:55:d8', 'ec:88:92:25:82:8c', 'f4:f1:e1:57:a4:f8']  # new test device palo alto office
    print 'bssid_list', bssid_list  # use the 5 most common bssid to build the map

    for row in content:
        first_colon_index = row.find(':')
        place = row[:first_colon_index]
        place_set.add(place)
        data = eval(row[first_colon_index + 1:])

        for k in data.keys():
            if k not in bssid_list:
                del (data[k])
        for bssid in bssid_list:
            if bssid not in data:
                data[bssid] = '-100'

        # print place,data

        tmp_x_data = [int(data[bssid]) for bssid in bssid_list]
        if place not in zone_int_dict:
            zone_int_dict[place] = start_int
            start_int += 1
        tmp_y_data = zone_int_dict[place]
        y_data.append(tmp_y_data)
        x_data.append(tmp_x_data)
        # print place,tmp_x_data

    x_data = np.array(x_data)
    y_data = np.array(y_data)
    return x_data, y_data, len(place_set), zone_int_dict


def train_data():
    x_data, y_data, zone_cnt, zone_int_dict = parse_txt()

    knn = KNeighborsClassifier()

    indices = np.random.permutation(len(x_data))
    x_train = x_data
    y_train = y_data
    x_test = x_data[indices[-TEST_DATA_ROWS:]]
    y_test = y_data[indices[-TEST_DATA_ROWS:]]
    knn.fit(x_train, y_train)  # start training
    print 'training data count:', len(indices), ' number of zones:', zone_cnt
    test_result = knn.predict(x_test)  # test
    prob_test_result = knn.predict_proba(x_test)
    print prob_test_result

    # no duplicate value, so reverse this dictionary
    int_zone_dict = dict(zip(zone_int_dict.values(), zone_int_dict.keys()))

    print 'predict result:', test_result, [int_zone_dict[x] for x in test_result]  # test result
    print 'ground truth:', y_test, [int_zone_dict[x] for x in y_test]  # ground truth
    cnt = 0
    for i in range(TEST_DATA_ROWS):
        if test_result[i] == y_test[i]:
            cnt += 1
    print 'accurate rate', cnt * 1.0 / TEST_DATA_ROWS


def get_model():
    x_data, y_data, zone_cnt, zone_int_dict = parse_txt()
    knn = KNeighborsClassifier()
    knn.fit(x_data, y_data)
    return knn, zone_int_dict


if __name__ == '__main__':
    train_data()
