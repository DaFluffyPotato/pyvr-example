import math
from array import array

import glm
import moderngl

from ..mat3d import flatten, prep_mat
from ..elements import Element

TETRAHEDRON_VERTICES = [
    (math.cos(0.0) * 0.7, math.sin(0.0) * 0.7, 0.0),
    (math.cos(math.pi * 2 / 3) * 0.7, math.sin(math.pi * 2 / 3) * 0.7, 0.5),
    (math.cos(math.pi * 4 / 3) * 0.7, math.sin(math.pi * 4 / 3) * 0.7, 0.5),
    (0.0, 0.0, -0.5),
]

TETRAHEDRON = [
    TETRAHEDRON_VERTICES[0],
    TETRAHEDRON_VERTICES[1],
    TETRAHEDRON_VERTICES[2],

    TETRAHEDRON_VERTICES[0],
    TETRAHEDRON_VERTICES[2],
    TETRAHEDRON_VERTICES[3],

    TETRAHEDRON_VERTICES[1],
    TETRAHEDRON_VERTICES[0],
    TETRAHEDRON_VERTICES[3],

    TETRAHEDRON_VERTICES[2],
    TETRAHEDRON_VERTICES[1],
    TETRAHEDRON_VERTICES[3],
]

class Polygon(Element):
    def __init__(self, points, program):
        super().__init__()

        ctx = self.e['MGL'].ctx
        self.program = program
        self.buffer = ctx.buffer(data=array('f', flatten(points)))
        self.vao = ctx.vertex_array(program, [(self.buffer, '3f', 'vert')])

    def update_uniforms(self, uniforms={}):
        tex_id = 0
        uniform_list = list(self.program)
        for uniform in uniforms:
            if uniform in uniform_list:
                if type(uniforms[uniform]) == moderngl.Texture:
                    # bind tex to next ID
                    uniforms[uniform].use(tex_id)
                    # specify tex ID as uniform target
                    self.program[uniform].value = tex_id
                    tex_id += 1
                else:
                    self.program[uniform].value = uniforms[uniform]

class PolygonOBJ(Element):
    def __init__(self, shape, pos=None, rotation=None):
        super().__init__()

        self.polygon = shape

        self.scale = glm.vec3(1.0, 1.0, 1.0)
        self.pos = glm.vec3(pos) if pos else glm.vec3(0.0, 0.0, 0.0)
        self.rotation = glm.quat(rotation) if rotation else glm.quat()

        self.calculate_transform()

    def calculate_transform(self):
        scale_mat = glm.scale(self.scale)
        self.transform = glm.translate(self.pos) * glm.mat4(self.rotation) * scale_mat

    def update(self):
        self.calculate_transform()

    def render(self, camera, uniforms={}):
        uniforms['world_transform'] = prep_mat(self.transform)
        uniforms['view_projection'] = camera.prepped_matrix

        self.polygon.update_uniforms(uniforms=uniforms)

        self.polygon.vao.render(mode=moderngl.TRIANGLES)