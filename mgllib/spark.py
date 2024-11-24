import math
import random

import glm

from .model.polygon import PolygonOBJ

class Spark(PolygonOBJ):
    def __init__(self, shape, pos, rotation, speed=1.0, spread=0.0, scale=(0.5, 0.2), decay=0.3, color=(1.0, 1.0, 1.0)):
        if len(color) == 3:
            color = tuple([*color, 1.0])

        scale = glm.vec2(scale)

        z_rot = glm.rotate(random.random() * math.pi * 2, (0, 0, 1))
        x_rot = glm.rotate((random.random() - 0.5) * spread, (1, 0, 0))
        y_rot = glm.rotate((random.random() - 0.5) * spread, (0, 1, 0))

        rotation = glm.quat(glm.mat4(rotation) * (y_rot * x_rot * z_rot))

        super().__init__(shape, pos=pos, rotation=rotation)

        self.scale = glm.vec3(scale.y, scale.y, scale.x)

        self.decay = decay
        self.color = color
        self.speed = speed
        self.velocity = glm.mat4(self.rotation) * glm.vec3(0.0, 0.0, -self.speed)

        self.calculate_transform()

    def update(self):
        dt = self.e['XRWindow'].dt

        self.scale.x = max(0, self.scale.x - self.decay * dt)
        self.scale.y = max(0, self.scale.y - self.decay * dt)
        self.scale.z = max(0, self.scale.z - self.decay * dt * 0.5)

        self.pos += self.velocity * dt

        if not (self.scale.x and self.scale.y):
            return True
        
        super().update()

    def render(self, camera, uniforms={}):
        uniforms['color'] = tuple(self.color)
        super().render(camera, uniforms=uniforms)