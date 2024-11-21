NO_COLLISIONS = {
    'right': False,
    'left': False,
    'top': False,
    'bottom': False,
    'front': False,
    'back': False,
}

class Cuboid:
    def __init__(self, origin, size):
        self.origin = list(origin)
        self.size = list(size)

    def __str__(self):
        return f'<Cuboid origin={self.origin} size={self.size}>'
    
    def __repr__(self):
        return self.__str__()

    @property
    def right(self):
        return self.origin[0] + self.size[0] * 0.5
    
    def set_right(self, value):
        self.origin[0] = value - self.size[0] * 0.5
    
    @property
    def left(self):
        return self.origin[0] - self.size[0] * 0.5
    
    def set_left(self, value):
        self.origin[0] = value + self.size[0] * 0.5
    
    @property
    def top(self):
        return self.origin[1] + self.size[1] * 0.5
    
    def set_top(self, value):
        self.origin[1] = value - self.size[1] * 0.5
    
    @property
    def bottom(self):
        return self.origin[1] - self.size[1] * 0.5
    
    def set_bottom(self, value):
        self.origin[1] = value + self.size[1] * 0.5
    
    @property
    def front(self):
        return self.origin[2] + self.size[2] * 0.5
    
    def set_front(self, value):
        self.origin[2] = value - self.size[2] * 0.5
    
    @property
    def back(self):
        return self.origin[2] - self.size[2] * 0.5
    
    def set_back(self, value):
        self.origin[2] = value + self.size[2] * 0.5
    
    def collidecuboid(self, cuboid):
        if ((cuboid.right > self.left) and (cuboid.left < self.right)) or ((cuboid.right < self.left) and (cuboid.left > self.right)):
            if ((cuboid.front > self.back) and (cuboid.back < self.front)) or ((cuboid.front < self.back) and (cuboid.back > self.front)):
                if ((cuboid.top > self.bottom) and (cuboid.bottom < self.top)) or ((cuboid.top < self.bottom) and (cuboid.bottom > self.top)):
                    return True
        return False
    
    def collision_check(self, blockers):
        for blocker in blockers:
            if self.collidecuboid(blocker):
                return blocker
    
    def move(self, movement, blockers):
        collisions = NO_COLLISIONS.copy()

        self.origin[0] += movement[0]
        blocker = self.collision_check(blockers)
        if blocker:
            if movement[0] > 0:
                self.set_right(blocker.left)
                collisions['right'] = True
            if movement[0] < 0:
                self.set_left(blocker.right)
                collisions['left'] = True
        
        self.origin[1] += movement[1]
        blocker = self.collision_check(blockers)
        if blocker:
            if movement[1] > 0:
                self.set_top(blocker.bottom)
                collisions['top'] = True
            if movement[1] < 0:
                self.set_bottom(blocker.top)
                collisions['bottom'] = True

        self.origin[2] += movement[2]
        blocker = self.collision_check(blockers)
        if blocker:
            if movement[2] > 0:
                self.set_front(blocker.back)
                collisions['front'] = True
            if movement[2] < 0:
                self.set_back(blocker.front)
                collisions['back'] = True
        
        return collisions
    
class FloorCuboid(Cuboid):
    def __init__(self, origin, size):
        super().__init__(origin, size)

    @property
    def top(self):
        return self.origin[1] + self.size[1]
    
    def set_top(self, value):
        self.origin[1] = value - self.size[1]
    
    @property
    def bottom(self):
        return self.origin[1]
    
    def set_bottom(self, value):
        self.origin[1] = value

class CornerCuboid(Cuboid):
    def __init__(self, origin, size):
        super().__init__(origin, size)

    @property
    def right(self):
        return self.origin[0] + self.size[0]
    
    def set_right(self, value):
        self.origin[0] = value - self.size[0]
    
    @property
    def left(self):
        return self.origin[0]
    
    def set_left(self, value):
        self.origin[0] = value
    
    @property
    def top(self):
        return self.origin[1] + self.size[1]
    
    def set_top(self, value):
        self.origin[1] = value - self.size[1]
    
    @property
    def bottom(self):
        return self.origin[1]
    
    def set_bottom(self, value):
        self.origin[1] = value
    
    @property
    def front(self):
        return self.origin[2] + self.size[2]
    
    def set_front(self, value):
        self.origin[2] = value - self.size[2]
    
    @property
    def back(self):
        return self.origin[2]
    
    def set_back(self, value):
        self.origin[2] = value