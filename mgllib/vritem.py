import math
import random

import glm

from .model.entity3d import Entity3D
from .shapes.cuboid import CornerCuboid
from .shapes.sphere import sphere_collide
from .elements import Element, elems
from .mat3d import prep_mat, quat_scale, vec3_exponent
from .const import HAND_VELOCITY_TIMEFRAME, PHYSICS_EPSILON, RECOIL_PATTERNS, HOVER_COOLDOWN
from .util import segment_project_progress

from .tracer import Tracer

class VRItemComponent(Element):
    def __init__(self):
        super().__init__()

# the two types are grip and interact (grib vs trigger)
class VRItemPoint(Element):
    def __init__(self, point_type, pos, radius=0.3, default=False):
        super().__init__()

        self.parent = None
        self.type = point_type
        self.pos = glm.vec3(pos)
        self.default = default
        self.radius = radius

        self.local_rotation = glm.quat(1.0, 0.0, 0.0, 0.0)

        self.input_rotation = glm.quat(1.0, 0.0, 0.0, 0.0)
        self.input_pos = glm.vec3(0.0, 0.0, 0.0)

        self.interacting = None

        self.hover_vibrate_cooldown = [0, 0]

        self.hand_override = None

    @property
    def scaled_pos(self):
        return self.pos * self.parent.scale

    @property
    def world_pos(self):
        return self.parent.transform * self.pos
    
    def offsetted_world_pos(self, offset):
        return self.parent.transform * (self.pos + offset)
    
    def grab(self, hand):
        if self.type in {'grip', 'trigger_grip', 'grip_interact', 'trigger_interact'}:
            if not (hand.interacting or self.interacting):
                if self.type in {'grip', 'trigger_grip'}:
                    if self.parent.in_slot:
                        self.parent.in_slot.take()
                    
                    self.parent.velocity_reset()
                    self.parent.floor_mode = False
                if (self.type in {'grip_interact', 'trigger_interact'}) and (self.parent.primary_grip):
                    # for now, the interaction points only function when the object is held
                    hand.interacting = self
                    self.interacting = hand

                if self.type in {'grip', 'trigger_grip'}:
                    hand.interacting = self
                    self.interacting = hand
                    
                    # handle grip arrangement
                    if not self.parent.primary_grip:
                        self.parent.primary_grip = self
                    elif self.parent.default_grip == self:
                        # move old primary to alt because this point is the default
                        self.parent.alt_grip = self.parent.primary_grip
                        self.parent.primary_grip = self
                    else:
                        # primary is taken and this isn't the default, so make self the alt grip
                        self.parent.alt_grip = self

                self.parent.e['Sounds'].play_from('grab', position=self.world_pos, volume=0.7)

                hand.vibrate(amplitude=1.0)

    def handle_hover(self, hand):
        if not hand.interacting:
            if not self.hover_vibrate_cooldown[hand.hand]:
                hand.vibrate(amplitude=0.4)
            self.hover_vibrate_cooldown[hand.hand] = HOVER_COOLDOWN
    
    def update(self, hand):
        self.hover_vibrate_cooldown[0] = max(self.hover_vibrate_cooldown[0] - self.e['XRWindow'].dt, 0)
        self.hover_vibrate_cooldown[1] = max(self.hover_vibrate_cooldown[1] - self.e['XRWindow'].dt, 0)
        if hand.interacting == self:
            if (not self.parent.primary_grip) and (self.type in {'grip_interact', 'trigger_interact'}):
                # release an interact point if the item is dropped/thrown
                hand.interacting = None
                self.interacting = None

            holding = False
            if (self.type in {'grip', 'grip_interact'}) and hand.squeeze.holding:
                holding = True
            if (self.type in {'trigger_grip', 'trigger_interact'}) and hand.trigger.holding:
                holding = True
            if holding:
                self.input_pos = glm.vec3(hand.pos)
                self.input_rotation = glm.quat(hand.aim_rot[3], *(hand.aim_rot[:3]))
            elif (self.parent.primary_grip == self) or (self.parent.alt_grip == self):
                hand.interacting = None
                if self.type in {'grip', 'trigger_grip'}:
                    if self.parent.primary_grip == self:
                        if self.parent.alt_grip:
                            # make alt grip primary
                            self.parent.primary_grip = self.parent.alt_grip
                            self.parent.alt_grip = None
                        else:
                            self.parent.primary_grip = None

                            # handle throw because this is was the last grip
                            self.parent.velocity = vec3_exponent(hand.velocity(HAND_VELOCITY_TIMEFRAME), 1.7) / self.parent.weight

                            # angular velocity must be adjusted for snap turn orientation
                            self.parent.angular_velocity = hand.angular_velocity(HAND_VELOCITY_TIMEFRAME)

                            self.parent.rotation = self.input_rotation

                            # undo pivot placement by finding origin offset after the transform
                            origin = glm.vec3(0.0, 0.0, 0.0)
                            #interaction_point_offset = (self.parent.transform * origin) - self.world_pos
                            self.parent.pos = self.parent.transform * origin
                    else:
                        # this must be an alt grip
                        self.parent.alt_grip = None

                self.interacting = None

                self.parent.e['Sounds'].play_from('release', position=self.world_pos, volume=0.45)
                hand.vibrate(amplitude=0.7)
            if (not holding) and (self.type in {'grip_interact', 'trigger_interact'}):
                hand.interacting = None
                self.interacting = None
                self.parent.e['Sounds'].play_from('release', position=self.world_pos, volume=0.45)
                hand.vibrate(amplitude=0.7)


