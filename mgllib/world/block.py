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

TEXTURE_RESOLUTION = 16
BLOCK_MAP = {
    'chiseled_stone': 0,
    'log': 1,
    'grass': 2,
}

BLOCK_CACHE = {}

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
        uniforms['eye_pos'] = camera.eye_pos
        self.tvaos.render(uniforms=uniforms)

class BlockReferenceGeometry(Element):
    def __init__(self, block_id='chiseled_stone'):
        super().__init__()

        self.block_id = block_id
        self.block_id_num = BLOCK_MAP[self.block_id]

        if not CACHE['texture']:
            CACHE['texture'] = self.e['MGL'].load_texture('data/textures/block_textures.png')
            CACHE['texture'].filter = (moderngl.NEAREST, moderngl.NEAREST)

        tex_count = int(CACHE['texture'].height // TEXTURE_RESOLUTION)

        y_offset = (tex_count - 1) - self.block_id_num
        uv_scale = (1 / 6, 1 / tex_count)
        uv_base = (0, y_offset * uv_scale[1])
        self.raw_geometry = gen_cube(uv_base, uv_scale=uv_scale)

    def localize(self, chunk_pos=(0, 0, 0), side_flags=(1, 1, 1, 1, 1, 1)):
        data_buffer = []
        for i, point in enumerate(self.raw_geometry):
            if side_flags[int(i // 6)]:
                data_buffer += [point[0] + chunk_pos[0], point[1] + chunk_pos[1], point[2] + chunk_pos[2], *point[3:]]
        return data_buffer
    
class ChunkBlock(Element):
    def __init__(self, parent, block_id='chiseled_stone', chunk_pos=(0, 0, 0)):
        super().__init__()

        self.chunk = parent
        self.block_id = block_id
        self.chunk_pos = chunk_pos

        self.generate()

    def generate(self):
        # do side flags later
        self.buffer = BLOCK_CACHE[self.block_id].localize(chunk_pos=self.chunk_pos)

def populate_block_cache():
    for block_id in BLOCK_MAP:
        BLOCK_CACHE[block_id] = BlockReferenceGeometry(block_id=block_id)