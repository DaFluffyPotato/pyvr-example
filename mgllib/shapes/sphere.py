import math
import random

import glm

class Sphere:
    def __init__(self, pos, radius):
        self.pos = glm.vec3(pos)
        self.radius = radius
    
    def collidepoint(self, point):
        return glm.length(self.pos - point) <= self.radius
    
    def random_point(self):
        xz_angle = random.random() * math.pi * 2
        y_angle = random.random() * math.pi * 2
        radius = random.random() * self.radius

        return glm.vec3(math.cos(xz_angle) * radius * math.cos(y_angle), math.sin(y_angle) * radius, math.sin(xz_angle) * radius * math.cos(y_angle)) + self.pos

def sphere_collide(p1, p2, radius):
    return glm.length(p2 - p1) < radius