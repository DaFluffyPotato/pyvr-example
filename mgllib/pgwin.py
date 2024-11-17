import time
import sys

import pygame

from .mgl import MGL
from .elements import ElementSingleton

class PygameWindow(ElementSingleton):
    def __init__(self, application, dimensions=(800, 800), fps=165, title='Pygame Window'):
        super().__init__()
        
        self.application = application
        self.dimensions = dimensions
        self.fps = fps

        self.screen = pygame.display.set_mode(self.dimensions, pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()

        self.dt = 0.1
        self.last_frame = time.time()

    def run(self):
        self.application.init_mgl()
        while True:
            self.application.update()
            self.cycle()

    def cycle(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()
        self.clock.tick(self.fps)

        new_time = time.time()
        self.dt = min(new_time - self.last_frame, 0.1)
        self.last_frame = new_time

class XRPygameWindow(ElementSingleton):
    def __init__(self, application, dimensions=(800, 800), fps=165):
        super().__init__()
        
        self.application = application
        self.dimensions = dimensions
        self.fps = fps

        self.screen = pygame.display.set_mode(self.dimensions)

        self.window_mgl = MGL()

    def cycle(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()

        self.screen.fill((128, 128, 128))

