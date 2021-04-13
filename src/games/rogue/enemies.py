import math
import copy
import random as rand

import utils

class Thing:
    def __init__(self, initdict={'type': 'thing', 'name': 'object'}):
        self.dict = copy.deepcopy(initdict)


    def apply(self, payload):
        try:
            for effect in payload['delta']:
                self.dict[effect] += payload['delta'][effect]
        except KeyError:
            name = self.dict['name']
            print('Error on {}; {} not present!'.format(name, effect))


    def onTouch(self, player):
        pass


    def animate(self, player):
        pass

optKeys = [
    (0, -1),
    (0, 1),
    (-1, 0),
    (1, 0),

    (-1, -1),
    (1, -1),
    (-1, 1),
    (1, 1),
]

class Enemy(Thing):

    def applyState(self):
        # may need adjusting if multiple enemies have same name
        if self.dict['state'] == 'idle':
            self.dict['char'] = '({})'.format(self.dict['name'][0])
        elif self.dict['state'] == 'alert':
            self.dict['char'] = '{{{}}}'.format(self.dict['name'][0])
        elif self.dict['state'] == 'chase':
            self.dict['char'] = '[{}]'.format(self.dict['name'][0])


    def animate(self, player):
        # simple movement script for now
        room = player.getRoom()
        playerPos = room.getPlayerPos(player)

        if self.dict['state'] == 'chase':
            self.dict['prevpos'] = (self.dict['x'], self.dict['y'])
            # TODO -- vertical upwards movement is slow for some reason
            vector = utils.direction((self.dict['x'], self.dict['y']), playerPos)
            self.dict['x'] += round(vector[0] * self.dict['stats']['speed'])
            self.dict['y'] += round(vector[1] * self.dict['stats']['speed'])

            if self.dict['x'] < 0:
                self.dict['x'] = 0
            elif self.dict['x'] > room.dict['width'] - 1:
                self.dict['x'] = room.dict['width'] - 1

            if self.dict['y'] < 0:
                self.dict['y'] = 0
            elif self.dict['y'] > room.dict['height'] - 1:
                self.dict['y'] = room.dict['height'] - 1
        elif self.dict['state'] == 'idle':
            if utils.distance(playerPos, (self.dict['x'], self.dict['y'])) <= self.dict['stats']['sensory-radius']:
                self.dict['state'] = 'chase'

        self.applyState()


    def generateCollisionOptions(self, player):
        currentPos = (self.dict['x'], self.dict['y'])
        room = player.getRoom()
        getRel = lambda x, y : (x.dict['x'] - y.dict['x'], x.dict['y'] - y.dict['y'])
        relpos = [getRel(x, self) for x in player.getRoom().dict['things']]
        ppos = room.getPlayerPos(player)
        relpos.append((ppos[0] - self.dict['x'], ppos[1] - self.dict['y']))
        opts = {k:True for k in optKeys}

        for pos in relpos:
            if pos in opts:
                opts[pos] = False

        for pos in opts:
            if not room.validPosition(utils.add_vector(currentPos, pos)):
                opts[pos] = False

        return opts


    def checkOptions(self, player, otherPos, rotSeq):
        currentPos = (self.dict['x'], self.dict['y'])
        if otherPos == currentPos:
            options = self.generateCollisionOptions(player)
            bestDirection = utils.direction((self.dict['x'], self.dict['y']), self.dict['prevpos'])
            bdpos = utils.round_vector(bestDirection)
            if utils.magnitude(bdpos) == 0:
                bdpos = rand.choice(optKeys)
            if options[bdpos] and player.getRoom().validPosition(utils.add_vector(currentPos, bdpos)):
                self.dict['x'] += bdpos[0]
                self.dict['y'] += bdpos[1]
                return True
            else:
                for rot in rotSeq:
                    testvec = utils.rotate(bdpos, rot)
                    testvec = utils.round_vector(testvec)
                    if options[testvec]:
                        self.dict['x'] += testvec[0]
                        self.dict['y'] += testvec[1]
                        return True
                # if nothing worked -- this could be expanded to do proper step-by-step
                # checking until invalid
                self.dict['x'] = self.dict['prevpos'][0]
                self.dict['y'] = self.dict['prevpos'][1]
                return True
        return False


    # this only partially works -- needs a bugfix
    def resolveCollision(self, player):
        rotSeq = [
            math.pi * 0.25,
            -math.pi * 0.25,
            math.pi * 0.5,
            -math.pi * 0.5,
            math.pi * 0.75,
            -math.pi * 0.75,
            math.pi
        ]
        thinglist = []
        for thing in player.getRoom().dict['things']:
            if thing is not self:
                thinglist.append(thing)
        poslist = [(x.dict['x'], x.dict['y']) for x in thinglist]
        poslist += [player.getRoom().getPlayerPos(player)]
        for pos in poslist:
            if self.checkOptions(player, pos, rotSeq):
                break
            # collision resolution can fail if there are no options


    def onTouch(self, player):
        player.beginCombat(self)


    def action(self, player):
        item = rand.choice(self.dict['inventory'])
        while item['type'] != 'active':
            item = rand.choice(self.dict['inventory'])
        act = rand.choice(item['moveset'])
        payload = act['method'](self, [player])
        return payload


