from PIL import Image
import moderngl
import pygame

from .util import read_f
from .elements import ElementSingleton

class MGL(ElementSingleton):
    def __init__(self, share=False):
        super().__init__()

        self.ctx = moderngl.create_context(share=share, require=450)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)

    def program(self, vert_path, frag_path):
        return self.ctx.program(vertex_shader=read_f(vert_path), fragment_shader=read_f(frag_path))
    
    def load_texture(self, path, swizzle=True):
        img = Image.open(path).convert('RGBA').transpose(Image.FLIP_TOP_BOTTOM)
        return self.ctx.texture(img.size, components=4, data=img.tobytes())
    
    def tx2pg(self, tex):
        surf = pygame.image.frombytes(tex.read(), tex.size, 'RGBA', True)
        return surf