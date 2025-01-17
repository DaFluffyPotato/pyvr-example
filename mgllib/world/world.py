import math

import astar

from ..elements import ElementSingleton, Element
from .chunk import Chunk, CHUNK_SIZE, BLOCK_SCALE
from .block import populate_block_cache
from .const import MaxDepthReached

VALID_MOVEMENT_DIRECTIONS = [
    (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1),
    (1, 1, 0), (-1, 1, 0), (0, 1, 1), (0, 1, -1),
    (1, -1, 0), (-1, -1, 0), (0, -1, 1), (0, -1, -1)
]

DIAGONAL_CHECKS = {
    (1, 0, 1): [(1, 0, 0), (0, 0, 1)],
    (-1, 0, 1): [(-1, 0, 0), (0, 0, 1)],
    (1, 0, -1): [(1, 0, 0), (0, 0, -1)],
    (-1, 0, -1): [(-1, 0, 0), (0, 0, -1)],
}

class Pathfinder(astar.AStar):
    def __init__(self, world, max_depth=2000):
        super().__init__()

        self.world = world
        self.depth = 0
        self.max_depth = max_depth
    
    def astar(self, *args, **kwargs):
        self.depth = 0
        return super().astar(*args, **kwargs)

    def neighbors(self, node):
        neighbors = self.world.lookup_neighbors(node)
        return neighbors

    def distance_between(self, n1, n2):
        return math.sqrt((n2[0] - n1[0]) ** 2 + (n2[1] - n1[1]) ** 2 + (n2[2] - n1[2]) ** 2)
    
    def heuristic_cost_estimate(self, current, goal):
        self.depth += 1
        if self.depth >= self.max_depth:
            raise MaxDepthReached
        distance = self.distance_between(current, goal)
        return distance
    
    def is_goal_reached(self, current, goal):
        return current == goal

class World(ElementSingleton):
    def __init__(self, program):
        super().__init__()

        self.chunks = {}
        self.program = program

        populate_block_cache()

        self.reset_rebuild()

        self.pathfinder = Pathfinder(self)

        self.neighbor_map = {}

    def gen_navmesh(self, xz_origin, scan_range=100):
        origin = None
        for i in range(scan_range):
            up = (xz_origin[0], xz_origin[1] + i, xz_origin[2])
            if self.valid_pathing_block(up):
                origin = up
                break
            down = (xz_origin[0], xz_origin[1] - i, xz_origin[2])
            if self.valid_pathing_block(down):
                origin = down
                break
        if origin:
            remaining = [origin]
            seen = set(remaining)
            while len(remaining):
                neighbors = self.path_neighbors(remaining[0])
                self.neighbor_map[remaining[0]] = neighbors
                for neighbor in neighbors:
                    if neighbor not in seen:
                        remaining.append(neighbor)
                        seen.add(neighbor)
                remaining.pop(0)
        
        # add diagonals on level ground
        for pos in list(self.neighbor_map):
            valid_diagonals = []
            for diagonal in DIAGONAL_CHECKS:
                world_diag = (pos[0] + diagonal[0], pos[1] + diagonal[1], pos[2] + diagonal[2])
                if world_diag in self.neighbor_map:
                    if any([(pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2]) in self.neighbor_map[pos] for offset in DIAGONAL_CHECKS[diagonal]]):
                        valid_diagonals.append(world_diag)
            self.neighbor_map[pos] += valid_diagonals

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
        
    def valid_pathing_block(self, world_pos):
        base = self.get_block(world_pos)
        mid = self.get_block((world_pos[0], world_pos[1] + 1, world_pos[2]))
        top = self.get_block((world_pos[0], world_pos[1] + 2, world_pos[2]))
        floor = self.get_block((world_pos[0], world_pos[1] - 1, world_pos[2]))
        if floor and not (base or mid or top):
            return True
        
    def find_valid_path_destination(self, world_pos):
        if self.valid_pathing_block(world_pos):
            return world_pos
        below = (world_pos[0], world_pos[1] - 1, world_pos[2])
        if self.valid_pathing_block(below):
            return below
        above = (world_pos[0], world_pos[1] + 1, world_pos[2])
        if self.valid_pathing_block(above):
            return above
        neighbors = self.path_neighbors(world_pos)
        if len(neighbors):
            return neighbors[0]
        
    def lookup_neighbors(self, world_pos):
        if world_pos in self.neighbor_map:
            return self.neighbor_map[world_pos]
        return []
        
    def path_neighbors(self, world_pos):
        blocks = []
        for offset in VALID_MOVEMENT_DIRECTIONS:
            base_pos = (world_pos[0] + offset[0], world_pos[1] + offset[1], world_pos[2] + offset[2])
            if self.valid_pathing_block(base_pos):
                blocks.append(base_pos)
        return blocks
    
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
    
    def world_to_block(self, world_pos):
        return tuple(int(world_pos[i] // BLOCK_SCALE) for i in range(3))
    
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