from PIL import Image
import moderngl
import pygame

from .util import read_f
from .elements import ElementSingleton
from .const import SKYBOX_DIRECTIONS

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
    
    def load_cubemap(self, base_path):
        images = []
        for direction in SKYBOX_DIRECTIONS:
            images.append(Image.open(f'{base_path}_{direction}.png').convert('RGBA'))

        skybox_data = b''
        for img in images:
            skybox_data += img.tobytes()

        return self.ctx.texture_cube(images[0].size, components=4, data=skybox_data)
    
    def tx2pg(self, tex):
        surf = pygame.image.frombytes(tex.read(), tex.size, 'RGBA', True)
        return surf
    
    def pg2tx(self, surf, swizzle=True):
        channels = 4
        new_tex = self.ctx.texture(surf.get_size(), channels)
        new_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        if swizzle:
            new_tex.swizzle = 'BGRA'
        new_tex.write(surf.get_view('1'))
        return new_tex