import math

import glm

from .entity import Entity

class Tracer(Entity):
    def __init__(self, base_obj, pos, rotation):
        super().__init__(base_obj, pos=pos, rotation=rotation)

        self.scale.x *= 0.2
        self.scale.y *= 0.2

        self.speed = 120
        self.velocity = (glm.mat4(rotation) * glm.vec3(0.0, 0.0, -1.0)) * self.speed

        self.step_spacing = 0.1 # 10cm per physics check
        self.range = 10 # 10m maximum range
        self.travel_distance = 0

    def physics_check(self):
        if self.e['World'].check_block(self.pos):
            return True
        
    def destroy(self, collision=False):
        pass
    
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