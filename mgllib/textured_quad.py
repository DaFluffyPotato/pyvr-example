from array import array

import glm
import moderngl

from .elements import Element
from .mat3d import prep_mat

class TexturedQuad(Element):
    def __init__(self):
        super().__init__()

        self.ctx = self.e['MGL'].ctx

        self.program = self.e['Demo'].no_norm_shader

        self.quad_buffer = self.ctx.buffer(data=array('f', [
            # position (x, y, z) , texture coordinates (x, y)
            -1.0, 0.0, -1.0, 0.0, 0.0,
            -1.0, 0.0, 1.0, 0.0, 1.0,
            1.0, 0.0, -1.0, 1.0, 0.0,
            1.0, 0.0, 1.0, 1.0, 1.0,
        ]))

        self.quad_vao = self.ctx.vertex_array(self.program, [(self.quad_buffer, '3f 2f', 'vert', 'uv')])

        self.texture = None
        self.locally_owned_texture = False

        self.transform = glm.mat4()

    def release(self):
        if self.texture and self.locally_owned_texture:
            self.texture.release()
            self.texture = None
        self.quad_vao.release()
        self.quad_buffer.release()

    def bind_texture(self, texture):
        if self.texture and self.locally_owned_texture:
            self.texture.release()
            self.texture = None
        self.texture = texture
        self.locally_owned_texture = False

    def apply_surface(self, surf):
        new_tex = self.e['MGL'].pg2tx(surf)
        self.bind_texture(new_tex)
        self.locally_owned_texture = True

    def render(self, camera, uniforms={}):
        tex_id = 0
        self.texture.use(tex_id)
        self.program['tex'].value = tex_id

        uniforms['world_transform'] = prep_mat(self.transform)
        uniforms['view_projection'] = camera.prepped_matrix

        for uniform in uniforms:
            self.program[uniform].value = uniforms[uniform]

        self.quad_vao.render(mode=moderngl.TRIANGLE_STRIP)