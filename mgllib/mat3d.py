import numpy as np
import glm

class Transform3D:
    def __init__(self, swap_rot_order=True):
        self.pos = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [1, 1, 1]
        self.swap_rot_order = swap_rot_order
        self.quaternion = None

    @property
    def translate_matrix(self):
        return glm.translate(glm.vec3(self.pos))

    @property
    def rotation_matrix(self):
        if self.quaternion:
            return glm.mat4(self.quaternion)
        return euler_rotate_matrix(self.rotation)

    @property
    def scale_matrix(self):
        return glm.scale(glm.vec3(self.scale))

    @property
    def matrix(self):
        return prep_mat(self.glmmatrix)
        
    @property
    def glmmatrix(self):
        if self.swap_rot_order:
            return self.translate_matrix * self.rotation_matrix * self.scale_matrix
        else:
            return self.rotation_matrix * self.translate_matrix * self.scale_matrix

    @property
    def npmatrix(self):
        if self.swap_rot_order:
            return np.array((self.translate_matrix * self.rotation_matrix * self.scale_matrix).to_list()).T
        else:
            return np.array((self.rotation_matrix * self.translate_matrix * self.scale_matrix).to_list()).T
        
def quat_to_mat(x, y, z, w):
    return np.array(glm.mat4(glm.quat(w, x, y, z)))

def flatten(l):
    return [item for sublist in l for item in sublist]

def perspective_matrix(fovy, ratio, znear, zfar):
    return glm.perspective(fovy, ratio, znear, zfar)

def lookat_matrix(eye, target, up):
    return glm.lookAt(glm.vec3(*eye), glm.vec3(*target), glm.vec3(*up))

def prep_mat(matrix):
    return tuple(flatten(matrix.to_tuple()))

def euler_rotate_matrix(angles):
    x_mat = glm.rotate(angles[0], glm.vec3(1, 0, 0))
    y_mat = glm.rotate(angles[1], glm.vec3(0, 1, 0))
    z_mat = glm.rotate(angles[2], glm.vec3(0, 0, 1))
    return x_mat * y_mat * z_mat

def change_basis_mat(from_basis, to_basis):
    return np.matmul(np.linalg.inv(np.array(from_basis)), np.array(to_basis))

def mat3_to_mat4(mat3):
    new_mat = np.identity(4)
    new_mat[:3, :3] = mat3
    return new_mat

def unflatten_matrix(matrix):
    if len(matrix) == 3 * 3:
        return np.array(matrix).reshape(-1, 3)
    elif len(matrix) == 4 * 4:
        return np.array(matrix).reshape(-1, 4)

# https://math.stackexchange.com/questions/237369/given-this-transformation-matrix-how-do-i-decompose-it-into-translation-rotati
def extract_rotation(mat3):
    scale = [np.linalg.norm(np.array([mat3[i][0], mat3[i][1], mat3[i][2]])) for i in range(3)]
    rotation_mat = np.array([[mat3[i][0] / scale[0], mat3[i][1] / scale[1], mat3[i][2] / scale[2]] for i in range(3)])
    return rotation_mat