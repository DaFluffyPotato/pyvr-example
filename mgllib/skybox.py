from array import array

import moderngl

from .elements import ElementSingleton
from .mat3d import Transform3D

SKYBOX_VERTICES = [
    -1.0,  1.0, -1.0,
    -1.0, -1.0, -1.0,
     1.0, -1.0, -1.0,
     1.0, -1.0, -1.0,
     1.0,  1.0, -1.0,
    -1.0,  1.0, -1.0,

    -1.0, -1.0,  1.0,
    -1.0, -1.0, -1.0,
    -1.0,  1.0, -1.0,
    -1.0,  1.0, -1.0,
    -1.0,  1.0,  1.0,
    -1.0, -1.0,  1.0,

     1.0, -1.0, -1.0,
     1.0, -1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0, -1.0,
     1.0, -1.0, -1.0,

    -1.0, -1.0,  1.0,
    -1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0, -1.0,  1.0,
    -1.0, -1.0,  1.0,

    -1.0,  1.0, -1.0,
     1.0,  1.0, -1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
    -1.0,  1.0,  1.0,
    -1.0,  1.0, -1.0,

    -1.0, -1.0, -1.0,
    -1.0, -1.0,  1.0,
     1.0, -1.0, -1.0,
     1.0, -1.0, -1.0,
    -1.0, -1.0,  1.0,
     1.0, -1.0,  1.0
]

class Skybox(ElementSingleton):
    def __init__(self, path, program):
        super().__init__()

        self.cubemap = self.e['MGL'].load_cubemap(path)
        #self.cubemap.filter = moderngl.NEAREST, moderngl.NEAREST
        self.program = program
        self.world_transform = Transform3D()

        ctx = self.e['MGL'].ctx
        buffer = ctx.buffer(data=array('f', SKYBOX_VERTICES))
        self.vao = ctx.vertex_array(self.program, [(buffer, '3f', 'apos')])

    def update(self, uniforms={}):
        tex_id = 1
        uniform_list = list(self.program)
        for uniform in uniforms:
            if uniform in uniform_list:
                if type(uniforms[uniform]) == moderngl.Texture:
                    # bind tex to next ID
                    uniforms[uniform].use(tex_id)
                    # specify tex ID as uniform target
                    self.program[uniform].value = tex_id
                    tex_id += 1
                else:
                    self.program[uniform].value = uniforms[uniform]

    def render(self, camera, uniforms={}, mode=moderngl.TRIANGLES):
        self.world_transform.pos = list(camera.pos)
        self.world_transform.rotation = [-v for v in camera.world_rotation]
        self.program['world_transform'] = self.world_transform.matrix
        self.program['view_projection'] = camera.sky_matrix
        tex_id = 0
        self.cubemap.use(tex_id)
        self.program['skybox'] = tex_id

        self.update(uniforms=uniforms)
        
        self.e['MGL'].ctx.screen.depth_mask = False

        self.vao.render(mode=mode)

        self.e['MGL'].ctx.screen.depth_mask = True