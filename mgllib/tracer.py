import math
import random

import glm

from .entity import Entity
from .spark import Spark

class Tracer(Entity):
    def __init__(self, base_obj, bullet_type, pos, rotation):
        super().__init__(base_obj, pos=pos, rotation=rotation)

        self.type = bullet_type

        self.scale.x *= 0.2
        self.scale.y *= 0.2

        self.speed = 120
        self.velocity = (glm.mat4(rotation) * glm.vec3(0.0, 0.0, -1.0)) * self.speed

        self.step_spacing = 0.1 # 10cm per physics check
        self.range = 100 # 10m maximum range
        self.travel_distance = 0

        self.create_sparks(4)

    def create_blood(self, count):
        rotation = glm.quat(glm.mat4(self.rotation) * glm.rotate(math.pi, (0, 1, 0)))

        for i in range(count):
            self.e['Demo'].particles.append(Spark(self.e['Demo'].spark_res, self.pos, rotation, speed=random.random() + 1, spread=1.1, scale=(0.2, 0.16), decay=0.4 + random.random() * 0.2, color=(1.0, 0.0, 0.267)))

    def create_sparks(self, count, backwards=False):
        rotation = self.rotation
        if backwards:
            rotation = glm.quat(glm.mat4(self.rotation) * glm.rotate(math.pi, (0, 1, 0)))

        for i in range(count):
            self.e['Demo'].particles.append(Spark(self.e['Demo'].spark_res, self.pos, rotation, speed=5, spread=0.7, scale=(0.2, 0.05), decay=0.6, color=(1.0, 1.0, 1.0)))

    def physics_check(self):
        for npc in self.e['Demo'].npcs:
            hit = npc.hit_check(self.pos)
            if hit:
                npc.damage(self.type, hit)
                self.create_blood(6)
                return True
            
        if self.e['World'].check_block(self.pos):
            self.e['Sounds'].play_from('bullet_collide', position=self.pos)
            return True
        
    def destroy(self, collision=False):
        if collision:
            self.create_sparks(8, backwards=True)
        else:
            self.create_sparks(4)
    
    def update(self):
        current_speed = glm.length(self.velocity)

        movement_steps = math.ceil((current_speed * self.e['XRWindow'].dt) * (1 / self.step_spacing))
        for step in range(movement_steps):
            step_amount = (self.e['XRWindow'].dt * (1 / movement_steps))
            self.travel_distance += current_speed * step_amount
            self.pos += self.velocity * step_amount

            if self.physics_check():
                self.destroy(collision=True)
                return True
            
            if self.travel_distance >= self.range:
                self.destroy()
                return True

        self.calculate_transform()