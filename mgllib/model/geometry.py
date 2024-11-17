from array import array

class VertexBuffer:
    def __init__(self, ctx, data, fmt):
        self.ctx = ctx
        self.buffer = ctx.buffer(data=array('f', data))
        self.fmt = fmt

class FrozenGeometry:
    def __init__(self, src, buffers):
        self.bounds = src.bounds
        self.buffers = buffers

    def generate_vaos(self, program, fmt):
        ctx = None
        vaos = []
        for buffer in self.buffers:
            ctx = self.buffers[buffer].ctx
            datatypes = ' '.join([fmt.datatypes[group] for group in self.buffers[buffer].fmt])
            params = [(self.buffers[buffer].buffer, datatypes, *self.buffers[buffer].fmt)]
            vaos.append(ctx.vertex_array(program, params))
        return vaos

class Geometry:
    def __init__(self, materials):
        super().__init__()

        self.materials = materials
    
    def get_bounds(self):
        self.bounds = None
        if len(self.materials):
            first_material = self.materials[list(self.materials)[0]]
            if len(first_material):
                dimensions = len(first_material[0]['vert'])
                bounds = [(9999999, -9999999)] * dimensions
                for vertices in self.materials.values():
                    for vert in vertices:
                        for i in range(dimensions):
                            bounds[i] = (min(bounds[i][0], vert['vert'][i]), max(bounds[i][1], vert['vert'][i]))
        
                self.bounds = bounds

    def get_center(self):
        self.get_bounds()
        if self.bounds:
            center = tuple((dim[1] - dim[0]) * 0.5 + dim[0] for dim in self.bounds)
            return center
            
    def center(self, rescale=False):
        old_center = self.get_center()
        if old_center:
            largest_span = max(dim[1] - dim[0] for dim in self.bounds)
            for vertices in self.materials.values():
                for i in range(len(vertices)):
                    if rescale:
                        vertices[i]['vert'] = tuple((vertices[i]['vert'][j] - old_center[j]) / largest_span * 2 for j in range(len(old_center)))
                    else:
                        vertices[i]['vert'] = tuple(vertices[i]['vert'][j] - old_center[j] for j in range(len(old_center)))
            self.get_bounds()
    
    def build(self, ctx, program, fmt):
        buffers = {}
        for material in self.materials:
            if len(self.materials[material]):
                material_fmt = list(self.materials[material][0])
                material_data = []
                for vertex in self.materials[material]:
                    for group in material_fmt:
                        for v in vertex[group]:
                            material_data.append(v)
                buffers[material] = VertexBuffer(ctx, material_data, material_fmt)
        return FrozenGeometry(self, buffers).generate_vaos(program, fmt)


