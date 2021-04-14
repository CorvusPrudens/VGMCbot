import random
import math
import copy

import numpy as np

import utils

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

tiles = {
    'unlit': ' ',
    'lit': '•',
    'opaque': '█',
    'opaque_up': '▀',
    'opaque_down': '▄',
    'water': '~'
    # 'corpse': '×', this would be a dynamic element, not a baked room element
}

# flatgen = {}
# keys = list(tiles.keys())
#
# for i in range(len(keys)):
#     for j in range(len(keys)):



flat = {
    (0, 0): 'unlit',
    (2, 1): 'opaque_up',
    (1, 2): 'opaque_down',
    (1, 1): 'lit',

    (2, 0): 'opaque_up',
    (0, 2): 'opaque_down',
    (2, 2): 'opaque',
}

# NOTE for map data --
# 0 = unlit tile
# 1 = lit
# 2 = opaque

doorTemplate = {
    'type': 'normal',
    'position': (0, 0),
    'postr': 'left',
    'state': 'open',
}

def newDoor(type, pos, postr, state):
    return {'type': type, 'pos': pos, 'postr': postr, 'state': state}

roomTemplate = {
    'type': 'room',
    'name': 'room',
    'width' : -1,
    'height': -1,
    'playerw': 3,
    'playerh': 3,
    'draww': -1,
    'drawh': -1,
    'ptog': {},
    'flav': {},
    'map': [],
    'things': [],
    'doors': [],
    'special': None,
    'dist': 0,
}

sqRoom = {
    'type': 'room',
    'name': 'square',
    'width': 5,
    'height': 5,
    'playerw': 3,
    'playerh': 3,
    'map': [
        2, 2, 2, 2, 2,
        2, 0, 0, 0, 2,
        2, 0, 0, 0, 2,
        2, 0, 0, 0, 2,
        2, 2, 2, 2, 2,
    ],
    'things': [],
}

def formatRoom(roomdict):
    w = roomdict['draww']
    h = roomdict['drawh']
    # for final discord use:
    # output = '```'
    output = ''
    mapp = roomdict['map']
    # print(math.ceil(h/2))
    for y in range(math.ceil(h/2)):
        for x in range(w):
            pos1 = utils.od(x, y*2, w)
            pos2 = utils.od(x, y*2 + 1, w)
            # print(pos1, pos2)
            try:
                output += tiles[flat[(mapp[pos1], mapp[pos2])]]
            except IndexError:
                # print(flat[(mapp[pos1]), mapp[pos1]])
                output += tiles[flat[(mapp[pos1], 0)]]
            except KeyError:
                print('Error: room {} is poorly formatted!'.format(roomdict['name']))
                exit(1)
        output += '\n'
    # for final discord use:
    # output += '```'
    return output


doorList = [
    'up',
    'down',
    'left',
    'right'
]

doorTrans = {
    (0, 1): 'left',
    (2, 1): 'right',
    (1, 0): 'up',
    (1, 2): 'down'
}

wallTile = 2
litTile = 1

