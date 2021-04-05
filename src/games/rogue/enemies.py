import random as rand
import copy

class Thing:
    def __init__(self, initdict={'type': 'thing', 'name': 'object'}):
        self.dict = copy.deepcopy(initdict)

    def save(self):
        return self.dict

    def apply(self, payload):
        try:
            for effect in payload['delta']:
                self.dict[effect] += payload['delta'][effect]
        except KeyError:
            name = self.dict['name']
            print('Error on {}; {} not present!'.format(name, effect))


class Enemy(Thing):

    def animate(self, player):
        pass

    def action(self, player):
        item = rand.choice(self.dict['inventory'])
        while item['type'] != 'active':
            item = rand.choice(self.dict['inventory'])
        act = rand.choice(item['moveset'])
        payload = act['method'](self, [player])


def longestKey(dic, indent=0):
    longest = 0
    for key in dic:
        try:
            temp = longestKey(dic[key], indent=indent+2)
            if temp > longest:
                longest = temp
        except (AttributeError, TypeError) as error:
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
        except (AttributeError, TypeError) as error:
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

sentry = {
    'name': 'sentry bot',
    'type': 'enemy',
    'char': '[s]',
    'x': 2,
    'y':0,
    'hp': 10.0,
    'inventory': [
        lens,
        stun,
    ],
    'stats': { #base stats
        'strength': 0,
        'tech': 5,
        'speed': 0.5, # units / sec
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
