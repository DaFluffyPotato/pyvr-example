import ctypes
import os
import sys

import pygame

CONTEXT_VERSION_MAJOR = 0
CONTEXT_VERSION_MINOR = 0
DOUBLEBUFFER = 0
OPENGL_CORE_PROFILE = 0
OPENGL_PROFILE = 0
VISIBLE = 0

class DetectContext:
    def __init__(self):
        ctypes.windll.opengl32.wglGetCurrentDC.restype = ctypes.c_void_p
        ctypes.windll.opengl32.wglGetCurrentContext.restype = ctypes.c_void_p
        self.hdc = ctypes.windll.opengl32.wglGetCurrentDC()
        self.hglrc = ctypes.windll.opengl32.wglGetCurrentContext()

    def make_current(self):
        ctypes.windll.opengl32.wglMakeCurrent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        ctypes.windll.opengl32.wglMakeCurrent(self.hdc, self.hglrc)

class g:
    ctx = None

def create_window(*args, **kwargs):
    os.environ['SDL_WINDOWS_DPI_AWARENESS'] = 'permonitorv2'

    pygame.init()
    pygame.display.set_mode((1280, 720), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=False)
    g.ctx = DetectContext()
    return 1

def make_context_current(*args, **kwargs):
    g.ctx.make_current()

def poll_events(*args, **kwargs):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

def destroy_window(*args, **kwargs):
    pass

def init(*args, **kwargs):
    return 1

def swap_interval(*args, **kwargs):
    pass

def terminate(*args, **kwargs):
    pass

def window_hint(*args, **kwargs):
    pass

def window_should_close(*args, **kwargs):
    pass