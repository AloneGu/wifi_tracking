import numpy as np
from sklearn.neighbors import KNeighborsClassifier

bssid_list = ['6c:72:20:11:12:60','74:d0:2b:5d:40:0a','00:0f:13:39:21:25']
TRAINING_DATA = 'bssidlist.txt'

def char_to_number(char):
    # A is 1
    return ord(str(char))-64

def number_to_char(number):
    # 1 is A
    return chr(int(number)+64)

def parse_txt():
    f = open(TRAINING_DATA)
    content = f.readlines()
    x_data,y_data=[],[]
    for row in content:
        first_colon_index = row.find(':')
        place = row[:first_colon_index]
        data = eval(row[first_colon_index+1:])
        
        for k in data.keys():
            if k not in bssid_list:
                del(data[k])
        for bssid in bssid_list:
            if bssid not in data:
                data[bssid]='-90'
                
        print place,data
        y_data.append(char_to_number(place))
        tmp_x_data = [int(data[bssid]) for bssid in bssid_list]
        x_data.append(tmp_x_data)

    x_data = np.array(x_data)
    y_data = np.array(y_data)
    return x_data,y_data

def train_data():
    x_data,y_data = parse_txt()

    knn = KNeighborsClassifier()

    indices = np.random.permutation(len(x_data))
    print indices
    x_train = x_data[indices[:-10]]
    y_train = y_data[indices[:-10]]
    x_test  = x_data[indices[-10:]]
    y_test  = y_data[indices[-10:]]
    knn.fit(x_train[:-5], y_train[:-5])
    
    print 'test'
    test_result = knn.predict(x_test)
    print 'predict result',
    print test_result,
    print [number_to_char(x) for x in test_result]
    print 'ground_truth',
    print y_test,
    print [number_to_char(x) for x in y_test]

train_data()