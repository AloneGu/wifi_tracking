from backend_common.storage import storage_manager
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import glob
import re
import gzip
import csv
import datetime

PALO_ALTO_FLAG = 1
AUTO_BSSID_LIST_FLAG = 0
TRAINING_DATA = '../calibration_data/bssidlist_palto_2016119.txt'

TEST_DATA_ROWS = 20
RESULT_CSV = 'pa_office_result_zone.csv'
ROUTERS = ['90:68:c3:3e:55:d8', 'ec:88:92:25:82:8c', 'f4:f1:e1:57:a4:f8']
PLC_ROUTER_DICT = {'8100236': '90:68:c3:3e:55:d8', '8600207': 'ec:88:92:25:82:8c', '8100128': 'f4:f1:e1:57:a4:f8'}
ROUTERS_NUM = len(ROUTERS)

from wifi_util.wifi_vendor import get_vendor_checker

placements = ['8100236','8600207','8100128']
date_time = '2016-01-19'
local_path = '../data/39/'

def download_file():
    for p in placements:
        remote_path = 'gs://percolata-data/data/combined/wifi/'+p+'/'+date_time
        storage_manager.download_dir_to_local(remote_path,local_path)
        print 'download',remote_path,local_path

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
        bssid_list = ['90:68:c3:3e:55:d8', 'ec:88:92:25:82:8c', 'f4:f1:e1:57:a4:f8']  # new test device palo alto office:8100236,8600207,8100128
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

def get_model():
    x_data, y_data, zone_cnt, zone_int_dict = parse_txt()
    knn = KNeighborsClassifier()
    knn.fit(x_data, y_data)
    return knn, zone_int_dict

def main():
    #download_file()
    KNN, zone_int_dict = get_model()
    # no duplicate value, so reverse this dictionary
    int_zone_dict = dict(zip(zone_int_dict.values(), zone_int_dict.keys()))
    file_list = glob.glob(local_path + date_time + '/*csv.gz')
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
                        # routers a,b,c if phone send 2 pkgs(c,d) c is detected by a, d is detected by b,c ,can get good result without seqid as key
                        tmp_key = (mac, time)
                        if tmp_key not in mac_sn_dict:
                            mac_sn_dict[tmp_key] = [-100] * ROUTERS_NUM
                        mac_sn_dict[tmp_key][index] = sn

        except Exception as e:
            print e
            print f
    fout = open(RESULT_CSV, 'w')
    writer = csv.writer(fout)
    writer.writerow(['mac', 'time'] + ROUTERS + ['zone'])
    vender_checker = get_vendor_checker()
    data_row_cache = []

    for key in mac_sn_dict:
        mac = key[0]
        if str(mac) in ROUTERS:
            continue
        vender = vender_checker.get_manuf(str(mac))
        time = datetime.datetime.utcfromtimestamp(key[1] - 8 * 60 * 60)  # transfer to local time
        x_data = np.array([map(int, mac_sn_dict[key])])
        predict_result = int_zone_dict[int((KNN.predict(x_data)[0]))]
        tmp_probability = max(KNN.predict_proba(x_data)[0])
        data_row_cache.append([mac, time] + mac_sn_dict[key] + [predict_result, vender])

    print 'sort the result'
    data_row_cache = sorted(data_row_cache, key=lambda x: (x[0], x[1]))

    for row in data_row_cache:
        writer.writerow(row)
    print 'finished'

if __name__=='__main__':
    main()