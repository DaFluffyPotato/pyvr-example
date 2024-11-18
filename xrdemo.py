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
from mgllib.world.block import StandaloneBlock

class Demo(ElementSingleton):
    def __init__(self):
        super().__init__()

        self.window = XRWindow(self, (1280, 720))

        self.pg_window = None

    def init_mgl(self):
        self.mgl = MGL()

        self.journey_obj = OBJ('data/models/journey/journey.obj', self.mgl.program('data/shaders/default.vert', 'data/shaders/default.frag'), centered=True)

        self.ak_obj = OBJ('data/models/ak47/ak47.obj', self.mgl.program('data/shaders/default.vert', 'data/shaders/default.frag'), centered=True)

        self.shiba_obj = OBJ('data/models/shiba/shiba.obj', self.mgl.program('data/shaders/default.vert', 'data/shaders/default.frag'), centered=True)

        self.block = StandaloneBlock(self.mgl.program('data/shaders/default.vert', 'data/shaders/default.frag'), block_id='chiseled_stone')

        self.test_entity = self.journey_obj.new_entity()
        self.test_entity_2 = self.ak_obj.new_entity()
        self.test_entity_3 = self.shiba_obj.new_entity()

        self.e['XRCamera'].light_pos = [0.5, 1, 1]

        self.player = PlayerBody()

    def run(self):
        self.window.run()

    def update(self, view_index):
        if view_index == 0:
            self.player.cycle()
        self.e['XRCamera'].cycle()

        self.test_entity.render(self.e['XRCamera'])

        self.test_entity_2.transform.quaternion = None
        self.test_entity_2.transform.pos = [2.5, 0.0, 0.0]
        self.test_entity_2.transform.scale = [0.5, 0.5, 0.5]
        self.test_entity_2.render(self.e['XRCamera'])

        self.test_entity_3.transform.quaternion = None
        self.test_entity_3.transform.pos = [-2.5, 0.0, 0.0]
        self.test_entity_3.transform.scale = [0.3, 0.3, 0.3]
        self.test_entity_3.render(self.e['XRCamera'])

        for i, hand in enumerate(self.player.hands):
            self.test_entity_2.transform.quaternion = glm.quat(hand.aim_rot[3], *(hand.aim_rot[:3])) * glm.quat(glm.rotate(math.pi / 2, glm.vec3(0, 1, 0)))
            self.test_entity_2.transform.pos = list(hand.pos)
            self.test_entity_2.transform.scale = [0.5, 0.5, 0.5]
            self.test_entity_2.render(self.e['XRCamera'])

        self.block.render(self.e['XRCamera'])

Demo().run()
