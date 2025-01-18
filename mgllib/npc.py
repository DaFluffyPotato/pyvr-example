import time
import math
import random
import threading

import glm

from .elements import Element
from .mat3d import prep_mat
from .world.const import BLOCK_SCALE, MaxDepthReached
from .shapes.cuboid import FloorCuboid, CornerCuboid, NO_COLLISIONS
from .shapes.sphere import Sphere
from .shapes.cylinder import FloorCylinder
from .const import BULLET_STATS
from .spark import Spark
from .vritem import M4
from .util import angle_diff

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

class NPCAI(Element):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        self.local_weapon_offset = glm.vec3(0.22, 0.0, -0.55)
        self.global_weapon_offset = glm.vec3(0.0, 1.4, 0.0)
        self.weapon = M4(self.e['Demo'].m4_res, glm.vec3(self.parent.pos))

        self.targeting = None
        self.target_timer = 0
        self.target_duration = 0
        self.attack_cooldown = 0

        self.movement_target_blocks = None
        self.current_path = []
        self.movement_angle = 0

        self.pathing_delay = random.random() * 10
        if time.time() - self.e['Demo'].start_time < 5:
            self.pathing_delay += 16
        self.generating_path = False

    def calculate_weapon_pos(self):
        return (self.parent.rotation * self.local_weapon_offset) + self.global_weapon_offset + self.parent.pos
    
    def alert_rate(self, pos):
        offset = pos - self.parent.pos
        angle = math.atan2(offset.x, offset.z) + math.pi
        in_visible_angle = angle_diff(angle, self.parent.last_xz_angle) < math.pi / 3
        visible_range = 5
        if in_visible_angle:
            visible_range = 15
        if glm.length(offset) < visible_range:
            return 1
        return 0
    
    def gen_path(self, start, end):
        try:
            new_path = self.e['World'].pathfinder.astar(start, end)
            if not new_path:
                self.current_path = []
            else:
                self.current_path = [start] + list(new_path)
        except MaxDepthReached:
            # it took over 200 steps with no path found
            self.current_path = []
        self.movement_target_blocks = (start, end)
        self.generating_path = False

    def update(self):
        movement = glm.vec3(0)
        if self.weapon:
            self.weapon.core_update()

            self.pathing_delay = max(0, self.pathing_delay - self.e['XRWindow'].dt)

            player = self.e['Demo'].player
            alert_rate = self.alert_rate(glm.vec3(player.world_pos.pos))
            if not self.targeting:
                if alert_rate:
                    self.target_timer += alert_rate * self.e['XRWindow'].dt
                    if self.target_timer > 1.7:
                        self.targeting = player
                else:
                    self.target_timer = 0
                    self.targeting = None
            elif not alert_rate:
                self.target_timer = 0
                self.targeting = None

            if self.targeting:
                target_coord = glm.vec3(self.targeting.world_pos.pos) + glm.vec3(0.0, self.targeting.height * 0.7, 0.0)
                target_offset = target_coord - self.parent.pos
            else:
                player_block = player.pathing_pos
                bp = self.parent.pathing_pos
                if player_block and bp and (not self.pathing_delay):
                    if (bp, player_block) != self.movement_target_blocks:
                        if not self.generating_path:
                            self.generating_path = True
                            threading.Thread(target=self.gen_path, args=(bp, player_block)).start()
                
                path_angle = None
                if len(self.current_path) and bp:
                    if self.current_path[0] == bp:
                        self.current_path.pop(0)
                    if len(self.current_path):
                        path_offset = glm.vec3(self.current_path[0]) * BLOCK_SCALE + glm.vec3(BLOCK_SCALE * 0.5) - self.parent.pos
                        if self.current_path[0][1] > bp[1]:
                            self.parent.jump()
                        path_angle = math.atan2(path_offset.x, path_offset.z)
                        ad = angle_diff(path_angle, self.movement_angle)
                        self.movement_angle += max(-self.e['XRWindow'].dt * 2, min(self.e['XRWindow'].dt * 2, ad))
                        movement.x = math.sin(self.movement_angle)
                        movement.z = math.cos(self.movement_angle)

                if path_angle != None:
                    # aim along pathfinding path if the player is not close enough
                    target_coord = self.global_weapon_offset + movement * 15 + self.parent.pos
                else:
                    # default to forward if there is no path movement
                    target_coord = self.global_weapon_offset + (self.parent.rotation * glm.vec3(0.0, 0.0, -15.0)) + self.parent.pos
                target_offset = target_coord - self.parent.pos

            self.parent.last_xz_angle = math.atan2(target_offset.x, target_offset.z) + math.pi
            self.parent.rotation = glm.quat(glm.rotate(self.parent.last_xz_angle, (0, 1, 0)))

            self.weapon.pos = self.calculate_weapon_pos()
            self.weapon.lookat(target_coord)
            self.weapon.calculate_transform()

            if self.targeting:
                self.attack_cooldown = max(0, self.attack_cooldown - self.e['XRWindow'].dt)
                self.target_duration += self.e['XRWindow'].dt
                if (self.target_duration > 0.5) and (self.attack_cooldown <= 0):
                    self.weapon.force_reload()
                    if self.weapon.attempt_fire():
                        if random.random() < 0.25:
                            self.attack_cooldown = random.random() * 0.75 + 0.5
            else:
                self.target_duration = 0
            
        return movement

    def render(self, camera, uniforms={}):
        if self.weapon:
            self.weapon.render(camera, uniforms=uniforms)

