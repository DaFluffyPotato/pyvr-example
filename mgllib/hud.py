from array import array

import moderngl

from .elements import ElementSingleton

class HUD(ElementSingleton):
    def __init__(self):
        super().__init__()

        self.ctx = self.e['MGL'].ctx

        self.program = self.e['MGL'].program('data/shaders/quad.vert', 'data/shaders/hud.frag')

        self.quad_buffer = self.ctx.buffer(data=array('f', [
            # position (x, y) , texture coordinates (x, y)
            -1.0, 1.0, 0.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 0.0,
            1.0, -1.0, 1.0, 1.0,
        ]))

        self.quad_vao = self.ctx.vertex_array(self.program, [(self.quad_buffer, '2f 2f', 'vert', 'texcoord')])

        self.blood_flash = 0

    def flash(self):
        self.blood_flash = 0.5

    def update(self):
        self.blood_flash = max(0, self.blood_flash - self.e['XRWindow'].dt)

    def render(self):
        self.program['blood_flash'].value = self.blood_flash

        self.e['MGL'].ctx.screen.depth_mask = False
        self.quad_vao.render(mode=moderngl.TRIANGLE_STRIP)
        self.e['MGL'].ctx.screen.depth_mask = True