class VRItem(Element):
    def __init__(self, base_obj, pos=None, parts={}):
        super().__init__()

        self.parts = parts.copy()

        self.floor_item = False
        self.floor_mode = False

        self.in_slot = None

        self.hover_height = 0.65
        self.bob_force = 0.35

        self.weight = 0.5

        self.scale = glm.vec3(1.0, 1.0, 1.0)

        self.base_obj = base_obj

        self.points = {'grip': [], 'interact': []}
        self.default_grip = None

        # these indicate where the item is currently being held from
        self.primary_grip = None
        self.alt_grip = None

        self.holding_rotation = glm.quat()

        self.pos = glm.vec3(pos) if pos else glm.vec3(0.0, 0.0, 0.0)

        self.recoil = glm.vec2(0.5, 0.0)

        self.velocity_reset()
        self.gravity = 9.81 # m/s^2

        self.bounce = 0
        self.min_bounce = 0.2
        self.bounce_sound = None
        self.bounce_vol_scale = 1.0

        self.floor_rot_reset = True

        # simple grab makes it so that grabbing an unheld object within the radius of the origin binds the hand to the default grip point
        self.simple_grab = 0

        # this is the cooldown for the simple_grab since that doesn't use a point
        self.hover_vibrate_cooldown = [0, 0]

        self.calculate_transform()

    @property
    def free(self):
        return not self.primary_grip

    def first_point(self, p_type):
        if (p_type in self.points) and len(self.points[p_type]):
            return self.points[p_type][0].world_pos
        return glm.vec3(0, 0, 0)
    
    def handle_hover(self, hand):
        if not hand.interacting:
            if not self.hover_vibrate_cooldown[hand.hand]:
                hand.vibrate(amplitude=0.4)
            self.hover_vibrate_cooldown[hand.hand] = HOVER_COOLDOWN

    def update(self):
        self.hover_vibrate_cooldown[0] = max(self.hover_vibrate_cooldown[0] - self.e['XRWindow'].dt, 0)
        self.hover_vibrate_cooldown[1] = max(self.hover_vibrate_cooldown[1] - self.e['XRWindow'].dt, 0)

        if self.primary_grip:
            self.velocity = glm.vec3(0.0, 0.0, 0.0)
        else:
            if self.in_slot:
                self.velocity = glm.vec3(0.0, 0.0, 0.0)
                self.pos = self.in_slot.pos
                self.rotation = self.in_slot.rot
            elif self.floor_mode:
                # hovering logic
                self.angular_velocity = glm.quat(glm.rotate(0.3, (0, 1, 0)))
                self.velocity.y = max(-self.bob_force, self.velocity.y)
                if self.e['World'].check_block(self.pos + glm.vec3(0.0, -self.hover_height, 0.0)):
                    self.velocity.y += self.gravity * self.e['XRWindow'].dt * 0.04
                else:
                    self.velocity.y -= self.gravity * self.e['XRWindow'].dt * 0.04

                    # add one-way pressure to keep bob near the max strength
                    if self.velocity.y < 0:
                        self.velocity.y -= self.gravity * self.e['XRWindow'].dt * 0.01

            else:
                self.velocity.y -= self.gravity * self.e['XRWindow'].dt

            self.spin = self.spin * quat_scale(self.angular_velocity, self.e['XRWindow'].dt * 4)

            movement = self.velocity * self.e['XRWindow'].dt
            self.move(movement, bounce=True)

        self.calculate_transform()

    def velocity_reset(self, rot=True):
        if rot:
            self.rotation = glm.quat()
        else:
            # the soft rotation reset just keeps the y axis rotation
            # not the best solution, but it works
            forward = self.rotation * glm.vec3(0, 0, -1)
            self.rotation = glm.quat(glm.rotate(math.atan2(forward.x, forward.z) + math.pi, glm.vec3(0, 1, 0)))
        self.spin = glm.quat()
        self.velocity = glm.vec3(0.0, 0.0, 0.0)
        self.angular_velocity = glm.quat()

    def floor_reset(self):
        self.velocity_reset(rot=self.floor_rot_reset)

        if self.floor_item:
            self.floor_mode = True

    def move(self, movement, bounce=False):
        movement = glm.vec3(movement)

        self.pos.x += movement.x
        block = self.e['World'].check_block(self.pos)
        bounced = 0
        if block:
            cuboid = CornerCuboid(block.scaled_world_pos, (block.scale, block.scale, block.scale))
            if movement.x > 0:
                self.pos.x = cuboid.left - PHYSICS_EPSILON
                if bounce and (self.velocity.x > self.min_bounce):
                    self.velocity *= self.bounce
                    bounced = max(bounced, abs(self.velocity.x))
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.x *= -1
                else:
                    self.floor_reset()
            if movement.x < 0:
                self.pos.x = cuboid.right + PHYSICS_EPSILON
                if bounce and (self.velocity.x < -self.min_bounce):
                    self.velocity *= self.bounce
                    bounced = max(bounced, abs(self.velocity.x))
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.x *= -1
                else:
                    self.floor_reset()

        self.pos.y += movement.y
        block = self.e['World'].check_block(self.pos)
        if block:
            cuboid = CornerCuboid(block.scaled_world_pos, (block.scale, block.scale, block.scale))
            if movement.y > 0:
                self.pos.y = cuboid.bottom - PHYSICS_EPSILON
                if bounce and (self.velocity.y > self.min_bounce):
                    self.velocity *= self.bounce
                    bounced = max(bounced, abs(self.velocity.y))
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.y *= -1
                else:
                    self.floor_reset()
            if movement.y < 0:
                self.pos.y = cuboid.top + PHYSICS_EPSILON
                if bounce and (self.velocity.y < -self.min_bounce):
                    self.velocity *= self.bounce
                    bounced = max(bounced, abs(self.velocity.y))
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.y *= -1
                else:
                    self.floor_reset()

        self.pos.z += movement.z
        block = self.e['World'].check_block(self.pos)
        if block:
            cuboid = CornerCuboid(block.scaled_world_pos, (block.scale, block.scale, block.scale))
            if movement.z > 0:
                self.pos.z = cuboid.back - PHYSICS_EPSILON
                if bounce and (self.velocity.z > self.min_bounce):
                    self.velocity *= self.bounce
                    bounced = max(bounced, abs(self.velocity.z))
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.z *= -1
                else:
                    self.floor_reset()
            if movement.z < 0:
                self.pos.z = cuboid.front + PHYSICS_EPSILON
                if bounce and (self.velocity.z < -self.min_bounce):
                    self.velocity *= self.bounce
                    bounced = max(bounced, abs(self.velocity.z))
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.z *= -1
                else:
                    self.floor_reset()
        
        if bounced and self.bounce_sound:
            vol = min(bounced / 10, 1) * self.bounce_vol_scale
            self.e['Sounds'].play_from(self.bounce_sound, volume=vol, position=self.pos)

    def place(self, pos):
        self.pos = glm.vec3(pos)

    def add_point(self, point):
        if point.default:
            self.default_grip = point

        if point.type not in self.points:
            self.points[point.type] = []
        
        self.points[point.type].append(point)

        point.parent = self

    def calculate_transform(self):
        scale_mat = glm.scale(self.scale)
        if self.primary_grip:
            inverse_pivot = self.primary_grip.pos * -1
            recoil_rotation = glm.rotate(self.recoil.x, glm.vec3(0, 1, 0)) * glm.rotate(self.recoil.y, glm.vec3(1, 0, 0))
            if not self.alt_grip:
                rotation = self.primary_grip.input_rotation
                translation = glm.translate(self.primary_grip.input_pos)
                self.transform = translation * glm.mat4(rotation) * recoil_rotation * scale_mat * glm.translate(inverse_pivot)

                self.holding_rotation = rotation * glm.quat(recoil_rotation)
            else:
                # take up vector from primary grip to handle the roll of the aim
                up = glm.mat4(self.primary_grip.input_rotation) * glm.vec3(0, 1, 0)
                # look from the primary grip to the alt to get a rotation to line up grip points along Z axis
                grip_target = self.alt_grip.scaled_pos - self.primary_grip.scaled_pos
                local_rotation = glm.lookAt(glm.vec3(0.0, 0.0, 0.0), grip_target, glm.vec3(0.0, 1.0, 0.0))
                # get angle between hands to get world rotation of the object
                target = self.alt_grip.input_pos - self.primary_grip.input_pos
                # camera matrices are inverted, so it needs to be uninverted to get an object orientation
                rotation = glm.inverse(glm.lookAt(glm.vec3(0.0, 0.0, 0.0), target, up))
                # generate transform
                translation = glm.translate(self.primary_grip.input_pos)
                self.transform = translation * rotation * recoil_rotation * local_rotation * scale_mat * glm.translate(inverse_pivot)

                self.holding_rotation = glm.quat(rotation * recoil_rotation * local_rotation)
        else:
            self.transform = glm.translate(self.pos) * glm.mat4(self.spin) * glm.mat4(self.rotation) * scale_mat

    def handle_interaction_event(self, event_type, hand, point):
        pass

    def handle_interactions(self, hand):
        hand_pos = glm.vec3(hand.pos)
        if self.free and self.simple_grab:
            if sphere_collide(hand_pos, self.pos, self.simple_grab):
                self.handle_hover(hand)
                if hand.squeeze.pressed and (self.default_grip.type == 'grip'):
                    self.default_grip.grab(hand)
                elif hand.trigger.pressed and (self.default_grip.type == 'trigger_grip'):
                    self.default_grip.grab(hand)
        else:
            for group in self.points:
                for point in self.points[group]:
                    if group in {'grip', 'trigger_grip', 'grip_interact', 'trigger_interact'}:
                        if sphere_collide(hand_pos, point.world_pos, point.radius):
                            point.handle_hover(hand)
                            if group in {'grip', 'grip_interact'}:
                                if hand.squeeze.pressed:
                                    point.grab(hand)
                            if group in {'trigger_grip', 'trigger_interact'}:
                                if hand.trigger.pressed:
                                    point.grab(hand)
                    elif sphere_collide(hand_pos, point.world_pos, point.radius):
                        self.handle_interaction_event('hover', hand, point)
                        if hand.squeeze.pressed:
                            self.handle_interaction_event('grip', hand, point)
                        elif hand.trigger.pressed:
                            self.handle_interaction_event('trigger', hand, point)
        
        for group in self.points:
            if group in {'grip', 'trigger_grip', 'grip_interact', 'trigger_interact'}:
                for point in self.points[group]:
                    point.update(hand)

    def render(self, camera, uniforms={}):
        uniforms['world_light_pos'] = tuple(camera.light_pos)
        uniforms['world_transform'] = prep_mat(self.transform)
        uniforms['view_projection'] = camera.prepped_matrix
        uniforms['eye_pos'] = camera.eye_pos
        self.base_obj.vao.render(uniforms=uniforms)

