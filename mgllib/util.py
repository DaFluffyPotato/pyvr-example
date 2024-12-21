import math
import glm

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

def segment_project_progress(start, end, sample, clamp=True):
    projected = start + glm.dot(sample - start, end - start) / glm.dot(end - start, end - start) * (end - start)
    rel_proj = projected - start
    rel_end = end - start
    progress = glm.length(rel_proj) / glm.length(rel_end)
    epsilon = 0.0001
    # the vectors point in opposite directions if the length of the two vectors combined is less then the individual lengths combined
    if glm.length(rel_proj + rel_end) < glm.length(rel_proj) + glm.length(rel_end) - epsilon:
        progress *= -1
    if clamp:
        progress = max(0, min(1, progress))
    return progress