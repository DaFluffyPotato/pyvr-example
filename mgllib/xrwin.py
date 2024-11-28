import gc
import time

import glm
import numpy as np
from pympler import tracker
from OpenGL import GL
import xr

from .xr_plugin_hack import hack_pyopenxr
from .xrinput import XRInput
from .elements import ElementSingleton

class XRCamera(ElementSingleton):
    def __init__(self, pos=[0, 0, 1], target=[0, 0, 0], up=[0, 1, 0]):
        super().__init__()
        self.pos = list(pos)
        self.target = list(target)
        self.up = list(up)

        self.matrix = None
        self.prepped_matrix = None
        self.sky_matrix = None

        self.world_matrix = None
        self.world_rotation = [0, 0, 0]

        self.light_pos = [0.1, 1, 0.2]
        self.eye_pos = [0, 0, 0]

    def cycle(self):
        if type(self.world_matrix) != type(None):
            # take original view matrix -> remove head offset -> apply world transform
            self.prepped_matrix = (self.world_matrix.T @ self.e['XRInput'].head_transform @ np.reshape(self.matrix.as_numpy(), (4, 4))).flatten()

            # hacked eye pos (not accurate for separate eye positions; just based on head pos)
            # only used for specular
            self.eye_pos = [self.e['Demo'].player.world_pos.pos[0], self.pos[1] + self.e['Demo'].player.world_pos.pos[1], self.e['Demo'].player.world_pos.pos[2]]
        else:
            self.prepped_matrix = self.matrix.as_numpy()
            self.eye_pos = list(self.pos)

        self.sky_matrix = self.matrix.as_numpy()

class XRState(ElementSingleton):
    def __init__(self):
        super().__init__()

        self.camera = XRCamera()
        self.orientation = None

class XRWindow(ElementSingleton):
    def __init__(self, application, dimensions=(800, 800), fps=165, title='VR Test'):
        super().__init__()
        
        self.application = application
        self.dimensions = dimensions
        self.fps = fps

        self.dt = 0.1
        self.last_frame = time.time()

        self.xrstate = XRState()

        self.title = title

        self.input = XRInput()

        self.motion_flags = [0, 1, 0]

        #self.mem_check = tracker.SummaryTracker()

    def run(self):
        hack_pyopenxr(self.dimensions, self.title)

        with xr.ContextObject(
            instance_create_info=xr.InstanceCreateInfo(
                enabled_extension_names=[
                    # A graphics extension is mandatory (without a headless extension)
                    xr.KHR_OPENGL_ENABLE_EXTENSION_NAME,
                ],
            ),
        ) as context:
            self.application.init_mgl()

            self.input.init(context)

            for frame_index, frame_state in enumerate(context.frame_loop()):
                new_time = time.time()
                self.dt = min(new_time - self.last_frame, 0.1)
                self.last_frame = new_time

                self.input.update(frame_state)

                for view_index, view in enumerate(context.view_loop(frame_state)):
                    projection = xr.Matrix4x4f.create_projection_fov(
                        graphics_api=xr.GraphicsAPI.OPENGL,
                        fov=view.fov,
                        near_z=0.03,
                        far_z=200.0
                    )

                    to_view = xr.Matrix4x4f.create_translation_rotation_scale(
                        translation=view.pose.position,
                        rotation=view.pose.orientation,
                        scale=(1.0, 1.0, 1.0),
                    )
                    new_view = xr.Matrix4x4f.invert_rigid_body(to_view)

                    GL.glClearColor(0.5, 0.5, 0.5, 1)
                    GL.glClearDepth(1.0)
                    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

                    xrcam = self.xrstate.camera

                    xrcam.matrix = projection @ new_view
                    xrcam.pos = list(view.pose.position[:3])

                    self.xrstate.orientation = view.pose.orientation

                    self.application.update(view_index)

                    # mirror the result to the window
                    if view_index == 0:
                        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
                        size = (context.swapchains[0].width, context.swapchains[0].height)
                        GL.glBlitFramebuffer(
                            0, 0, size[0], size[1], 0, 0,
                            1280, 720,
                            GL.GL_COLOR_BUFFER_BIT,
                            GL.GL_NEAREST
                        )
                

                #if frame_index % 600 == 0:
                #    self.mem_check.print_diff()