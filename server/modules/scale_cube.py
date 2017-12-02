
IONIAN = [
    0, 2, 4, 5, 7, 9, 11
]

AEOLIAN = [
    0, 2, 3, 5, 7, 8, 10
]

# six scales

SCALES = [
    IONIAN,
    AEOLIAN,
] + [AEOLIAN] * 4


class ScaleCube:
    """
    The Power Cube of Scales
    """

    def __init__(self, scales=SCALES, init_scale=0):
        self.scales = scales
        self.scale = scales[init_scale]
