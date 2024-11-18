# UV mappings (by index)
# +x +y
# +x +z
# +z +y
# y is always second so up on the texture is up in the world

# counterclockwise perspective is front

def gen_pane(base, scale, normal, uv_base, uv_scale=(1, 1), flip=False):
    offset_1 = (0, 0, 0)
    offset_2 = (0, 0, 0)

    if not scale[0]:
        offset_2 = (0, scale[1], 0, 0, uv_scale[1])
        offset_1 = (0, 0, scale[2], uv_scale[0], 0)
    if not scale[1]:
        offset_2 = (0, 0, scale[2], 0, uv_scale[1])
        offset_1 = (scale[0], 0, 0, uv_scale[0], 0)
    if not scale[2]:
        offset_1 = (0, scale[1], 0, 0, uv_scale[1])
        offset_2 = (scale[0], 0, 0, uv_scale[0], 0)
    
    if flip:
        offset_1, offset_2 = offset_2, offset_1

    # notes are for +x +y (as if just a square in 2D)
    return [
        # bottom left triangle
        (base[0], base[1], base[2], uv_base[0], uv_base[1], *normal), # bottom left
        (base[0] + offset_1[0], base[1] + offset_1[1], base[2] + offset_1[2], uv_base[0] + offset_1[3], uv_base[1] + offset_1[4], *normal), # bottom right 
        (base[0] + offset_2[0], base[1] + offset_2[1], base[2] + offset_2[2], uv_base[0] + offset_2[3], uv_base[1] + offset_2[4], *normal), # top left

        # top right triangle
        (base[0] + offset_1[0] + offset_2[0], base[1] + offset_1[1] + offset_2[1], base[2] + offset_1[2] + offset_2[2], uv_base[0] + offset_1[3] + offset_2[3], uv_base[1] + offset_1[4] + offset_2[4], *normal), # top right
        (base[0] + offset_2[0], base[1] + offset_2[1], base[2] + offset_2[2], uv_base[0] + offset_2[3], uv_base[1] + offset_2[4], *normal), # top left
        (base[0] + offset_1[0], base[1] + offset_1[1], base[2] + offset_1[2], uv_base[0] + offset_1[3], uv_base[1] + offset_1[4], *normal), # bottom right
    ]

def tuple_sum(t1, t2):
    return tuple([t1[i] + t2[i] for i in range(len(t1))])

def gen_cube(uv_base, scale=1, uv_scale=(1, 1)):
    # +z in OpenGL is towards the screen
    # consider keeping it so you flip the faces that use the (0, 0, 0) coord?
    # front face (+1 z) should ideally not need a flip
    # see grass texture to determine uv offsets

    bias = 0.00001
    uv_base = tuple_sum(uv_base, (bias, bias))
    uv_scale = tuple_sum(uv_scale, (-bias * 2, -bias * 2))

    # V3N3T2
    points = [
        *gen_pane((0, 0, scale), (scale, scale, 0), (0, 0, 1), tuple_sum(uv_base, (uv_scale[0] * 2, 0)), uv_scale=uv_scale, flip=True), # front
        *gen_pane((0, 0, 0), (scale, scale, 0), (0, 0, -1), tuple_sum(uv_base, (uv_scale[0] * 3, 0)), uv_scale=uv_scale), # back
        *gen_pane((scale, 0, 0), (0, scale, scale), (1, 0, 0), tuple_sum(uv_base, (uv_scale[0] * 4, 0)), uv_scale=uv_scale, flip=True), # right
        *gen_pane((0, 0, 0), (0, scale, scale), (-1, 0, 0), tuple_sum(uv_base, (uv_scale[0] * 5, 0)), uv_scale=uv_scale), # left
        *gen_pane((0, scale, 0), (scale, 0, scale), (0, 1, 0), tuple_sum(uv_base, (uv_scale[0] * 0, 0)), uv_scale=uv_scale, flip=True), # top
        *gen_pane((0, 0, 0), (scale, 0, scale), (0, -1, 0), tuple_sum(uv_base, (uv_scale[0] * 1, 0)), uv_scale=uv_scale), # bottom
    ]

    return points