def longestKey(dic, indent=0):
    longest = 0
    for key in dic:
        try:
            temp = longestKey(dic[key], indent=indent+2)
            if temp > longest:
                longest = temp
        except (AttributeError, TypeError):
            temp = len(' '*indent + key)
            if temp > longest:
                longest = temp
    return longest

def formatDict(dic, indent=0, longest=None):
    string = ''
    if longest == None:
        longest = longestKey(dic)
    for key in dic:
        try:
            temp = formatDict(dic[key], indent=indent+2, longest=longest)
            string += '{}:\n'.format(key)
            string += temp
        except (AttributeError, TypeError):
            spaces = longest - len(' '*indent + key)
            string += ' '*indent + '{}:{} {}\n'.format(key, spaces*' ', dic[key])
    return string

def diagMethod(user, targets):
    payload = {
        'message': formatDict(targets[0].dict['stats']),
        'data': targets[0].dict['stats'],
        'delta': {}, # this is where damage data would go
    }
    return payload

lens = {
    'name': 'diagnostic lens',
    'desc': 'this lens grants insight',
    'type': 'active',
    'moveset': [
        {
            'name': 'analyze',
            'targets': 1,
            'method': diagMethod,
        }
    ],
    'stat bonus': {}
}

def stunMethod(user, targets):
    payload = {
        'message': '{} has been stunned'.format(targets[0].dict['name']),
        'data': {},
        'delta': {'stun': 10},
    }
    return payload

stun = {
    'name': 'stun module',
    'desc': 'short aparatus equipped with electrically disruptive contacts',
    'type': 'active',
    'moveset': [
        {
            'name': 'stun',
            'targets': 1,
            'method': stunMethod,
        }
    ],
    'stat bonus': {}
}

# TODO -- moveset is generated from inventory (should be same for player)
# TODO -- each item move will have access to the current status (and player status)
# TODO -- moves are chosen randomly from a weighted list of options. Weights are a combination
# of item attributes and player/self status
sentry = {
    'name': 'sentry bot',
    'type': 'enemy',
    'char': '(s)',
    'state': 'idle',
    'x': 2,
    'y': 0,
    'prevpos': (2, 0),
    'status': {
        'hp': 10.0,
    },
    'inventory': [
        copy.deepcopy(lens),
        copy.deepcopy(stun),
    ],
    'stats': { #base stats
        'hp': 10.0,
        'sensory-radius': 3,
        'strength': 0,
        'tech': 5,
        'speed': 2, # units / player move NOTE -- really should be units per player distance travelled
        'resistance': {
            'heat': 5,
            'physical': 2,
            'electrical': 1,
            'radiation': 3,
        },
    }
}

if __name__ == '__main__':
    pass
    # print(formatDict(enemyTemplate['stats']))
