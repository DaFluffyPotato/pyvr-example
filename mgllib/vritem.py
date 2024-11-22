import glm

from .model.entity3d import Entity3D
from .shapes.cuboid import CornerCuboid
from .shapes.sphere import sphere_collide
from .elements import Element
from .mat3d import prep_mat, quat_scale
from .const import HAND_VELOCITY_TIMEFRAME, PHYSICS_EPSILON

class VRItemComponent(Element):
    def __init__(self):
        super().__init__()

# the two types are grip and interact (grib vs trigger)
class VRItemPoint(Element):
    def __init__(self, point_type, pos, default=False):
        self.parent = None
        self.type = point_type
        self.pos = glm.vec3(pos)
        self.default = default

        self.local_rotation = glm.quat(1.0, 0.0, 0.0, 0.0)

        self.input_rotation = glm.quat(1.0, 0.0, 0.0, 0.0)
        self.input_pos = glm.vec3(0.0, 0.0, 0.0)

        self.interacting = None

    @property
    def world_pos(self):
        return self.parent.transform * self.pos
    
    def grab(self, hand):
        if self.type == 'grip':
            if not (hand.interacting or self.interacting):
                hand.interacting = self
                self.parent.primary_grip = self
                self.interacting = hand
                self.parent.velocity_reset()
                self.parent.floor_mode = False
    
    def update(self, hand):
        if hand.interacting == self:
            if hand.squeeze.holding:    
                self.input_pos = glm.vec3(hand.pos)
                self.input_rotation = glm.quat(hand.aim_rot[3], *(hand.aim_rot[:3]))
            elif self.parent.primary_grip == self:
                hand.interacting = None
                self.parent.primary_grip = None
                self.interacting = None
                self.parent.velocity = glm.vec3(hand.velocity(HAND_VELOCITY_TIMEFRAME)) / self.parent.weight

                # angular velocity must be adjusted for snap turn orientation
                self.parent.angular_velocity = hand.angular_velocity(HAND_VELOCITY_TIMEFRAME)

                self.parent.rotation = self.input_rotation

                # undo pivot placement by finding origin offset after the transform
                origin = glm.vec3(0.0, 0.0, 0.0)
                #interaction_point_offset = (self.parent.transform * origin) - self.world_pos
                self.parent.pos = self.parent.transform * origin

class VRItem(Element):
    def __init__(self, base_obj, pos=None):
        super().__init__()

        self.floor_item = False
        self.floor_mode = False

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

        self.pos = glm.vec3(pos) if pos else glm.vec3(0.0, 0.0, 0.0)

        self.velocity_reset()
        self.gravity = 9.81 # m/s^2

        self.bounce = 0
        self.min_bounce = 0.2

        # simple grab makes it so that grabbing an unheld object within the radius of the origin binds the hand to the default grip point
        self.simple_grab = 0

        self.calculate_transform()

    @property
    def free(self):
        return not self.primary_grip

    def update(self):
        if self.primary_grip:
            self.velocity = glm.vec3(0.0, 0.0, 0.0)
        else:
            if self.floor_mode:
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

    def velocity_reset(self):
        self.rotation = glm.quat()
        self.spin = glm.quat()
        self.velocity = glm.vec3(0.0, 0.0, 0.0)
        self.angular_velocity = glm.quat()

    def floor_reset(self):
        self.velocity_reset()

        if self.floor_item:
            self.floor_mode = True

    def move(self, movement, bounce=False):
        movement = glm.vec3(movement)

        self.pos.x += movement.x
        block = self.e['World'].check_block(self.pos)
        if block:
            cuboid = CornerCuboid(block.scaled_world_pos, (block.scale, block.scale, block.scale))
            if movement.x > 0:
                self.pos.x = cuboid.left - PHYSICS_EPSILON
                if bounce and (self.velocity.x > self.min_bounce):
                    self.velocity *= self.bounce
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.x *= -1
                else:
                    self.floor_reset()
            if movement.x < 0:
                self.pos.x = cuboid.right + PHYSICS_EPSILON
                if bounce and (self.velocity.x < -self.min_bounce):
                    self.velocity *= self.bounce
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
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.y *= -1
                else:
                    self.floor_reset()
            if movement.y < 0:
                self.pos.y = cuboid.top + PHYSICS_EPSILON
                if bounce and (self.velocity.y < -self.min_bounce):
                    self.velocity *= self.bounce
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
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.z *= -1
                else:
                    self.floor_reset()
            if movement.z < 0:
                self.pos.z = cuboid.front + PHYSICS_EPSILON
                if bounce and (self.velocity.z < -self.min_bounce):
                    self.velocity *= self.bounce
                    quat_scale(self.angular_velocity, self.bounce)
                    self.velocity.z *= -1
                else:
                    self.floor_reset()

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
            if not self.alt_grip:
                rotation = self.primary_grip.input_rotation
                translation = glm.translate(self.primary_grip.input_pos)
                self.transform = translation * glm.mat4(rotation) * scale_mat * glm.translate(inverse_pivot)
            else:
                # take up vector from primary grip and use lookat for alt
                pass
        else:
            self.transform = glm.translate(self.pos) * glm.mat4(self.spin) * glm.mat4(self.rotation) * scale_mat

    def handle_interactions(self, hand):
        hand_pos = glm.vec3(hand.pos)
        if self.free and self.simple_grab:
            if sphere_collide(hand_pos, self.pos, self.simple_grab):
                if hand.squeeze.pressed:
                    self.default_grip.grab(hand)

        # TODO: implement logic when simple_grab is disabled
        
        for point in self.points['grip']:
            point.update(hand)

    def render(self, camera, uniforms={}):
        uniforms['world_light_pos'] = tuple(camera.light_pos)
        uniforms['world_transform'] = prep_mat(self.transform)
        uniforms['view_projection'] = camera.prepped_matrix
        uniforms['eye_pos'] = camera.eye_pos
        self.base_obj.vao.render(uniforms=uniforms)

# item points are pre-scaling
# op order is pivot -> scale -> rotate (either copy src or aim at alt) -> world translate

class Knife(VRItem):
    def __init__(self, base_obj, pos=None):
        super().__init__(base_obj, pos=pos)

        self.scale = glm.vec3(0.25, 0.25, 0.25)
        self.bounce = 0.5
        self.weight = 0.2
        self.floor_item = True

        self.add_point(VRItemPoint('grip', (0, -0.4, 0), default=True))

        self.simple_grab = 0.3