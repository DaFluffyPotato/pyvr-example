import os

import pywavefront
import moderngl

from .geometry import Geometry
from .vao import TexturedVAOs, TEXTURE_CATEGORIES
from .entity3d import Entity3D
from ..elements import Element

FORMAT_NAMES = {
    'T': 'uv',
    'N': 'normal',
    'V': 'vert',
}

class VertexFormat:
    def __init__(self, string):
        self.group_map = []
        self.datatypes = {}

        offset = 0
        for part in string.split('_'):
            part_id = 'unknown'
            if part[:-2] in FORMAT_NAMES:
                part_id = FORMAT_NAMES[part[:-2]]
            size = int(part[-2])
            self.group_map.append((part_id, offset, offset + size))
            self.datatypes[part_id] = part[-2:].lower()
            offset += size
        
        self.length = offset

class OBJ(Element):
    def __init__(self, path, program, centered=True, pixelated=True, simple=False, save_geometry=False, no_build=False):
        super().__init__()

        self.vao = None
        self.bounds = None
        self.save_geometry = save_geometry
        self.geometry = None
        
        self.simple = simple
        self.pixelated = pixelated
        self.no_build = no_build

        self.name = path.split('/')[-1].split('.')[0]
        
        self.load(path, program, centered=centered)

    def parse_format(self, fmt):
        parsed_format = []
        for part in fmt.split('_'):
            part_id = 'unknown'
            if part[:-2] in FORMAT_NAMES:
                part_id = FORMAT_NAMES[part[:-2]]
            for i in range(int(part[-2])):
                parsed_format.append(part_id)

    def load(self, path, program, centered=True):
        scene = pywavefront.Wavefront(path)

        matwise_verts = {}

        fmt = None
        for name, material in scene.materials.items():
            points = []

            if not len(material.vertex_format):
                continue
            fmt = VertexFormat(material.vertex_format)

            for i in range(len(material.vertices) // fmt.length):
                points.append({group[0]: tuple(material.vertices[i * fmt.length + group[1] : i * fmt.length + group[2]]) for group in fmt.group_map})

            matwise_verts[name] = points
        
        geometry = Geometry(matwise_verts)
        if centered:
            geometry.center(rescale=True)
        else:
            geometry.get_bounds()
        if fmt:
            if self.no_build:
                self.vao = TexturedVAOs(program, [], simple=self.simple)
            else:
                self.vao = TexturedVAOs(program, geometry.build(self.e['MGL'].ctx, program, fmt), simple=self.simple)
            
            base_path = '/'.join(path.split('/')[:-1])
            folder_contents = os.listdir(base_path)
            for file in folder_contents:
                if file.split('.')[-1] == 'png':
                    file_suffix = file.split('_')[-1].split('.')[0]
                    if file_suffix in TEXTURE_CATEGORIES:
                        tex = self.e['MGL'].load_texture(base_path + '/' + file)
                        if self.pixelated:
                            tex.filter = moderngl.NEAREST, moderngl.NEAREST
                        self.vao.bind_texture(tex, file_suffix)
                    # check base texture case
                    if file.split('.')[0] == path.split('/')[-1].split('.')[0]:
                        tex = self.e['MGL'].load_texture(base_path + '/' + file)
                        if self.pixelated:
                            tex.filter = moderngl.NEAREST, moderngl.NEAREST
                        self.vao.bind_texture(tex, 'texture')
        self.bounds = geometry.bounds

        if self.save_geometry:
            self.geometry = geometry

    def new_entity(self):
        return Entity3D(self.vao)
            