import math
import random

import glm

class FloorCylinder:
    def __init__(self, pos, height, radius):
        self.pos = glm.vec3(pos)

        self.xz_pos = glm.vec2(self.pos.x, self.pos.z)

        self.height = height
        self.radius = radius

    def collidepoint(self, point):
        if self.pos.y <= point.y <= self.pos.y + self.height:
            if glm.length(self.xz_pos - glm.vec2(point.x, point.z)) <= self.radius:
                return True
        return False
    
    def random_point(self):
        radius = random.random() * self.radius
        angle = random.random() * math.pi * 2
        return glm.vec3(math.cos(angle) * radius + self.pos.x, self.pos.y + random.random() * self.height, math.sin(angle) * radius + self.pos.z)