# https://communityforums.atmeta.com/t5/OpenXR-Development/sRGB-RGB-giving-washed-out-bright-image/td-p/957475
FORCE_SRGB = True

SKYBOX_DIRECTIONS = ['e', 'w', 'u', 'd', 'n', 's']

TRIGGER_THRESHOLD = 0.5
HAND_VELOCITY_TIMEFRAME = 0.1
PHYSICS_EPSILON = 0.00001

RECOIL_PATTERNS = {
    'default': {
        'start': [
            (-1, 2),
            (-1, 1.5),
            (-0.2, 1.5),
            (0, 1.1),
            (2.5, 1.7),
            (-1.1, -0.2),
            (-2.1, 1.5),
            (-1, 0.7),
            (0.2, 2.1),
        ],
        'loop': [
            (0.9, 1.5),
            (2.2, 1.5),
            (2.2, 1.5),
            (0.9, 1.5),
            (0.2, 1.5),
            (-0.9, 1.5),
            (-1.8, 1.5),
            (-2.2, 1.5),
            (-1.5, 1.5),
            (-0.5, 1.5),
        ],
    }
}

BULLET_STATS = {
    'm4': {
        'helmet_pen': 0.75,
        'helmet_dmg': 1,
        'damage': 20,
    }
}