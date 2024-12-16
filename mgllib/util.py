import math

def read_f(path):
    f = open(path, 'r')
    data = f.read()
    f.close()
    return data

def angle_diff(angle_1, angle_2):
    return ((angle_1 - angle_2) + math.pi) % (math.pi * 2) - math.pi

def angle_pull_within(angle, ref_angle, angle_range):
    diff = angle_diff(ref_angle, angle)
    if abs(diff) > angle_range:
        scale = (abs(diff) - angle_range) / abs(diff)
        angle += diff * scale
    return angle