class Gun(VRItem):
    def __init__(self, base_obj, pos=None, parts={}):
        super().__init__(base_obj, pos=pos, parts=parts)

        self.type = 'm4'

        self.floor_item = True
        self.simple_grab = 0.5
        self.bounce = 0.25

        self.rpm = 600
        self.cooldown = 0

        self.capacity = 10
        self.remaining_capacity = self.capacity
        self.chambered = True

        self.low_ammo_threshold = 10

        self.recoil_scale = glm.vec2(0.65, 1.25)
        self.recoil_pattern = 'default'
        self.recoil_velocity = glm.vec2(0.0, 0.0)
        self.recoil_decay = 30
        self.spray_control_force = 0
        self.spray_control_force_scale = 6
        self.spray_index = 0

        self.mag_offset = None
        self.rack_offset = glm.vec3(0.0, 0.0, 0.0)
        self.mag_loaded = True
        self.rack_point = None
        self.rack_vector = glm.vec3(0.0, 0.0, -1.0)
        self.rack_progress_state = 0
        self.chamber_offset = glm.vec3(0.0, 0.0, 0.0)
        self.casing_velocity = glm.vec3(0.0, 0.0, 0.0)

    def render(self, camera, uniforms={}):
        super().render(camera, uniforms=uniforms)
        if self.mag_offset and ('mag' in self.parts) and self.mag_loaded:
            # camera-related uniforms already set inside super method
            uniforms['world_transform'] = prep_mat(self.transform * glm.translate(self.mag_offset))
            self.parts['mag'].vao.render(uniforms=uniforms)
        if 'rack' in self.parts:
            uniforms['world_transform'] = prep_mat(self.transform * glm.translate(self.rack_offset))
            self.parts['rack'].vao.render(uniforms=uniforms)

    def handle_interaction_event(self, event_type, hand, point):
        super().handle_interaction_event(event_type, hand, point)

        if point.type == 'magazine':
            if (event_type == 'trigger') and (not hand.interacting):
                self.mag_loaded = False
                mag = Magazine(self, hand.pos)
                mag.remaining_capacity = self.remaining_capacity
                self.remaining_capacity = 0
                mag.default_grip.grab(hand)
                self.e['Demo'].items.append(mag)
                self.e['Sounds'].play_from('release_mag', position=self.first_point('slot_reference'), volume=0.4)

    def fire(self):
        if 'muzzle' in self.points:
            muzzle_pos = self.points['muzzle'][0].world_pos
            angle = self.holding_rotation

            self.e['Sounds'].play_from('shoot', volume=1.0, position=muzzle_pos)
            if self.remaining_capacity < self.low_ammo_threshold:
                self.e['Sounds'].play_from('low_ammo', volume=1.0, position=muzzle_pos)

            self.e['Demo'].tracers.append(Tracer(self.e['Demo'].tracer_res, self.type, muzzle_pos, angle))
            self.e['Demo'].items.append(Casing(self))

            pattern = RECOIL_PATTERNS[self.recoil_pattern]
            if len(pattern['start']) <= self.spray_index:
                recoil = pattern['loop'][self.spray_index % len(pattern['loop'])]
            else:
                recoil = pattern['start'][self.spray_index]
            self.recoil_velocity += glm.vec2(recoil)
            self.spray_control_force = 0
            self.spray_index += 1

            if self.primary_grip and self.primary_grip.interacting:
                self.primary_grip.interacting.vibrate(amplitude=1.0)

            if self.alt_grip and self.alt_grip.interacting:
                self.alt_grip.interacting.vibrate(amplitude=1.0)

    def handle_recoil(self):
        dt = self.e['XRWindow'].dt

        recoil_modifier = 0.4 if self.primary_grip and self.alt_grip else 1.0

        self.recoil += self.recoil_velocity * dt * self.recoil_scale * recoil_modifier
        self.recoil.y = min(self.recoil.y, math.pi / 3 * recoil_modifier)
        vel_recovery_amount = self.recoil_decay * dt
        if vel_recovery_amount > glm.length(self.recoil_velocity):
            self.recoil_velocity = glm.vec2(0.0, 0.0)
        else:
            vel_recovery_angle = math.atan2(-self.recoil_velocity.y, -self.recoil_velocity.x)
            self.recoil_velocity.x += math.cos(vel_recovery_angle) * vel_recovery_amount
            self.recoil_velocity.y += math.sin(vel_recovery_angle) * vel_recovery_amount
        
        if self.spray_control_force:
            rec_recovery_amount = self.spray_control_force * dt
            if rec_recovery_amount > glm.length(self.recoil):
                self.recoil = glm.vec2(0.0, 0.0)
                if not glm.length(self.recoil_velocity):
                    self.spray_index = 0
            else:
                rec_recovery_angle = math.atan2(-self.recoil.y, -self.recoil.x)
                self.recoil.x += math.cos(rec_recovery_angle) * rec_recovery_amount
                self.recoil.y += math.sin(rec_recovery_angle) * rec_recovery_amount
            
        self.spray_control_force += dt * self.spray_control_force_scale

    def update(self):
        super().update()

        dt = self.e['XRWindow'].dt
        residual_cooldown = max(0, dt - self.cooldown) if self.cooldown else 0
        self.cooldown = max(0, self.cooldown - dt)

        self.handle_recoil()

        if self.primary_grip and self.primary_grip.interacting and self.primary_grip.interacting.pressed_upper and self.mag_loaded:
            self.mag_loaded = False
            mag = Magazine(self)
            self.e['Demo'].items.append(mag)
            self.e['Sounds'].play_from('release_mag', position=self.first_point('slot_reference'), volume=0.4)
            mag.remaining_capacity = self.remaining_capacity
            self.remaining_capacity = 0

        if self.primary_grip and self.primary_grip.interacting and self.primary_grip.interacting.trigger.holding and (self.primary_grip == self.default_grip):
            if not self.cooldown:
                # only fire if a round is chambered
                if self.chambered:
                    self.chambered = False
                    # load next round into chamber if available
                    if self.remaining_capacity:
                        self.remaining_capacity = max(0, self.remaining_capacity - 1)
                        self.chambered = True
                    self.fire()
                    self.cooldown = max(0, 1 / (self.rpm / 60) - residual_cooldown)
                elif self.primary_grip.interacting.trigger.pressed:
                    self.e['Sounds'].play_from('no_ammo', volume=1.0, position=self.primary_grip.world_pos)

        if self.rack_point and self.rack_point.interacting:
            pull = segment_project_progress(self.rack_point.world_pos, self.rack_point.offsetted_world_pos(self.rack_vector), self.rack_point.input_pos)
            if (pull == 1) and (not self.rack_progress_state):
                self.rack_progress_state = 1
                self.e['Sounds'].play_from('rack', position=self.rack_point.world_pos, volume=0.7)

                if self.chambered:
                    self.e['Demo'].items.append(Casing(self))

                self.chambered = False
                if self.remaining_capacity:
                    self.chambered = True
                    self.remaining_capacity = max(0, self.remaining_capacity - 1)
            if (pull < 0.8) and self.rack_progress_state:
                self.rack_progress_state = 0
            self.rack_offset = self.rack_vector * pull
            self.rack_point.hand_override = self.rack_point.offsetted_world_pos(self.rack_offset)
        else:
            if self.rack_point.hand_override:
                self.e['Sounds'].play_from('rack_close', position=self.rack_point.world_pos, volume=0.7)
            self.rack_offset = glm.vec3(0)
            self.rack_point.hand_override = None

