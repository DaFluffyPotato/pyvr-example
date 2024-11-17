import moderngl

TEXTURE_CATEGORIES = ['texture', 'normal', 'metallic']

class VAOs:
    def __init__(self, program, vaos):
        self.program = program
        self.vaos = vaos

    def update(self, uniforms={}):
        tex_id = 0
        uniform_list = list(self.program)
        for uniform in uniforms:
            if uniform in uniform_list:
                if type(uniforms[uniform]) == moderngl.Texture:
                    # bind tex to next ID
                    uniforms[uniform].use(tex_id)
                    # specify tex ID as uniform target
                    self.program[uniform].value = tex_id
                    tex_id += 1
                else:
                    self.program[uniform].value = uniforms[uniform]

    def render(self, uniforms={}, mode=moderngl.TRIANGLES):
        self.update(uniforms=uniforms)
        for vao in self.vaos:
            vao.render(mode=mode)

class TexturedVAOs(VAOs):
    def __init__(self, program, vaos):
        super().__init__(program, vaos)

        self.textures = {}
        self.texture_flags = 1

    def bind_texture(self, texture, category):
        if category in TEXTURE_CATEGORIES:
            self.texture_flags |= (2 ** TEXTURE_CATEGORIES.index(category))
            self.textures[category] = texture

    def render(self, uniforms={}, mode=moderngl.TRIANGLES):
        for category in self.textures:
            tex = self.textures[category]
            if category == 'texture':
                category = 'tex'
            else:
                category = category + '_tex'
            uniforms[category] = tex
        uniforms['texture_flags'] = self.texture_flags
        super().render(uniforms=uniforms, mode=mode)
