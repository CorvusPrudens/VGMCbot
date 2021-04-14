import copy
import random

from games.rogue import rooms
from games.rogue import enemies
from games.rogue import maze
import utils


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


def _genMap(rms, width, height, symboldict):
    string = []
    for idx, room in enumerate(rms):
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
             rm = lambda w, h, d, s, di : rooms.genRoom('rect', w, h, 'rect', doors=d, special=s, dist=di)
             rs = lambda d, s, di : rm(size(3.5, 1), size(3.5, 1), d, s, di)
             # print(drs)
             # for x in drs.flatten():
             #     print(x, maze.macro2key(x))
             drs = drs.flatten()
             doors = [maze.macro2key(x) for x in drs]
             special = [maze.macro2sp(x) for x in drs]
             dists = [maze.getDist(x) for x in drs]
             temprooms = [rooms.Room(initdict=rs(x, y, z)) for x, y, z in zip(doors, special, dists)]

             for room in temprooms:
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))
                 room.insert(enemies.Enemy(enemies.sentry))


             temprooms[end_flat].dict['special'] = 'E'

             self.dict['rooms'] = temprooms
