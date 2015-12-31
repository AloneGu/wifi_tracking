import os
import csv
import gzip
import datetime
import numpy
from wifi_util.download_csv import download_csv
from wifi_tracking_training import number_to_char,get_model

LOCAL_DIR = './data/'
REMOTE_DIR = 'data/combined/wifi/'
LOCATION_ID = '39'
placements = ['8100109','8100110','8100111','8100112']
BUCKET = 'percolata-data'
DATE_TIME = '2015-12-14'
curr_start = 16*4
next_end = 3*4
ROUTERS = ['2c:5d:93:3b:40:59', 'f2:14:24:07:bf:90', 'f0:99:bf:07:24:14', '2c:5d:93:3b:40:58', 'c0:a0:bb:c5:61:56']
SSID_MAP = {'PPS Guest Network':'f2:14:24:07:bf:90','BaySensors':'c0:a0:bb:c5:61:56','Percolata':'2c:5d:93:3b:40:58',\
            'PPS Network':'f0:99:bf:07:24:14','Field Architecture':'0e:18:d6:53:bf:90'}
RESULT_CSV = 'result.csv'
KNN = get_model()

def download_data():
    download_csv(LOCATION_ID,placements,DATE_TIME,BUCKET,curr_start,next_end,LOCAL_DIR,REMOTE_DIR)

def generate_csv():
    # mac_sn_dict : { (mac_address,time_accurate_to_10_seconds):[signal_strength according to the routers] }
    mac_sn_dict = {}
    fl = os.listdir(LOCAL_DIR+str(LOCATION_ID)+'/'+DATE_TIME+'/')
    ROUTERS_NUM = len(ROUTERS)
    for f in fl:
        try:
            with gzip.open(LOCAL_DIR+str(LOCATION_ID)+'/'+DATE_TIME+'/'+f,'rb') as fp:
                reader = csv.reader(fp)
                for row in reader:
                    # jump first row
                    if reader.line_num ==1:
                        continue
                    # process each ros
                    mac = str(row[3]).lower()
                    ssid = str(row[7])
                    router_bssid = str(row[5]).lower()
                    time = int(row[0])/10*10
                    sn = int (row[6])
                    if router_bssid in ROUTERS:
                        index = ROUTERS.index(router_bssid)
                        tmp_key = (mac,time)
                        if tmp_key not in mac_sn_dict:
                            mac_sn_dict[tmp_key] = [-100 ] * ROUTERS_NUM
                        mac_sn_dict[tmp_key][index] = sn
                    elif ssid in SSID_MAP:
                        tmp_bssid = SSID_MAP[ssid]
                        index = ROUTERS.index(tmp_bssid)
                        tmp_key = (mac,time)
                        if tmp_key not in mac_sn_dict:
                            mac_sn_dict[tmp_key] = [-100 ] * ROUTERS_NUM
                        mac_sn_dict[tmp_key][index] = sn
        except Exception as e:
            print e
            print f
    fout = open(RESULT_CSV,'w')
    writer = csv.writer(fout)
    writer.writerow(['mac','time']+ROUTERS+['zone'])
    for key in mac_sn_dict:
        mac = key[0]
        time = datetime.datetime.utcfromtimestamp(key[1]+8*60*60) # transfer to local time
        x_data = numpy.array([map(int,mac_sn_dict[key])])
        predict_result = number_to_char(KNN.predict(x_data)[0])
        writer.writerow([mac,time]+mac_sn_dict[key]+[predict_result])

if __name__=='__main__':
    local_save_dir = LOCAL_DIR+str(LOCATION_ID)+'/'+DATE_TIME+'/'
    if not os.path.exists(local_save_dir):
        os.makedirs(local_save_dir)
    #download_data()
    generate_csv()






