import os
import operator
import datetime
import gzip
import csv
import re

LOCAL_DIR = './data/'
REMOTE_DIR = 'data/combined/wifi/'
LOCATION_ID = '39'
DATE_TIME = '2015-12-14'

def find_one_mac(target_mac):
    result = []
    fl = os.listdir(LOCAL_DIR+str(LOCATION_ID)+'/'+DATE_TIME+'/')
    for f in fl:
        with gzip.open(LOCAL_DIR+str(LOCATION_ID)+'/'+DATE_TIME+'/'+f,'rb') as fp:
            placement = re.findall("\d{7}",f)[0]
            reader = csv.reader(fp)
            for row in reader:
                if reader.line_num ==1:
                    continue
                mac = str(row[3]).lower()
                row[0] = datetime.datetime.utcfromtimestamp(int(row[0])-8*60*60) # transfer to local time
                if mac == target_mac:
                    result.append(row+[placement])
    #print result
    print target_mac,'packages',len(result),' on ',DATE_TIME
    result = sorted(result,key=lambda x:x[0])
    for row in result:
        print row

if __name__=='__main__':
    import sys
    find_one_mac(sys.argv[1])