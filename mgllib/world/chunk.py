from array import array

from ..elements import Element
from .block import ChunkBlock, CACHE, N7_OFFSETS
from ..model.vao import TexturedVAOs
from ..mat3d import Transform3D

CHUNK_SIZE = 16
BLOCK_SCALE = 0.75

class Chunk(Element):
    def __init__(self, parent, chunk_id):
        super().__init__()

        self.world = parent
        self.chunk_id = chunk_id
        self.world_offset = tuple(self.chunk_id[i] * CHUNK_SIZE for i in range(3))
        self.program = self.world.program

        self.transform = Transform3D()
        self.transform.pos = [v * BLOCK_SCALE for v in self.world_offset]
        self.transform.scale = [BLOCK_SCALE, BLOCK_SCALE, BLOCK_SCALE]

        # absolute position is used for blocks to speed up lookups
        self.blocks = {}

        self.tvaos = None
        self.buffer = None

        self.changes_since_rebuild = set()

    def release(self):
        if self.tvaos:
            for vao in self.tvaos.vaos:
                vao.release()
        
        if self.buffer:
            self.buffer.release()

        self.tvaos = None
        self.buffer = None

    def combine(self):
        self.release()

        content = []
        
        for block in self.blocks.values():
            content += block.buffer
        
        self.buffer_from_content(content)

    def buffer_from_content(self, content):
        ctx = self.e['MGL'].ctx
        if len(content):
            self.buffer = ctx.buffer(data=array('f', content))
            vao = ctx.vertex_array(self.program, [(self.buffer, '3f 2f 3f', 'vert', 'uv', 'normal')])

            self.tvaos = TexturedVAOs(self.program, [vao])

            self.tvaos.bind_texture(CACHE['texture'], 'texture')
        else:
            self.buffer = None
            self.tvaos = None

    # TODO: add change list param to limit rebuild
    def rebuild(self, deltas_only=False, local=False):
        # release any old data that's about to be replaced
        self.release()

        content = []

        if not deltas_only:
            for block in self.blocks.values():
                block.generate()
                content += block.buffer
        else:
            built_blocks = set()
            for pos in self.changes_since_rebuild:
                for offset in N7_OFFSETS:
                    world_pos = tuple(offset[i] + v for i, v in enumerate(pos))
                    if world_pos not in built_blocks:
                        built_blocks.add(world_pos)
                    else:
                        continue
                    block = self.world.get_block(world_pos)
                    if block:
                        block.generate()
                        if block.chunk != self:
                            self.world.temp_rebuild['combines_needed'].add(block.chunk)
            
            for block in self.blocks.values():
                content += block.buffer
        
        self.changes_since_rebuild = set()
        self.world.temp_rebuild['rebuilt'].add(self)

        self.buffer_from_content(content)

        if local and deltas_only:
            self.world.combine_missing()

    def get_block(self, world_pos):
        if world_pos in self.blocks:
            return self.blocks[world_pos]

    def add_block(self, block_id, world_pos, rebuild=True):
        chunk_pos = tuple(world_pos[i] - self.world_offset[i] for i in range(3))

        self.blocks[world_pos] = ChunkBlock(self, block_id=block_id, chunk_pos=chunk_pos)

        self.changes_since_rebuild.add(world_pos)

        if rebuild:
            self.rebuild(deltas_only=True, local=True)

    def remove_block(self, world_pos, rebuild=True):
        if world_pos in self.blocks:
            del self.blocks[world_pos]

            self.changes_since_rebuild.add(world_pos)

            if rebuild:
                self.rebuild(deltas_only=True, local=True)

    def render(self, camera, uniforms={}):
        if self.tvaos:
            uniforms['world_light_pos'] = tuple(camera.light_pos)
            uniforms['world_transform'] = self.transform.matrix
            uniforms['view_projection'] = camera.prepped_matrix
            uniforms['eye_pos'] = camera.eye_pos
            self.tvaos.render(uniforms=uniforms)
