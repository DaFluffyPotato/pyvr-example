import glm

from .mat3d import prep_mat
from .elements import Element

class Entity(Element):
    def __init__(self, base_obj, pos=None, rotation=None):
        super().__init__()
        
        self.scale = glm.vec3(1.0, 1.0, 1.0)
        self.pos = glm.vec3(pos) if pos else glm.vec3(0.0, 0.0, 0.0)
        self.rotation = glm.quat(rotation) if rotation else glm.quat()

        self.base_obj = base_obj

        self.calculate_transform()

    def calculate_transform(self):
        scale_mat = glm.scale(self.scale)
        self.transform = glm.translate(self.pos) * glm.mat4(self.rotation) * scale_mat

    def render(self, camera, uniforms={}):
        uniforms['world_light_pos'] = tuple(camera.light_pos)
        uniforms['world_transform'] = prep_mat(self.transform)
        uniforms['view_projection'] = camera.prepped_matrix
        uniforms['eye_pos'] = camera.eye_pos
        self.base_obj.vao.render(uniforms=uniforms)