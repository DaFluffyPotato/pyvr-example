from array import array

import moderngl

from ..elements import Element
from .coord_gen import gen_cube
from ..mat3d import Transform3D
from ..model.vao import TexturedVAOs


def flatten(lss):
    return [x for ls in lss for x in ls]

CACHE = {
    'texture': None,
}

class StandaloneBlock(Element):
    def __init__(self, program, block_id='chiseled_stone', pos=(0, 0, 0)):
        super().__init__()

        self.block_id = block_id

        self.transform = Transform3D()
        self.transform.pos = list(pos)

        uv_base = (0, 0)
        raw_geometry = gen_cube(uv_base, scale=0.75)

        ctx = self.e['MGL'].ctx
        buffer = ctx.buffer(data=array('f', flatten(raw_geometry)))
        vao = ctx.vertex_array(program, [(buffer, '3f 2f 3f', 'vert', 'uv', 'normal')])

        self.tvaos = TexturedVAOs(program, [vao])

        if not CACHE['texture']:
            CACHE['texture'] = self.e['MGL'].load_texture('data/textures/block_textures.png')
            CACHE['texture'].filter = (moderngl.NEAREST, moderngl.NEAREST)

        self.tvaos.bind_texture(CACHE['texture'], 'texture')
    
    def bind_texture(self, texture, category):
        self.tvaos(texture, category)

    def render(self, camera, uniforms={}):
        uniforms['world_light_pos'] = tuple(camera.light_pos)
        uniforms['world_transform'] = self.transform.matrix
        uniforms['view_projection'] = camera.prepped_matrix
        uniforms['eye_pos'] = camera.pos
        self.tvaos.render(uniforms=uniforms)
