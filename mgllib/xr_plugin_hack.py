import ctypes
import platform

from OpenGL import GL
if platform.system() == "Windows":
    from OpenGL import WGL
    from xr.platform.windows import *
elif platform.system() == "Linux":
    from OpenGL import GLX
    from xr.platform.linux import *
import glfw

from xr.opengl_graphics import OpenGLGraphics
from xr.enums import *
from xr.exception import *
from xr.typedefs import *
from xr.functions import *

def hack_pyopenxr(window_size, window_title='VR Test'):
    # hack the default rendering plugin so we don't have to write a custom one
    def opengl_graphics_init(self, instance, system, title='glfw OpenGL window'):
        if not glfw.init():
            raise XrException("GLFW initialization failed")
        self.window_size = window_size
        self.pxrGetOpenGLGraphicsRequirementsKHR = ctypes.cast(
            get_instance_proc_addr(
                instance=instance,
                name="xrGetOpenGLGraphicsRequirementsKHR",
            ),
            PFN_xrGetOpenGLGraphicsRequirementsKHR
        )
        self.graphics_requirements = GraphicsRequirementsOpenGLKHR()
        result = self.pxrGetOpenGLGraphicsRequirementsKHR(
            instance,
            system,
            ctypes.byref(self.graphics_requirements))
        result = check_result(Result(result))
        if result.is_exception():
            raise result
        glfw.window_hint(glfw.DOUBLEBUFFER, False)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(*self.window_size, window_title, None, None)
        if self.window is None:
            raise XrException("Failed to create GLFW window")
        glfw.make_context_current(self.window)
        # Attempt to disable vsync on the desktop window, or
        # it will interfere with the OpenXR frame loop timing
        glfw.swap_interval(0)
        self.graphics_binding = None
        if platform.system() == "Windows":
            self.graphics_binding = GraphicsBindingOpenGLWin32KHR()
            self.graphics_binding.h_dc = WGL.wglGetCurrentDC()
            self.graphics_binding.h_glrc = WGL.wglGetCurrentContext()
        elif platform.system() == "Linux":
            drawable = GLX.glXGetCurrentDrawable()
            context = GLX.glXGetCurrentContext()
            display = GLX.glXGetCurrentDisplay()
            self.graphics_binding = GraphicsBindingOpenGLXlibKHR(
                x_display=display,
                glx_drawable=drawable,
                glx_context=context,
            )
        else:
            raise NotImplementedError
        self.swapchain_framebuffer = None
        self.color_to_depth_map = {}

    # the cursed override
    OpenGLGraphics.__init__ = opengl_graphics_init