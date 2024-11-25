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