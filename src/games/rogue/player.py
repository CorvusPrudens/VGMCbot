import copy

import utils
from games.rogue import levels

playerTemplate = {
    'id': '-1',
    'lastChannel': None,
    'type': 'player',
    'name': 'Player',
    'x': 0,
    'y': 0,
    'char': '.C ',
    'levels': [], # need to make home level
    'inventory': [

    ],
    'status': {
        'hp': 7.5,
    },
    'state': {
        'level': 0,
        'room': 0,
        'state': 'exploration',
        'initiator': '',
    },
    'stats': { #base stats
        'hp': 10.0,
        'sensory-radius': 3,
        'strength': 3,
        'tech': 3,
        'speed': 1, # units per move?
        'resistance': {
            'heat': 3,
            'physical': 3,
            'electrical': 3,
            'radiation': 3,
        },
    },
    'prefs': {
        'movement': 'above'
    },
    'session': None,
    'enemies': [],
}

controlOptions = [
    'above',
    'below'
]

class Player:
    def __init__(self, initdict=playerTemplate, name=None, char=None, id=None):
        self.dict = copy.deepcopy(initdict)

        self.dict['name'] = name if name is not None else self.dict['name']
        self.dict['char'] = char if char is not None else self.dict['char']
        self.dict['id'] = id if id is not None else self.dict['id']

        self.dict['levels'] = [levels.Level(self)]

    def save(self):
        out = copy.deepcopy(self.dict)
        for i in range(len(out['levels'])):
            out['levels'][i] = out['levels'][i].save()
        return out

    def setLastChannel(self, channel):
        self.dict['lastChannel'] = channel

    def draw(self):
        return self.getRoom().draw(self)

    def getRoom(self):
        level = self.dict['state']['level']
        room = self.dict['state']['room']
        return self.dict['levels'][level].dict['rooms'][room]

    def apply(self, payload):
        try:
            for effect in payload['delta']:
                self.dict[effect] += payload['delta'][effect]
        except KeyError:
            name = self.dict['name']
            print('Error on {}; {} not present!'.format(name, effect))


    # async def encounter(self):
    #     # for now, if the player is close to an enemy, combat will start
    #     room = self.getRoom()
    #     pos = room.getPlayerPos(self)
    #     for thing in room.dict['things']:
    #         dist = (pos[0] - thing.dict['x'])**2 + (pos[1] - thing.dict['y'])**2
    #         if dist <= 2:
    #             self.dict['state']['state'] = 'combat'
    #             mess = 'you have entered combat'
    #             await self.dict['lastChannel'].send(mess)


    def beginCombat(self, enemy):
        self.dict['state']['initiator'] = enemy.dict['name']
        self.dict['state']['state'] = 'combat'
        for thing in self.getRoom().dict['things']:
            if thing.dict['type'] == 'enemy':
                p1 = (thing.dict['x'], thing.dict['y'])
                p2 = self.getRoom().getPlayerPos(self)
                if utils.distance(p1, p2) < 4 and thing not in self.dict['enemies']: # this distance is arbitrary -- should rather rely on 'alerted'
                    self.dict['enemies'].append(thing)


    def combat(self):
        pass