class Knife(VRItem):
    def __init__(self, base_obj, pos=None):
        super().__init__(base_obj, pos=pos)

        self.scale = glm.vec3(0.25, 0.25, 0.25)
        self.bounce = 0.5
        self.weight = 0.75
        self.floor_item = True

        self.add_point(VRItemPoint('grip', (0, -0.4, 0), default=True))

        self.simple_grab = 0.3

class Magazine(VRItem):
    def __init__(self, src_weapon, pos=None):
        if not pos:
            # select dedicated magazine position from source weapon
            pos = src_weapon.transform * src_weapon.mag_offset
        super().__init__(src_weapon.parts['mag'], pos=pos)

        self.remaining_capacity = src_weapon.capacity

        self.rotation = glm.quat(src_weapon.holding_rotation)

        self.scale = glm.vec3(src_weapon.scale)

        self.add_point(VRItemPoint('trigger_grip', (0, 0, 0), default=True))

        self.add_point(VRItemPoint('slot_reference', (0, 4.6 / 16, 0)))

        self.bounce = 0.5
        self.weight = 0.75

        self.held_outside_load_range = False

        self.calculate_transform()

    def update(self):
        super().update()

        # check if being held
        if self.primary_grip and self.primary_grip.interacting:
            # check if the other hand is holding something
            if self.primary_grip.interacting.other and self.primary_grip.interacting.other.interacting:
                gun = self.primary_grip.interacting.other.interacting.parent
                # check if the other item is a gun
                if issubclass(gun.__class__, Gun):
                    # if close enough, load mag
                    if glm.length(gun.first_point('slot_reference') - self.first_point('slot_reference')) < gun.reload_range:
                        if self.held_outside_load_range:
                            gun.mag_loaded = True
                            gun.remaining_capacity = self.remaining_capacity
                            self.primary_grip.interacting.vibrate(amplitude=1.0)
                            self.e['Sounds'].play_from('load', position=self.first_point('slot_reference'), volume=0.6)
                            # unlink mag from hand
                            self.primary_grip.interacting.interacting = None
                            self.primary_grip.interacting = None
                            # delete self
                            return True
                    elif not self.held_outside_load_range:
                        if glm.length(gun.first_point('slot_reference') - self.first_point('slot_reference')) > gun.reload_range * 1.5:
                            self.held_outside_load_range = True

