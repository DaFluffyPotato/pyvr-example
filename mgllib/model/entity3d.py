import glm

from ..mat3d import Transform3D
from ..elements import Element
from ..camera import Camera

class Entity3D(Element):
    def __init__(self, vao):
        super().__init__()
        
        self.vao = vao
        self.transform = Transform3D()

    def render(self, camera, uniforms={}):
        uniforms['world_light_pos'] = tuple(camera.light_pos)
        uniforms['world_transform'] = self.transform.matrix
        uniforms['view_projection'] = camera.prepped_matrix
        uniforms['eye_pos'] = camera.eye_pos
        self.vao.render(uniforms=uniforms)