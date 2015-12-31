import os
import operator
import gzip
import csv

LOCAL_DIR = './data/'
REMOTE_DIR = 'data/combined/wifi/'
LOCATION_ID = '39'
DATE_TIME = '2015-12-14'

bssid_cnt={}
fl = os.listdir(LOCAL_DIR+str(LOCATION_ID)+'/'+DATE_TIME+'/')
for f in fl:
    with gzip.open(LOCAL_DIR+str(LOCATION_ID)+'/'+DATE_TIME+'/'+f,'rb') as fp:
        reader = csv.reader(fp)
        for row in reader:
            bssid = str(row[5]).lower()
            if bssid not in bssid_cnt:
                bssid_cnt[bssid]=0
            else:
                bssid_cnt[bssid]+=1

sorted_result = sorted(bssid_cnt.items(),key=operator.itemgetter(1))
print 'sort keys',sorted_result
bssid_list = [x[0] for x in sorted_result[-6:]]
print 'bssid_list',bssid_list # use the 5 most common bssid to build the map