def genRect(dict, tempmap, width, height, fill, location, doors):
    # smallest size for a rect is 5x5
    for y in range(height):
        for x in range(width):
            if y == 0:
                tempmap[utils.od(x, y, width)] = wallTile
            elif y == height - 1:
                tempmap[utils.od(x, y, width)] = wallTile
            if x == 0:
                tempmap[utils.od(x, y, width)] = wallTile
            elif x == width - 1:
                tempmap[utils.od(x, y, width)] = wallTile

            if fill:
                if x > 1 and x < width - 2 and y > 1 and y < height - 2:
                    if (x + 1) % 3 == 0:
                        tempmap[utils.od(x, y, width)] = litTile
    # if width
    # dict['playerw']
    # TODO -- this should be in terms of playerw and playerh
    for y in range(3):
        for x in range(3):
            dict['ptog'][(x, y)] = (x*((dict['width'] - 1)//2),
                                   y*((dict['height'] - 1)//2))
            dict['flav'][(x, y)] = flavorText.flavor(location, (x, y))

            if (x, y) in doorTrans and doorTrans[(x, y)] in doors:
                dict['doors'].append(newDoor('normal', (x, y), doorTrans[(x, y)], 'open'))
            elif (x, y) in doorTrans and doorTrans[(x, y)] + '_k' in doors:
                dict['doors'].append(newDoor('key', (x, y), doorTrans[(x, y)], 'open'))

    # doors (hardcoded 2 pixels)
    unlit = 0
    if height % 2 == 0:
        if 'left' in doors:
            tempmap[utils.od(0, height/2 - 1, width)] = unlit
            tempmap[utils.od(0, height/2, width)] = unlit

        if 'right' in doors:
            tempmap[utils.od(width - 1, height/2 - 1, width)] = unlit
            tempmap[utils.od(width - 1, height/2, width)] = unlit
    else:
        if 'left' in doors:
            tempmap[utils.od(0, math.floor(height/2), width)] = unlit
        if 'right' in doors:
            tempmap[utils.od(width - 1, math.floor(height/2), width)] = unlit

    if width % 2 == 0:
        if 'up' in doors:
            tempmap[utils.od(width/2 - 1, 0, width)] = unlit
            tempmap[utils.od(width/2, 0, width)] = unlit

        if 'down' in doors:
            tempmap[utils.od(width/2 - 1, height - 1, width)] = unlit
            tempmap[utils.od(width/2, height - 1, width)] = unlit
    else:
        if 'up' in doors:
            tempmap[utils.od(width/2, 0, width)] = unlit
        if 'down' in doors:
            tempmap[utils.od(width/2, height - 1, width)] = unlit


def genCircle(tempmap, width, height, fill, location):
    # smallest size for a rect is 5x5
    for y in range(height):
        for x in range(width):
            if y == 0:
                tempmap[utils.od(x, y, width)] = wallTile
            elif y == height - 1:
                tempmap[utils.od(x, y, width)] = wallTile
            if x == 0:
                tempmap[utils.od(x, y, width)] = wallTile
            elif x == width - 1:
                tempmap[utils.od(x, y, width)] = wallTile

            if fill:
                if x > 1 and x < width - 2 and y > 1 and y < height - 2:
                    if (x + 1) % 3 == 0:
                        tempmap[utils.od(x, y, width)] = litTile
    # if width
    # dict['playerw']
    # TODO -- this should be in terms of playerw and playerh
    for y in range(3):
        for x in range(3):
            dict['ptog'][(x, y)] = (x*((dict['width'] - 1)//2),
                                   y*((dict['height'] - 1)//2))
            dict['flav'][(x, y)] = flavorText.flavor(location, (x, y))

    # doors (hardcoded 2 pixels)
    unlit = 0
    if height % 2 == 0:
        tempmap[utils.od(0, height/2 - 1, width)] = unlit
        tempmap[utils.od(0, height/2, width)] = unlit
        tempmap[utils.od(width - 1, height/2 - 1, width)] = unlit
        tempmap[utils.od(width - 1, height/2, width)] = unlit
    else:
        tempmap[utils.od(0, math.floor(height/2), width)] = unlit
        tempmap[utils.od(width - 1, math.floor(height/2), width)] = unlit

    if width % 2 == 0:
        tempmap[utils.od(width/2 - 1, 0, width)] = unlit
        tempmap[utils.od(width/2, 0, width)] = unlit
        tempmap[utils.od(width/2 - 1, height - 1, width)] = unlit
        tempmap[utils.od(width/2, height - 1, width)] = unlit
    else:
        tempmap[utils.od(width/2, 0, width)] = unlit
        tempmap[utils.od(width/2, height - 1, width)] = unlit


def genRoom(name, width, height, shape, doors=doorList, fill=True, location='rim', special=None, dist=0):
    dict = copy.deepcopy(roomTemplate)
    dict['name'] = name
    dict['width'] = width
    dict['height'] = height
    width = width*3 + 2
    height = height*2 + 4
    dict['draww'] = width
    dict['drawh'] = height
    dict['special'] = special
    dict['dist'] = dist
    tempmap = np.zeros((width*height,), dtype='u1')

    # note -- this will cause errors if the height is less than four
    if shape == 'rect':
        genRect(dict, tempmap, width, height, fill, location, doors)
    elif shape == 'circle':
        genCircle(tempmap, width, height, fill, location)

    dict['map'] = tempmap
    return dict

# bigg = genRoom('sq', 18, 9, 'rect')

def printRoom(roomdict):
    for y in range(roomdict['drawh']):
        string = ''
        for x in range(roomdict['draww']):
            string += str(roomdict['map'][utils.od(x, y, roomdict['draww'])])
        print(string)

# printRoom(bigg)

arenaStr = '\n'.join([
'   ░░░░░░░░░░░░░░░░░░░░░░░░   ',
'   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒   ',
'   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ',
'  /...............{6}.{3}..\\  ',
' /••{0}••••••••••••{4}•{1}••\\ ',
'/●●●●●●●●●●●●●●●●●●●{5}●{2}●●\\'
])

replacement = [
    '•••',
    '●●●',
    '...',
    '•••',
    '●●●',
    '...'
]

barStr = '\n'.join([
' {} ',
'│{}│',
'│{}│',
'│{}│',
'│{}│',
'│{}│',
])

barFill = [
    ' ',
    '▁',
    '▂',
    '▃',
    '▄',
    '▅',
    '▆',
    '▇',
    '█',
]

def drawBar(char, total, current):
    numsegs = 5
    totalRange = numsegs * 8 # as determined by box characters
    # this assumes a start of zero
    barval = utils.clamp(int(utils.remap(current, 0, total, 0, totalRange)), 0, totalRange)
    numFull = barval // 8
    partial = barval % 8
    barlist = [barFill[-1] for x in range(numFull)]
    if partial != 0:
        barlist += [barFill[partial]]
    barlist += [' ' for x in range(numsegs - len(barlist))]
    return barStr.format(char, *barlist[::-1])


def drawArena(player):
    enemyList = [x.dict['char'] for x in player.dict['enemies']]
    enemyList += replacement[len(enemyList):]
    arena = arenaStr.format(player.dict['char'], *enemyList)
    bar = drawBar('H', player.dict['stats']['hp'], player.dict['status']['hp'])
    merge1 = utils.mergeStrings(arena, bar, 3, 0)
    return merge1


rectTemplate = genRoom('chamber', 7, 5, 'rect')

class Room:
    def __init__(self, initdict=rectTemplate, name=None, width=None, height=None, shape=None, dist=None):
        self.dict = copy.deepcopy(initdict)

        self.dict['name'] = name if name is not None else self.dict['name']
        self.dict['width'] = width if width is not None else self.dict['width']
        self.dict['height'] = height if height is not None else self.dict['height']
        self.dict['shape'] = shape if shape is not None else ''

    def draw(self, player):
        if player.dict['state']['state'] == 'exploration':
            tempbuff = formatRoom(self.dict)
            for thing in self.dict['things']:
                tempbuff = self.add(tempbuff, thing)
            tempbuff = self.addPlayer(tempbuff, player)
        elif player.dict['state']['state'] == 'combat':
            tempbuff = drawArena(player)
        return tempbuff

    def add(self, buff, thing):
        pos = self.buff2coord(thing.dict['x'], thing.dict['y'])
        offset = len(thing.dict['char'])//2
        return buff[:pos - offset] + thing.dict['char'] + buff[pos + 1 + offset:]

    def addPlayer(self, buff, player):
        temppos = self.getPlayerPos(player)
        pos = self.buff2coord(temppos[0], temppos[1])
        offset = len(player.dict['char'])//2
        # print(playerpos, temppos, pos)
        return buff[:pos - offset] + player.dict['char'] + buff[pos + 1 + offset:]

    def buff2coord(self, x, y):
        # + 1 because of newline
        return (x*3 + 2) + (y + 1)*(self.dict['draww'] + 1)

    def getPlayerPos(self, player):
        playerpos = (player.dict['x'], player.dict['y'])
        return self.dict['ptog'][playerpos]

    def insert(self, thing):
        self.dict['things'].append(thing)

    def save(self):
        for i in range(len(self.dict['things'])):
            self.dict['things'][i] = self.dict['things'][i].save()
        return self.dict

    def animate(self, player):
        for thing in self.dict['things']:
            thing.animate(player)
        for thing in self.dict['things']:
            if thing.dict['type'] == 'enemy':
                thing.resolveCollision(player)
        for thing in self.dict['things']:
            if utils.distance((thing.dict['x'], thing.dict['y']), self.getPlayerPos(player)) < 2:
                thing.onTouch(player)

    def validPosition(self, pos):
        if pos[0] < 0 or pos[0] > self.dict['width'] - 1:
            return False
        if pos[1] < 0 or pos[1] > self.dict['height'] - 1:
            return False
        return True
