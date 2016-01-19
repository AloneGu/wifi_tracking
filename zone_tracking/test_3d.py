from wifi_tracking_training import parse_txt
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

color_new_map = {1: 'r', 2: 'g', 3: 'b', 4: 'y', 5: 'k', 6: 'w'}


def test_draw():
    x_data, y_data, _, _ = parse_txt()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    data_cnt = len(x_data)
    x = []
    y = []
    z = []
    colors = []

    for i in range(data_cnt):
        item = x_data[i]
        x.append(-item[0])
        y.append(-item[1])
        z.append(-item[2])
        colors.append(color_new_map[y_data[i]])
    ax.scatter(x, y, z, c=colors, marker='o')

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.show()


if __name__ == '__main__':
    test_draw()
