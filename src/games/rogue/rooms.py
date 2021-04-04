import random

class flavorText:

    std = '...'

    # assuming 3x3 player grid
    trans = {
        (0, 0): 'corner',
        (0, 1): 'wall',
        (0, 2): 'corner',

        (1, 0): 'wall',
        (1, 1): 'center',
        (1, 2): 'wall',

        (2, 0): 'corner',
        (2, 1): 'wall',
        (2, 2): 'corner',
    }

    rim = {
        'corner': ['a snowdrift is piled up in the corner'],
        'center': ['starlight streams in from above'],
        'wall': ['a crooked panel reveals numerous decrepit cables'],
    }

    locs = {
        'rim': rim,
    }

    @classmethod
    def flavor(self, location, pos):
        if random.random() < 0.1:
            return random.choice(self.locs[location][self.trans[pos]])
        else:
            return self.std
