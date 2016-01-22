import glob
import csv
import gzip
import datetime
import numpy
import re
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from wifi_util.wifi_vendor import get_vendor_checker

SRC_FILE = '../calibration_data/bssidlist_palto_2016119.txt'
SRC_FOLDER = '../data/39/2016-01-19'
RESULT_CSV = 'pa_office_result_path.csv'
ROUTERS = ['90:68:c3:3e:55:d8', 'ec:88:92:25:82:8c', 'f4:f1:e1:57:a4:f8']
PLC_ROUTER_DICT = {'8100236': '90:68:c3:3e:55:d8', '8600207': 'ec:88:92:25:82:8c', '8100128': 'f4:f1:e1:57:a4:f8'}
ROUTERS_NUM = len(ROUTERS)

def parse_txt():
    place_set = set()
    f = open(SRC_FILE)
    content = f.readlines()

    # key: zone name, value: lists of signal strength list. like {'A':[[-22,-23,-44],[-34,-23,-33]]}
    data_dict = {}
    bssid_list = ROUTERS
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
    KNN, path_int_dict = get_model()
    # no duplicate value, so reverse this dictionary
    int_path_dict = dict(zip(path_int_dict.values(), path_int_dict.keys()))
    file_list = glob.glob(SRC_FOLDER + '/*csv.gz')
    # mac_sn_dict : { (mac_address,time_accurate_to_10_seconds):[signal_strength according to the routers] }
    mac_sn_dict = {}
    for f in file_list:
        placement_name = re.findall("\d{7}", f)[0]
        router_bssid = PLC_ROUTER_DICT[placement_name]
        try:
            with gzip.open(f, 'rb') as fp:
                reader = csv.reader(fp)
                for row in reader:
                    # jump first row
                    if reader.line_num == 1:
                        continue
                    # process each ros
                    mac = str(row[3]).lower()
                    ssid = str(row[7])
                    time = int(row[0]) / 10 * 10
                    sn = int(row[6])
                    if router_bssid in ROUTERS:
                        index = ROUTERS.index(router_bssid)
                        tmp_key = (mac, time)
                        if tmp_key not in mac_sn_dict:
                            mac_sn_dict[tmp_key] = [-100] * ROUTERS_NUM
                        mac_sn_dict[tmp_key][index] = sn

        except Exception as e:
            print e
            print f
    fout = open(RESULT_CSV, 'w')
    writer = csv.writer(fout)
    writer.writerow(['mac', 'time'] + ROUTERS + ['path', 'probability', 'vendor'])
    data_row_cache = []
    for key in mac_sn_dict:
        mac = key[0]
        if str(mac) in ROUTERS:
            continue
        time = datetime.datetime.utcfromtimestamp(key[1] - 8 * 60 * 60)  # transfer to local time
        data_row_cache.append([mac, time] + mac_sn_dict[key])

    print 'sort the result'
    data_row_cache = sorted(data_row_cache, key=lambda x: (x[0], x[1]))

    row_len = len(data_row_cache)
    diff_sn_cache = []
    new_data_row_cache = []
    for i in range(row_len - 2):
        mac_a = data_row_cache[i][0]
        mac_b = data_row_cache[i + 1][0]
        # delete last row, save the info in new_data_row_cache
        if mac_a != mac_b:
            continue
        start_sn_list = data_row_cache[i][-3:]
        end_sn_list = data_row_cache[i + 1][-3:]
        # A to B
        diff_sn = [x - y for (x, y) in zip(end_sn_list, start_sn_list)]
        diff_sn_cache.append(diff_sn)
        new_data_row_cache.append(data_row_cache[i])

    # predict
    predict_result = KNN.predict(numpy.array(diff_sn_cache))
    proba_result = KNN.predict_proba(numpy.array(diff_sn_cache))

    # add path,probability,vendor
    row_len = len(new_data_row_cache)
    vender_checker = get_vendor_checker()
    for i in range(row_len - 1):
        mac = new_data_row_cache[i][0]
        tmp_path = int_path_dict[predict_result[i]]
        tmp_proba = max(proba_result[i])
        vender = vender_checker.get_manuf(str(mac))
        new_data_row_cache[i] += [str(tmp_path), tmp_proba, vender]

    # save in csv
    for row in new_data_row_cache:
        writer.writerow(row)
    print 'finished'


if __name__ == '__main__':
    main_process()
