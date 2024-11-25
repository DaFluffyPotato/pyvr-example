import glm

class Sphere:
    def __init__(self, pos, radius):
        self.pos = glm.vec3(pos)
        self.radius = radius
    
    def collidepoint(self, point):
        return glm.length(self.pos - point) <= self.radius

def sphere_collide(p1, p2, radius):
    return glm.length(p2 - p1) < radius