# This implementation is specific to Windows. See PyOpenXR's hello_xr example for a linux variation.

from OpenGL import GL, WGL
import glfw

from .elements import ElementSingleton

class XRGLFWWin(ElementSingleton):
    def __init__(self, application, dimensions=(1280, 720), fps=165):
        super().__init__()
        
        self.application = application
        self.dimensions = dimensions
        self.fps = fps

        glfw.init()
        glfw.window_hint(glfw.DOUBLEBUFFER, False)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)


        self.window = glfw.create_window(dimensions[0], dimensions[1], 'VR Mirror', None, None)
        glfw.show_window(self.window)

        '''
        glfw.make_context_current(self.window)
        glfw.show_window(self.window)
        glfw.swap_interval(0)
        glfw.focus_window(self.window)
        '''

    def cycle(self, xr_context):
        '''
        glfw.make_context_current(self.window)

        size = (xr_context.swapchains[0].width, xr_context.swapchains[0].height)

        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
        GL.glBlitFramebuffer(
            0, 0, size[0], size[1], 0, 0,
            self.dimensions[0], self.dimensions[1],
            GL.GL_COLOR_BUFFER_BIT,
            GL.GL_NEAREST
        )

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        '''

        glfw.make_context_current(self.window)
        size = (xr_context.swapchains[0].width, xr_context.swapchains[0].height)

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, xr_context.graphics.swapchain_framebuffer)
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
        GL.glBlitFramebuffer(
            0, 0, size[0], size[1], 0, 0,
            self.dimensions[0], self.dimensions[1],
            GL.GL_COLOR_BUFFER_BIT,
            GL.GL_NEAREST
        )

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        xr_context.graphics.make_current()