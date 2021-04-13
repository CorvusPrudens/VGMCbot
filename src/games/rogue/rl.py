import copy
import math
import random
import numpy as np

from games.rogue import rooms
from games.rogue import enemies
from games.rogue import maze
import utils

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
            dict['flav'][(x, y)] = rooms.flavorText.flavor(location, (x, y))

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
            dict['flav'][(x, y)] = rooms.flavorText.flavor(location, (x, y))

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

#
# ┌───┐
# │ f ├──
# └───┘
#

doorwalls = {
    'left': '─┤',
    'right': '├─',
    'up': '┴',
    'down': '┬',
}

keydoors = {
    'left': '═╣',
    'right': '╠═',
    'up': '╩',
    'down': '╦',
}

nodwalls = {
    'left': ' │',
    'right': '│ ',
    'up': '─',
    'down': '─',
}

ddict = {
    'left': None,
    'right': None,
    'up': None,
    'down': None,
}

def genMapRoom(room, inside):
    empty = " ┌─{}─┐ \n{}{}{}\n └─{}─┘ "

    # TODO -- make doors a dictionary and just have doors that are walls!!!
    # doorlist = [x['postr'] for x in room.dict['doors']]

    for key in ddict:
        ddict[key] = nodwalls[key]
        for door in room.dict['doors']:
            if door['postr'] == key:
                ddict[key] = doorwalls[key] if door['type'] == 'normal' else keydoors[key]

    return empty.format(ddict['up'], ddict['left'], inside, ddict['right'], ddict['down'])


def combineH(strings):
    # this assumes all strings have same height
    h = len(strings[0].split('\n'))
    return ''.join([''.join([x.split('\n')[y] for x in strings]) + '\n' for y in range(h)])


def _genMap(rooms, width, height, symboldict):
    string = []
    for idx, room in enumerate(rooms):
        inside = symboldict[idx] if idx in symboldict else '   '
        string.append(genMapRoom(room, inside))
    return ''.join([combineH(string[x*width:(x+1)*width]) for x in range(height)])


levelTemplate = {
    'type': 'level',
    'name': 'Emitter Precipice',
    'width': 4,
    'height': 4,
    'rooms': [],
}


class Level:
    def __init__(self, player, initdict=levelTemplate):
        self.dict = copy.deepcopy(initdict)
        # self.dict['rooms'][0].insert(enemies.Enemy(initdict=enemies.sentry))
        self.generateLevel(player)

    def addRoom(self, room):
        self.dict['rooms'].append(room)

    def genMap(self, player):
        pos = player.dict['state']['room']
        char = player.dict['char']
        symboldict = {pos: char}
        for idx, room in enumerate(self.dict['rooms']):
            if room.dict['special'] is not None and idx not in symboldict:
                symboldict[idx] = ' {} '.format(room.dict['special'][0][0])
            elif idx not in symboldict:
                symboldict[idx] = ' {:X} '.format(room.dict['dist'])
        string = _genMap(self.dict['rooms'], self.dict['width'], self.dict['height'], symboldict)
        return string

    def extractScore(self, nprooms):
        pass

    def bestKeyDoor(self, opts, nprooms):
        smallest = 10000
        pos = (-1, -1)
        key = ''
        for opt in opts:
            roomint = nprooms[opts[opt]]
            dist = maze.getDist(roomint)
            if dist < smallest and dist != 0:
                smallest = dist
                pos = opts[opt]
                key = opt
        return pos, key, smallest

    def generateLevel(self, player, area='Emitter Precipice'):
         if area == 'Emitter Precipice':
             # todo -- levels should have random start, random end,
             # and use and moderate-length path between them

             attempts = 1
             scores = []
             genned = []
             starts = []
             ends = []

             for i in range(10):
                 while True:
                     try:
                         w = self.dict['width']
                         h = self.dict['height']

                         end = (random.randrange(h),random.randrange(w))

                         end_flat = utils.od(end[1], end[0], w)
                         rge = list(range(w*h))
                         rge.remove(end_flat)
                         start = random.choice(rge)
                         start = (start // w, start % w)

                         drs1, efp, dead, evis = maze.depthSearch(w, h, end, [start], max=random.randrange(2, 4))

                         drs, fp, dead, vis = maze.depthSearch(w, h, start, evis)
                         break
                     except maze.UnreachableError:
                         attempts += 1

                 # print(attempts, dead)
                 drs |= drs1

                 # connecting regions with key door
                 opts, numopts = maze.genOptions(efp, w, h, drs, evis, checkvis=False)
                 fromr = efp
                 if numopts == 0:
                     vispos = len(evis) - 1
                     while numopts == 0:
                         opts, numopts = maze.genOptions(evis[vispos], w, h, drs, evis, checkvis=False)
                         fromr = evis[vispos]
                         vispos -= 1

                 best, key, smallest = self.bestKeyDoor(opts, drs)
                 maze.setDoors(drs, key, fromr, best, 1)

                 scoretab = [
                    0,
                    10,
                    15,
                    20,
                    10,
                    5,
                 ]

                 if smallest < len(scoretab):
                     smscore = scoretab[smallest]
                 else:
                     smscore = 0

                 score = dead * 7.5 + smscore
                 # print(score)
                 scores.append(score)
                 genned.append(drs)
                 starts.append(start)
                 ends.append(end_flat)


             idx = scores.index(max(scores))
             end_flat = ends[idx]
             start = starts[idx]
             drs = genned[idx]
             player.dict['state']['room'] = utils.od(start[1], start[0], w)

             size = lambda mu, sig : utils.clamp(int(random.gauss(mu, sig)), 2, 5) * 2 + 1
             rm = lambda w, h, d, s, di : genRoom('rect', w, h, 'rect', doors=d, special=s, dist=di)
             rs = lambda d, s, di : rm(size(3.5, 1), size(3.5, 1), d, s, di)
             # print(drs)
             # for x in drs.flatten():
             #     print(x, maze.macro2key(x))
             drs = drs.flatten()
             doors = [maze.macro2key(x) for x in drs]
             special = [maze.macro2sp(x) for x in drs]
             dists = [maze.getDist(x) for x in drs]
             temprooms = [Room(initdict=rs(x, y, z)) for x, y, z in zip(doors, special, dists)]

             for room in temprooms:
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))


             temprooms[end_flat].dict['special'] = 'E'

             self.dict['rooms'] = temprooms
