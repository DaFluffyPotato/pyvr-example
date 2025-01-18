import math

import numpy as np
import glm

from .xrinput import Controller
from .mat3d import Transform3D, quat_to_mat
from .shapes.cuboid import FloorCuboid, CornerCuboid, NO_COLLISIONS
from .shapes.sphere import Sphere
from .shapes.cylinder import FloorCylinder
from .world.const import BLOCK_SCALE
from .elements import ElementSingleton, Element
from .vritem import Magazine, Gun
from .watch import Watch
from .util import angle_pull_within
from .const import BULLET_STATS

'''
Headset + Virtual Body Transform Model

Overview: x/z stripped irl transform -> body transform -> camera transform

Take in headset pos/rot, strip x/z pos and compute movement since last update.
Take in hand pos/rot. Update hand x/z to just be offset from headset.

Compute world hand position as [body_mat4] * [hand_vec4]. (note that the hand is already adjusted above)
Compute world hand aim vector as [body_mat4] * [hand_aim_vec4].
Compute movement based on [body_mat4] * [world_hand_aim_vec4].

Apply snap-turn to body matrix.
Apply headset movement as body motion.

Assign camera world matrix as the inverse of the body matrix.
'''

class InventorySlot(Element):
    def __init__(self, origin=None):
        super().__init__()

        self.holding = None
        self.origin = glm.vec3(origin) if origin else glm.vec3(0, 0, 0)
        self.pos = glm.vec3(0, 0, 0)
        self.rot = glm.quat()

    def attach(self, item):
        if self.holding:
            self.holding.in_slot = None

        self.holding = item
        item.in_slot = self
    
    def take(self):
        item = self.holding
        if self.holding:
            self.holding.in_slot = None
        self.holding = None
        return item

    def transform(self, pos_transform, rotation):
        # translate
        self.pos = glm.vec3(glm.rotate(rotation, glm.vec3(0, 1, 0)) * glm.vec3(self.origin) + pos_transform.pos)

        # rotate
        self.rot = glm.quat(glm.rotate(rotation, glm.vec3(0, 1, 0)))

