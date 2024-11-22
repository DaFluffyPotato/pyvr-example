import sys

import pygame

pygame.init()

s = pygame.display.set_mode((100, 100))

img = pygame.image.load(sys.argv[1]).convert_alpha()

size = int(img.get_width() / 4)

OFFSETS = {
    (1, 0): 'u',
    (0, 1): 'w',
    (1, 1): 'n',
    (2, 1): 'e',
    (3, 1): 's',
    (1, 2): 'd',
}

for offset in OFFSETS:
    direction = OFFSETS[offset]
    
    rect = pygame.Rect(offset[0] * size, offset[1] * size, size, size)

    pygame.image.save(img.subsurface(rect), f'{sys.argv[1].split(".")[0]}_{direction}.png')