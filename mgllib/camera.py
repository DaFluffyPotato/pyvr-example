from .mat3d import prep_mat, perspective_matrix, lookat_matrix

class Camera:
    def __init__(self, pos=[0, 0, 1], target=[0, 0, 0], up=[0, 1, 0]):
        self.pos = list(pos)
        self.target = list(target)
        self.up = list(up)
        self.update_matrix()

        self.light_pos = [0, 1, 0]

    def lookat(self, target):
        self.target = list(target[:3])
        self.update_matrix()

    def move(self, movement):
        for i in range(3):
            self.pos[i] += movement[i]
        self.update_matrix()

    def set_pos(self, pos):
        self.pos = list(pos)
        self.update_matrix()
    
    def update_matrix(self):
        view_matrix = lookat_matrix(self.pos, self.target, self.up)
        projection_matrix = perspective_matrix(80, 1.0, 0.001, 200)
        self.matrix = projection_matrix * view_matrix
        self.prepped_matrix = prep_mat(self.matrix)