class NPC(Element):
    def __init__(self, pos, mode='ai'):
        super().__init__()

        self.mode = mode

        self.scale = glm.vec3(1.0, 1.0, 1.0)
        self.pos = glm.vec3(pos) if pos else glm.vec3(0.0, 0.0, 0.0)
        self.last_xz_angle = random.random() * math.pi * 2
        self.rotation = glm.quat(glm.rotate(self.last_xz_angle, (0, 1, 0)))

        self.brain = None
        if mode == 'ai':
            self.brain = NPCAI(self)

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
        self.jump_force = 4.25
        self.air_time = 0
        self.movement_speed = 2.5

        self.pathing_pos = None

    def jump(self):
        if self.air_time < 0.25:
            self.velocity.y = self.jump_force
            self.air_time = 1

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
        
    def kill(self, score=True):
        if not self.killed:
            if score:
                self.e['Demo'].score += 1
                
            self.e['Sounds'].play('kill_confirmed', volume=0.5)

            for i in range(30):
                self.body_fragment(self.body.hitbox.random_point())
            for i in range(14):
                self.body_fragment(self.head.hitbox.random_point())
            self.killed = 0.1
        
    def damage(self, bullet_type, part, bullet=None):
        stats = BULLET_STATS[bullet_type]

        if part == 'head':
            if self.helmeted:
                self.helmet_health -= stats['helmet_dmg']
                if self.helmet_health <= 0:
                    self.helmeted = False
                self.health -= (self.health * 0.7 + self.max_health * 0.3) * stats['helmet_pen']
                if self.health > 0:
                    self.e['Sounds'].play('helmet', volume=0.7)
                else:
                    self.e['Sounds'].play('headshot')
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
            brain_movement = glm.vec3(0)
            if self.brain:
                brain_movement = self.brain.update()

            movement_vec = glm.vec3(0, 0, 0)

            self.velocity.y = max(-self.terminal_velocity, self.velocity.y - self.gravity * self.e['XRWindow'].dt)

            movement_vec.x += self.velocity.x * self.e['XRWindow'].dt
            movement_vec.y += self.velocity.y * self.e['XRWindow'].dt
            movement_vec.z += self.velocity.z * self.e['XRWindow'].dt
            movement_vec += brain_movement * self.movement_speed * self.e['XRWindow'].dt

            self.move(list(movement_vec))

            self.pathing_pos = self.e['World'].find_valid_path_destination(self.e['World'].world_to_block(self.pos))

            if self.last_collisions['bottom']:
                self.velocity.y = 0
                self.air_time = 0
            else:
                self.air_time += self.e['XRWindow'].dt

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

        if not self.killed:
            self.brain.render(camera, uniforms=uniforms)