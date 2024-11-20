from ..elements import ElementSingleton
from .chunk import Chunk, CHUNK_SIZE
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

    def get_block(self, world_pos):
        chunk_id = tuple(int(world_pos[i] // CHUNK_SIZE) for i in range(3))
        if chunk_id in self.chunks:
            return self.chunks[chunk_id].get_block(world_pos)

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

    def render(self, camera, uniforms={}):
        for chunk in self.chunks.values():
            chunk.render(camera, uniforms=uniforms)