import math
import random

import glm

from .elements import Element
from .mat3d import prep_mat
from .world.const import BLOCK_SCALE
from .shapes.cuboid import FloorCuboid, CornerCuboid, NO_COLLISIONS
from .shapes.sphere import Sphere
from .shapes.cylinder import FloorCylinder
from .const import BULLET_STATS
from .spark import Spark

class NPCPart(Element):
    def __init__(self, parent, model, part_type):
        self.parent = parent

        self.model = model
        self.type = part_type

        self.hitbox = Sphere(glm.vec3(0.0), 0)
        self.transform = glm.mat4()

    def calculate_transform(self):
        if self.type == 'head':
            self.transform = glm.translate(glm.vec3(0.0, 1.65, 0.0)) * glm.scale(glm.vec3(0.2))
            self.hitbox = Sphere(self.parent.transform * self.transform * glm.vec3(0.0), 0.2)
        elif self.type == 'body':
            self.transform = glm.translate(glm.vec3(0.0, 0.8, 0.0)) * glm.scale(glm.vec3(0.6))
            self.hitbox = FloorCylinder(self.parent.transform * glm.vec3(0.0), 1.5, 0.25)
        elif self.type == 'helmet':
            self.transform = glm.translate(glm.vec3(0.0, 1.68, 0.0)) * glm.scale(glm.vec3(0.24))
        else:
            self.transform = glm.mat4()

class NPC(Element):
    def __init__(self, pos):
        super().__init__()

        self.scale = glm.vec3(1.0, 1.0, 1.0)
        self.pos = glm.vec3(pos) if pos else glm.vec3(0.0, 0.0, 0.0)
        self.rotation = glm.quat(glm.rotate(random.random() * math.pi * 2, (0, 1, 0)))

        self.killed = 0
        self.helmeted = True
        self.max_health = 100
        self.health = self.max_health
        self.helmet_health = 1.0

        self.head = NPCPart(self, self.e['Demo'].head_res, 'head')
        self.helmet = NPCPart(self, self.e['Demo'].helmet_res, 'helmet')
        self.body = NPCPart(self, self.e['Demo'].body_res, 'body')

        self.physics_size = [0.6 * BLOCK_SCALE, 1.8, 0.6 * BLOCK_SCALE]
        self.cuboid = FloorCuboid(self.pos, self.physics_size)

        self.calculate_transform()

        self.last_collisions = NO_COLLISIONS.copy()

        self.gravity = 9.81 # m/s^2
        self.velocity = glm.vec3(0.0, 0.0, 0.0)
        self.terminal_velocity = 19

    def hit_check(self, point):
        if not self.killed:
            if self.head.hitbox.collidepoint(point):
                return 'head'
            if self.body.hitbox.collidepoint(point):
                return 'body'
            
    def body_fragment(self, source):
        rotation = glm.quat(glm.rotate(random.random() * math.pi * 2, (1, 0, 0)) * glm.rotate(random.random() * math.pi * 2, (0, 1, 0)) * glm.rotate(random.random() * math.pi * 2, (0, 0, 1)))
        colors = [(1.0, 0.0, 0.267), (0.635, 0.149, 0.2), (0.149, 0.169, 0.267)]
        self.e['Demo'].particles.append(Spark(self.e['Demo'].spark_res, source, rotation, speed=1.5 + random.random() * 3, spread=0, scale=(0.15 + random.random() * 0.08, 0.15 + random.random() * 0.16), decay=0.35 + random.random() * 0.25, color=random.choice(colors), accel=glm.vec3(0, -self.gravity * (0.5 + random.random() * 0.5), 0), drag=3))
        
    def kill(self):
        if not self.killed:
            self.e['Sounds'].play('kill_confirmed', volume=0.5)

            for i in range(30):
                self.body_fragment(self.body.hitbox.random_point())
            for i in range(14):
                self.body_fragment(self.head.hitbox.random_point())
            self.killed = 0.1
        
    def damage(self, bullet_type, part):
        stats = BULLET_STATS[bullet_type]

        if part == 'head':
            if self.helmeted:
                self.helmet_health -= stats['helmet_dmg']
                if self.helmet_health <= 0:
                    self.helmeted = False
                self.health -= (self.health * 0.7 + self.max_health * 0.3) * stats['helmet_pen']
                self.e['Sounds'].play('helmet', volume=0.7)
            else:
                self.health = 0
                self.e['Sounds'].play('headshot')
        else:
            self.health -= stats['damage']
            self.e['Sounds'].play('hurt')
        
        if self.health <= 0:
            self.kill()
    
    def move(self, movement):
        blockers = [CornerCuboid(block.scaled_world_pos, (block.scale, block.scale, block.scale)) for block in self.e['World'].nearby_blocks(self.cuboid.origin, radii=(1, 3, 1))]
        self.last_collisions = self.cuboid.move(movement, blockers)
        self.pos = list(self.cuboid.origin)

    def update(self):
        if not self.killed:
            movement_vec = glm.vec3(0, 0, 0)

            self.velocity.y = max(-self.terminal_velocity, self.velocity.y - self.gravity * self.e['XRWindow'].dt)

            movement_vec.x += self.velocity.x * self.e['XRWindow'].dt
            movement_vec.y += self.velocity.y * self.e['XRWindow'].dt
            movement_vec.z += self.velocity.z * self.e['XRWindow'].dt

            self.move(list(movement_vec))

            if self.last_collisions['bottom']:
                self.velocity.y = 0

            if self.last_collisions['top']:
                self.velocity.y = 0

        self.calculate_transform()

        if self.killed:
            self.killed = min(1, self.killed + self.e['XRWindow'].dt)

        return self.killed >= 1.0

    @property
    def parts(self):
        if self.helmeted and (not self.killed):
            return [self.head, self.helmet, self.body]
        return [self.head, self.body]

    def calculate_transform(self):
        scale_mat = glm.scale(self.scale)
        self.transform = glm.translate(self.pos) * glm.mat4(self.rotation) * scale_mat

        for part in self.parts:
            part.calculate_transform()

    def render(self, camera, uniforms={}):
        uniforms['world_light_pos'] = tuple(camera.light_pos)
        uniforms['view_projection'] = camera.prepped_matrix
        uniforms['eye_pos'] = camera.eye_pos
        uniforms['pop'] = self.killed

        for part in self.parts:
            uniforms['world_transform'] = prep_mat(self.transform * part.transform)
            part.model.vao.render(uniforms=uniforms)