CHUNK_SIZE = 16
BLOCK_SCALE = 0.75

BASE_DECOR_FORMAT = ['uv', 'normal', 'vert']
DECOR_FORMAT = ['2f 3f 3f 3f', 'uv', 'normal', 'vert', 'origin']

class MaxDepthReached(Exception):
    pass