class M4(Gun):
    def __init__(self, base_obj, pos=None):
        super().__init__(base_obj, pos=pos, parts={'mag': elems['Demo'].m4_mag_res, 'rack': elems['Demo'].m4_rack_res})

        self.mag_offset = glm.vec3(0, -7.5 / 16, 0.5 / 16)

        self.scale = glm.vec3(0.19, 0.19, 0.19)
        self.weight = 1.25

        self.reload_range = 0.05
        self.capacity = 30
        self.remaining_capacity = self.capacity

        self.rpm = 800

        self.add_point(VRItemPoint('grip', (0, -0.26, 0.735), default=True))

        self.add_point(VRItemPoint('grip', (0, 0, -0.735)))

        self.add_point(VRItemPoint('muzzle', (0, 0.18, -2.6)))

        self.add_point(VRItemPoint('magazine', self.mag_offset, radius=0.1))

        self.add_point(VRItemPoint('slot_reference', (0, self.mag_offset.y + 3 / 16, self.mag_offset.z)))

        self.rack_point = VRItemPoint('trigger_interact', (0, 4.8 / 16, 13.8 / 16), radius=0.08)
        self.add_point(self.rack_point)
        self.rack_vector = glm.vec3(0.0, 0.0, 0.45)

        self.chamber_offset = glm.vec3(0.0, 2.9 / 16, 0.0)
        self.casing_velocity = glm.vec3(1.0, 0.3, 1.0)

    def update(self):
        super().update()

class Casing(VRItem):
    def __init__(self, src_weapon, pos=None):
        super().__init__(elems['Demo'].casing_res, pos=pos)

        self.scale = glm.vec3(0.07)

        self.life = 5

        self.src_weapon = src_weapon
        if not pos:
            self.rotation = self.src_weapon.holding_rotation
            self.pos = self.src_weapon.transform * self.src_weapon.chamber_offset
            initial_velocity = self.src_weapon.casing_velocity
            initial_velocity.x *= (random.random() + 3.5) / 4
            initial_velocity.y *= (random.random() + 3.5) / 4
            initial_velocity.z *= (random.random() + 3.5) / 4
            self.velocity = glm.mat4(self.src_weapon.holding_rotation) * initial_velocity

        self.bounce_sound = 'casing_bounce'
        self.bounce_vol_scale = 0.5
        self.bounce = 0.5
        self.floor_rot_reset = False

        self.calculate_transform()

    def update(self):
        super().update()

        self.life = max(0, self.life - self.e['XRWindow'].dt)

        if not self.life:
            return True
