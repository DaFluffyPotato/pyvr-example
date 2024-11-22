import glm

class Sphere:
    pass

def sphere_collide(p1, p2, radius):
    return glm.length(p2 - p1) < radius