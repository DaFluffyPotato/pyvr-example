from ..elements import ElementSingleton
from .chunk import Chunk, CHUNK_SIZE, BLOCK_SCALE
from .block import populate_block_cache

class World(ElementSingleton):
    def __init__(self, program):
        super().__init__()

        self.chunks = {}
        self.program = program

        populate_block_cache()

        self.reset_rebuild()

    def reset_rebuild(self):
        self.temp_rebuild = {
            'combines_needed': set(),
            'rebuilt': set()
        }

    def combine_missing(self):
        for chunk in self.temp_rebuild['combines_needed'] - self.temp_rebuild['rebuilt']:
            chunk.combine()

        self.reset_rebuild()

    def add_decor(self, decor):
        world_pos = decor.pos
        chunk_id = tuple(int((world_pos[i] / BLOCK_SCALE) // CHUNK_SIZE) for i in range(3))
        if chunk_id not in self.chunks:
            self.chunks[chunk_id] = Chunk(self, chunk_id)
        
        self.chunks[chunk_id].add_decor(decor)

    def get_block(self, world_pos):
        chunk_id = tuple(int(world_pos[i] // CHUNK_SIZE) for i in range(3))
        if chunk_id in self.chunks:
            return self.chunks[chunk_id].get_block(world_pos)
    
    # takes floating world pos instead of grid pos
    def nearby_blocks(self, world_pos, radii=(1, 1, 1)):
        blocks = []
        base_pos = tuple(int(world_pos[i] // BLOCK_SCALE) for i in range(3))
        for x in range(radii[0] * 2 + 1):
            for y in range(radii[1] * 2 + 1):
                for z in range(radii[2] * 2 + 1):
                    lookup_pos = (base_pos[0] + x - radii[0], base_pos[1] + y - radii[1], base_pos[2] + z - radii[2])
                    block = self.get_block(lookup_pos)
                    if block:
                        blocks.append(block)
        return blocks
    
    # takes floating world pos instead of grid pos
    def check_block(self, world_pos):
        base_pos = tuple(int(world_pos[i] // BLOCK_SCALE) for i in range(3))
        block = self.get_block(base_pos)
        return block

    def add_block(self, block_id, world_pos, rebuild=True):
        chunk_id = tuple(int(world_pos[i] // CHUNK_SIZE) for i in range(3))
        if chunk_id not in self.chunks:
            self.chunks[chunk_id] = Chunk(self, chunk_id)
        
        self.chunks[chunk_id].add_block(block_id, world_pos, rebuild=rebuild)
    
    def remove_block(self, world_pos, rebuild=True):
        chunk_id = tuple(int(world_pos[i] // CHUNK_SIZE) for i in range(3))
        if chunk_id in self.chunks:
            self.chunks[chunk_id].remove_block(world_pos, rebuild=rebuild)

    def rebuild(self, deltas_only=False):
        for chunk in self.chunks.values():
            chunk.rebuild(deltas_only=deltas_only)

        self.combine_missing()

    def rebuild_decor(self):
        for chunk in self.chunks.values():
            chunk.rebuild_decor()

    def render(self, camera, uniforms={}, decor_uniforms={}):
        for chunk in self.chunks.values():
            chunk.render(camera, uniforms=uniforms, decor_uniforms=decor_uniforms)