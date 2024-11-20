import sys
import time
import math

import pygame
from OpenGL import GL
import glm

from mgllib.xrwin import XRWindow
from mgllib.glfwwin import XRGLFWWin
from mgllib.mgl import MGL
from mgllib.elements import ElementSingleton
from mgllib.model.obj import OBJ
from mgllib.camera import Camera
from mgllib.player_body import PlayerBody
from mgllib.world.world import World

class Demo(ElementSingleton):
    def __init__(self):
        super().__init__()

        self.window = XRWindow(self, (1280, 720))

        self.pg_window = None

    def init_mgl(self):
        self.mgl = MGL()

        self.ak_obj = OBJ('data/models/ak47/ak47.obj', self.mgl.program('data/shaders/default.vert', 'data/shaders/default.frag'), centered=True)

        self.world = World(self.mgl.program('data/shaders/default.vert', 'data/shaders/default.frag'))

        for x in range(32):
            for z in range(32):
                self.world.add_block('grass', (x - 16, -1, z - 16), rebuild=False)
        
        for y in range(4):
            self.world.add_block('chiseled_stone', (1, y, 1), rebuild=False)
            self.world.add_block('chiseled_stone', (-1, y, 1), rebuild=False)
            self.world.add_block('chiseled_stone', (-1, y, -1), rebuild=False)
            self.world.add_block('chiseled_stone', (1, y, -1), rebuild=False)
            
            t = 'log'
            if y == 3:
                t = 'chiseled_stone'
                self.world.add_block('chiseled_stone', (1, y, 0), rebuild=False)
                self.world.add_block('chiseled_stone', (0, y, 1), rebuild=False)
                self.world.add_block('chiseled_stone', (-1, y, 0), rebuild=False)
                self.world.add_block('chiseled_stone', (0, y, -1), rebuild=False)
            self.world.add_block(t, (2, y, 2), rebuild=False)
            self.world.add_block(t, (-2, y, 2), rebuild=False)
            self.world.add_block(t, (-2, y, -2), rebuild=False)
            self.world.add_block(t, (2, y, -2), rebuild=False)
        
        self.world.add_block('log', (4, 0, 0), rebuild=False)

        self.world.rebuild()

        self.world.add_block('log', (5, 0, 0), rebuild=True)

        self.test_entity_2 = self.ak_obj.new_entity()

        self.e['XRCamera'].light_pos = [0.5, 1, 1]

        self.player = PlayerBody()

    def run(self):
        self.window.run()

    def update(self, view_index):
        if view_index == 0:
            self.player.cycle()
        self.e['XRCamera'].cycle()

        for i, hand in enumerate(self.player.hands):
            self.test_entity_2.transform.quaternion = glm.quat(hand.aim_rot[3], *(hand.aim_rot[:3])) * glm.quat(glm.rotate(math.pi / 2, glm.vec3(0, 1, 0)))
            self.test_entity_2.transform.pos = list(hand.pos)
            self.test_entity_2.transform.scale = [0.5, 0.5, 0.5]
            self.test_entity_2.render(self.e['XRCamera'])

        self.world.render(self.e['XRCamera'])

Demo().run()