class PlayerBody(ElementSingleton):
    def __init__(self):
        super().__init__()

        self.world_pos = Transform3D()

        # OpenXR docs indicate that +Y is up, +X is right, and -Z is forward
        self.world_movement = glm.vec3(0.0, 0.0, 0.0)

        self.hands = [Controller(0), Controller(1)]
        for hand in self.hands:
            hand.parent = self
        self.hands[0].other = self.hands[1]
        self.hands[1].other = self.hands[0]

        self.snap_direction = 0
        self.snap_val = 0

        self.movement_speed = 4

        # funny minecraft dimensions
        self.size = [0.6 * BLOCK_SCALE, 1.8, 0.6 * BLOCK_SCALE]

        self.cuboid = FloorCuboid(self.world_pos.pos, self.size)

        self.last_collisions = NO_COLLISIONS.copy()

        self.gravity = 9.81 # m/s^2
        self.velocity = glm.vec3(0.0, 0.0, 0.0)
        self.terminal_velocity = 19
        self.air_time = 0
        self.jump_force = 4.25

        self.xz_angle = 0
        self.xz_slack = 1.0
        self.xz_angle_slacked = 0

        self.inventory = {'left_hip_mag': InventorySlot(), 'right_hip_mag': InventorySlot()}

        self.height = 2
        self.eye_height = 1.85

        self.helmeted = True
        self.max_health = 100
        self.health = self.max_health
        self.helmet_health = 1.0
        self.watch = Watch(self)
        
        self.pathing_pos = None

        self.calculate_hitboxes()

    def calculate_hitboxes(self):
        self.head_hitbox = Sphere(glm.vec3(self.world_pos.pos) + glm.vec3(0, self.eye_height, 0), 0.2)
        self.body_hitbox = FloorCylinder(glm.vec3(self.world_pos.pos), self.eye_height - 0.15, 0.25)
    
    def move(self, movement):
        blockers = [CornerCuboid(block.scaled_world_pos, (block.scale, block.scale, block.scale)) for block in self.e['World'].nearby_blocks(self.cuboid.origin, radii=(1, 3, 1))]
        self.last_collisions = self.cuboid.move(movement, blockers)
        self.world_pos.pos = list(self.cuboid.origin)

    def hit_check(self, point):
        if self.health > 0:
            if self.head_hitbox.collidepoint(point):
                return 'head'
            if self.body_hitbox.collidepoint(point):
                return 'body'
            
    def kill(self):
        for npc in self.e['Demo'].npcs:
            npc.kill(score=False)

        self.world_pos.pos = [0, 10, 0]
        self.cuboid.origin = list(self.world_pos.pos)
        self.health = self.max_health
        self.e['Demo'].score = 0

    def damage(self, bullet_type, part, bullet=None):
        stats = BULLET_STATS[bullet_type]

        sound_location = self.e['Sounds'].head_pos
        if bullet:
            sound_location = self.e['Sounds'].head_pos - glm.normalize(bullet.velocity)

        if part == 'head':
            if self.helmeted:
                self.helmet_health -= stats['helmet_dmg']
                if self.helmet_health <= 0:
                    self.helmeted = False
                self.health -= (self.health * 0.7 + self.max_health * 0.3) * stats['helmet_pen']
                if self.health > 0:
                    self.e['Sounds'].play_from('helmet', volume=0.7, position=sound_location)
                else:
                    self.e['Sounds'].play_from('headshot', position=sound_location)
            else:
                self.health = 0
                self.e['Sounds'].play_from('headshot', position=sound_location)
        else:
            self.health -= stats['damage']
            self.e['Sounds'].play_from('hurt', position=sound_location)

        self.e['HUD'].flash()
        
        if self.health <= 0:
            self.kill()

    @property
    def left_hand(self):
        return self.hands[0]
    
    @property
    def right_hand(self):
        return self.hands[1]

    def cycle(self):
        for hand in self.hands:
            hand.log_state()

        self.e['XRInput'].left_hand.copy_to(self.left_hand)
        self.e['XRInput'].right_hand.copy_to(self.right_hand)

        # hand_orientation.dot(forward_vector) -> remove y component (project to x/z) -> atan2 -> offset by joystick angle -> cos/sin back to vector -> move player
        movement_scale = np.linalg.norm(self.e['XRInput'].left_stick)

        movement_vec = glm.vec3(0, 0, 0)

        if movement_scale:
            # -1z 0x should be 0 degrees, so use inverted z as y input for atan
            projected_forward_angle = math.atan2(self.e['XRInput'].left_hand.aim_vector[2], self.e['XRInput'].left_hand.aim_vector[0])
            projected_forward_angle += math.atan2(self.e['XRInput'].left_stick[0], self.e['XRInput'].left_stick[1])
            stick_movement_vector = np.array([math.cos(projected_forward_angle), math.sin(projected_forward_angle)])

            movement_vec.x += self.e['XRWindow'].dt * stick_movement_vector[0] * movement_scale * self.movement_speed
            movement_vec.z += self.e['XRWindow'].dt * stick_movement_vector[1] * movement_scale * self.movement_speed

        snap_val = self.e['XRInput'].right_stick[0] / abs(self.e['XRInput'].right_stick[0]) if (abs(self.e['XRInput'].right_stick[0]) > 0.7) else 0
        if snap_val and not self.snap_val:
            self.snap_direction = self.snap_val
            self.world_pos.rotation[1] += -0.5 * snap_val
        else:
            self.snap_direction = 0
        self.snap_val = snap_val

        self.xz_angle = self.world_pos.rotation[1] + self.e['XRState'].xz_angle
        self.xz_angle_slacked = angle_pull_within(self.xz_angle_slacked, self.xz_angle, self.xz_slack)

        self.velocity.y = max(-self.terminal_velocity, self.velocity.y - self.gravity * self.e['XRWindow'].dt)

        if self.right_hand.pressed_lower and (self.air_time < 0.25):
            self.velocity.y = self.jump_force

        movement_vec.x += self.e['XRInput'].head_movement[0] + self.velocity.x * self.e['XRWindow'].dt
        movement_vec.y += self.velocity.y * self.e['XRWindow'].dt
        movement_vec.z += self.e['XRInput'].head_movement[2] + self.velocity.z * self.e['XRWindow'].dt
        # all movement at this point is from the perspective of the headset, so the player world rotation needs to be applied
        self.world_movement = self.world_pos.rotation_matrix * movement_vec

        self.move(list(self.world_movement))

        self.pathing_pos = self.e['World'].find_valid_path_destination(self.e['World'].world_to_block(self.world_pos.pos))

        if self.last_collisions['bottom']:
            self.velocity.y = 0
            self.air_time = 0
        else:
            self.air_time += self.e['XRWindow'].dt

        if self.last_collisions['top']:
            self.velocity.y = 0

        self.left_hand.transform(self.world_pos)
        self.right_hand.transform(self.world_pos)

        # average distance from eyes to top of head is ~15cm
        self.height = self.e['XRInput'].raw_head_pos[1] + 0.15
        self.eye_height = self.e['XRInput'].raw_head_pos[1]

        self.calculate_hitboxes()

        self.inventory['left_hip_mag'].origin = glm.vec3(-0.25, self.e['XRInput'].raw_head_pos[1] * 0.54, 0)
        self.inventory['right_hip_mag'].origin = glm.vec3(0.25, self.e['XRInput'].raw_head_pos[1] * 0.54, 0)
        for slot in self.inventory:
            self.inventory[slot].transform(self.world_pos, self.xz_angle_slacked)

        holding_weapon = None
        if self.right_hand.interacting and self.right_hand.interacting.parent:
            if issubclass(self.right_hand.interacting.parent.__class__, Gun):
                holding_weapon = self.right_hand.interacting.parent
        elif self.left_hand.interacting and self.left_hand.interacting.parent:
            if issubclass(self.left_hand.interacting.parent.__class__, Gun):
                holding_weapon = self.left_hand.interacting.parent
        if holding_weapon:
            if not (self.inventory['left_hip_mag'].holding):
                new_mag = Magazine(holding_weapon)
                self.inventory['left_hip_mag'].attach(new_mag)
                self.e['Demo'].items.append(new_mag)
            if not (self.inventory['right_hip_mag'].holding):
                new_mag = Magazine(holding_weapon)
                self.inventory['right_hip_mag'].attach(new_mag)
                self.e['Demo'].items.append(new_mag)
        else:
            if self.inventory['left_hip_mag'].holding:
                mag = self.inventory['left_hip_mag'].take()
                if mag in self.e['Demo'].items:
                    self.e['Demo'].items.remove(mag)
            if self.inventory['right_hip_mag'].holding:
                mag = self.inventory['right_hip_mag'].take()
                if mag in self.e['Demo'].items:
                    self.e['Demo'].items.remove(mag)

        self.e['XRCamera'].world_rotation = list(self.world_pos.rotation)
        self.e['XRCamera'].world_matrix = np.linalg.inv(self.world_pos.npmatrix)

        self.e['Sounds'].place_listener(glm.vec3(self.world_pos.pos) + glm.vec3(0, self.e['XRInput'].raw_head_pos[1], 0), self.world_pos.rotation_matrix * glm.mat4(self.e['XRInput'].raw_head_orientation))

    def late_cycle(self):
        self.watch.update()

    def render(self, camera):
        self.watch.render(camera)