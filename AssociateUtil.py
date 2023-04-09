import os
import numpy as np
import cv2


def gene_txt(pathResult):

    came1_pic_path = os.path.join(pathResult, "came1")
    came2_pic_path = os.path.join(pathResult, "came2")

    file1 = os.listdir(came1_pic_path)  # list
    file2 = os.listdir(came2_pic_path)  # list

    txt_file1 = open(os.path.join(pathResult, "came1.txt"), mode="w")
    for file1Index in range(len(file1)):
        if file1Index < len(file1) - 1:
            txt_file1.write(file1[file1Index] + "\n")
        else:
            txt_file1.write(file1[file1Index])
    txt_file1.close()

    txt_file2 = open(os.path.join(pathResult, "came2.txt"), mode="w")
    for file2Index in range(len(file2)):
        if file2Index < len(file2) - 1:
            txt_file2.write(file2[file2Index] + "\n")
        else:
            txt_file2.write(file2[file2Index])
    txt_file2.close()


def read_file_dict(txt_file_name):
    file = open(txt_file_name)
    data = file.read()
    lines = data.split("\n")
    lines.pop()                                                                                 # eliminate the last image
    timestamp = [(line.replace("-", "").split(".jpg")[0], line) for line in lines]

    return dict(timestamp)


def associate(first_stamp_dict, second_stamp_dict, max_difference, flag):
    first_keys = list(first_stamp_dict.keys())
    second_keys = list(second_stamp_dict.keys())

    candidate = []
    for value in first_keys:
        second_stamp_array = np.array(second_keys, dtype="float64")
        value_associate = second_keys[(np.abs(second_stamp_array - np.array(value, dtype="float64"))).argmin()]
        subValue = (np.abs(second_stamp_array - np.array(value, dtype="float64"))).min()
        if subValue > max_difference:
            continue
        if not flag:
            candidate.append((first_stamp_dict[value], second_stamp_dict[value_associate]))
        else:
            candidate.append((second_stamp_dict[value_associate], first_stamp_dict[value]))
    return candidate


def gene_video(path_result, out1, out2):
    file = open(os.path.join(path_result, "associate.txt"), mode='r')
    data = file.read()
    lines = data.split("\n")
    lines.pop()
    for line in lines:
        frame1 = cv2.imread(os.path.join(path_result, "came1", line.split(',')[0]))
        frame2 = cv2.imread(os.path.join(path_result, "came2", line.split(',')[1]))
        out1.write(frame1)
        out2.write(frame2)
    file.close()
    out1.release()
    out2.release()


def run_associate(path_result, out1, out2):
    first_list = read_file_dict(os.path.join(path_result, "came1.txt"))
    second_list = read_file_dict(os.path.join(path_result, "came2.txt"))

    if len(first_list) <= len(second_list):
        flag = 0
        matches = associate(first_list, second_list, max_difference=1.0, flag=flag)
    else:
        flag = 1
        matches = associate(second_list, first_list, max_difference=1.0, flag=flag)

    file = open(os.path.join(path_result, "associate.txt"), mode='w')
    for a, b in matches:
        file.write("%s,%s\n" % (a, b))
    file.close()

    # generate the upload video
    gene_video(path_result, out1, out2)
    print("Have generate the associate video")

