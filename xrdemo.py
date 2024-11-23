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
from mgllib.skybox import Skybox
from mgllib.vritem import Knife, M4

class Demo(ElementSingleton):
    def __init__(self):
        super().__init__()

        self.window = XRWindow(self, (1280, 720))

        self.pg_window = None

    def init_mgl(self):
        self.mgl = MGL()

        self.main_shader = self.mgl.program('data/shaders/default.vert', 'data/shaders/default.frag')
        self.tracer_shader = self.mgl.program('data/shaders/default.vert', 'data/shaders/tracer.frag')

        self.hand_obj = OBJ('data/models/hand/hand.obj', self.main_shader, centered=True)

        self.world = World(self.main_shader)

        self.skybox = Skybox('data/textures/skybox', self.mgl.program('data/shaders/skybox.vert', 'data/shaders/skybox.frag'))

        self.knife_res = OBJ('data/models/knife/knife.obj', self.main_shader, centered=False)
        self.m4_res = OBJ('data/models/m4/m4.obj', self.main_shader, centered=False)

        self.tracer_res = OBJ('data/models/tracer/tracer.obj', self.tracer_shader, centered=False, simple=True)
        
        self.items = [Knife(self.knife_res, (0, 1, i - 5)) for i in range(10)]
        self.items.append(M4(self.m4_res, (7, 1, 0)))

        self.tracers = []

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

        self.hand_entity = self.hand_obj.new_entity()
        self.hand_entity.transform.scale = [0.06, 0.06, 0.06]

        self.e['XRCamera'].light_pos = [0.5, 1, 1]

        self.player = PlayerBody()

    def run(self):
        self.window.run()

    def single_update(self):
        self.player.cycle()
        for item in self.items:
            for hand in self.player.hands:
                item.handle_interactions(hand)
            item.update()

        for tracer in list(self.tracers):
            kill = tracer.update()
            if kill:
                self.tracers.remove(tracer)

    def update(self, view_index):
        if view_index == 0:
            self.single_update()

        self.e['XRCamera'].cycle()

        self.skybox.render(self.e['XRCamera'])

        for item in self.items:
            item.render(self.e['XRCamera'])

        for tracer in self.tracers:
            tracer.render(self.e['XRCamera'])

        for i, hand in enumerate(self.player.hands):
            self.hand_entity.transform.quaternion = glm.quat(hand.aim_rot[3], *(hand.aim_rot[:3])) * glm.quat(glm.rotate(math.pi / 2, glm.vec3(0, 1, 0)))
            if hand.interacting and (hand.interacting.parent.alt_grip == hand.interacting):
                self.hand_entity.transform.pos = hand.interacting.world_pos
            else:    
                self.hand_entity.transform.pos = list(hand.pos)
            self.hand_entity.render(self.e['XRCamera'])

        self.world.render(self.e['XRCamera'])

Demo().run()
