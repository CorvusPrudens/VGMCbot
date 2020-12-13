import json
import math
import copy
import re
import numpy as np

# TODO LIST :
# - room generation
#   - tiles, room shapes, generation system
# - level generation
#   - rooms, puzzles, smart logic, setting
# - combat
#   - turn based system, weapons, status effects, stats
# - enemies
#   - enemy types, enemy lore, enemy abilities, etc
# - bosses
#   - boss types, boss lore, general ideas for fun gameplay
# - general art/lore?
# - items
#   - healing, keys, puzzle items, unkown items, item lore/info
# - dynamic events
#   - event scripting, interesting variety
# - synergy
#   - how can all these systems interact and combine to create
#     more than the sum of their parts

# IDEA -- there could be a weak light/lamp that only
# illuminates a part of the room (making going to the middle
# and using the item an interesting choice)

# Idea -- dark world setting? Cold surface with increasingly warm interior?
# WATER -- water can be indicated with ~ and can remove negative status
# effects like burning/acid etc

# Water could block the player's path unless they have a ladder, unless they
# attempt to wade

# IDEA -- a shopkeeper or two could speak in a different language that
# requires a cipher item to communicate with. Maybe you can even buy items
# like in a normal shop, but the keeper just can't explain it in your language

# IDEA -- maybe the level map requires an item just like the room view

concept1 = '''█▀▀▀▒▒▀▀▀█
█        █
▒▒   P  ▒▒
█        █
█▄▄▄▒▒▄▄▄█
'''

concept2 = '''╔═════════════════════════╗
║ Hello weary traveler... ║
╚═════════════════════════╝
'''

textBox = {
    'ul': '╔',
    'ur': '╗',
    'ud': '═',
    'lr': '║',
    'dl': '╚',
    'dr': '╝',
}

def drawText(string, center=False):
    lines = string.split('\n')
    longestLine = 0
    numlines = 1
    for line in lines:
        if len(line) > longestLine:
            longestLine = len(line)
    for char in string:
        if char == '\n':
            numlines += 1
    output = textBox['ul'] + textBox['ud']*(longestLine + 2) + textBox['ur'] + '\n'
    # if center:
        # there's probably a way to center with formatting
        # formatter = '{} {: >?} {: >!}\n'.replace('?', str(longestLine/2))
    # else:
    formatter = '{} {: <?} {}\n'.replace('?', str(longestLine))
    print(formatter)
    for line in lines:
        output += formatter.format(textBox['lr'], line, textBox['lr'])
    return output + textBox['dl'] + textBox['ud']*(longestLine + 2) + textBox['dr'] + '\n'

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

roomTemplate = {
    'type': 'room',
    'name': 'room',
    'width' : -1,
    'height': -1,
    'map': [],
    'things': [],
}

sqRoom = {
    'type': 'room',
    'name': 'square',
    'width': 5,
    'height': 5,
    'map': [
        2, 2, 2, 2, 2,
        2, 0, 0, 0, 2,
        2, 0, 0, 0, 2,
        2, 0, 0, 0, 2,
        2, 2, 2, 2, 2,
    ],
    'things': [],
}

def od(x, y, width):
    return int(x + y*width)

def formatRoom(roomdict):
    w = roomdict['width'] + 4
    h = roomdict['height']*2 + 4
    # for final discord use:
    # output = '```'
    output = ''
    mapp = roomdict['map']
    # print(math.ceil(h/2))
    for y in range(math.ceil(h/2)):
        for x in range(w):
            pos1 = od(x, y*2, w)
            pos2 = od(x, y*2 + 1, w)
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

def genRoom(name, width, height, shape, fill=False):
    dict = copy.deepcopy(roomTemplate)
    dict['name'] = name
    dict['width'] = width
    dict['height'] = height
    width += 4
    height = height*2 + 4
    tempmap = np.zeros((width*height,), dtype='u1')

    # note -- this will cause errors if the height is less than four
    wallTile = 2
    litTile = 1
    if shape == 'rect':
        for y in range(height):
            for x in range(width):
                if y == 0:
                    tempmap[od(x, y, width)] = wallTile
                elif y == height - 1:
                    tempmap[od(x, y, width)] = wallTile
                if x == 0:
                    tempmap[od(x, y, width)] = wallTile
                elif x == width - 1:
                    tempmap[od(x, y, width)] = wallTile

                if fill:
                    if x > 1 and x < width - 2 and y > 1 and y < height - 2:
                        tempmap[od(x, y, width)] = litTile

        # doors (hardcoded 2 pixels)
        unlit = 0
        if height % 2 == 0:
            tempmap[od(0, height/2 - 1, width)] = unlit
            tempmap[od(0, height/2, width)] = unlit
            tempmap[od(width - 1, height/2 - 1, width)] = unlit
            tempmap[od(width - 1, height/2, width)] = unlit
        else:
            tempmap[od(0, math.floor(height/2), width)] = unlit
            tempmap[od(width - 1, math.floor(height/2), width)] = unlit

        if width % 2 == 0:
            tempmap[od(width/2 - 1, 0, width)] = unlit
            tempmap[od(width/2, 0, width)] = unlit
            tempmap[od(width/2 - 1, height - 1, width)] = unlit
            tempmap[od(width/2, height - 1, width)] = unlit
        else:
            tempmap[od(width/2, 0, width)] = unlit
            tempmap[od(width/2, height - 1, width)] = unlit

    dict['map'] = tempmap
    return dict

bigg = genRoom('sq', 18, 9, 'rect', fill=True)

def printRoom(roomdict):
    for y in range(roomdict['height']):
        string = ''
        for x in range(roomdict['width']):
            string += str(roomdict['map'][od(x, y, roomdict['width'])])
        print(string)

def mono(string):
    return '```' + string + '```'

# printRoom(bigg)
class Level:
    def __init__(self):
        self.dict = {
            'type': 'level',
            'rooms': [],
        }

    def addRoom(self, room):
        self.dict['rooms'].append(room)

    def save(self):
        roomlist = []
        for room in self.dict['rooms']:
            roomlist.append(room.save())
        return roomlist

class Room:
    def __init__(self, name='chamber', width=18, height=9, shape='rect'):
        self.dict = genRoom(name, width, height, shape, fill=True)
        self.buffer = formatRoom(self.dict)

    def draw(self, player):
        tempbuff = self.buffer
        for thing in self.dict['things']:
            tempbuff = self.add(tempbuff, thing)
        tempbuff = seld.add(tempbuff, player)
        return tempbuff

    def add(self, buff, thing):
        pos = self.buff2coord(thing.dict['x'], thing.dict['y'])
        return buff[:pos] + thing.dict['char'] + buff[pos + 1:]

    def buff2coord(self, x, y):
        # + 5 instead of 4 because of newline
        return (x + 2) + (y + 1)*(self.dict['width'] + 5)

    def insert(self, thing):
        self.dict['things'].append(thing)

    def save(self):
        out = copy.deepcopy(self.dict)
        for i in range(len(out['things'])):
            out['things'][i] = out['things'][i].save()
        return out

class Thing:
    def __init__(self):
        self.dict = {
            'type': 'thing',
        }

    def save(self):
        return self.dict

class Player():
    def __init__(self, name='Player', char='@', id='0'):
        self.dict = {
            'id': id,
            'type': 'player',
            'name': name,
            'x': 9,
            'y': 4,
            'char': char,
            'levels': [], # need to make home level
            'state': {
                'level': 0,
                'room': 0,
            }
        }

    def save(self):
        out = copy.deepcopy(self.dict)
        for i in range(len(out['levels'])):
            out['levels'][i] = out['levels'][i].save()
        return out


class GameTemplate:
    def __init__(self):
        self.loopCommands = {}
        self.commands = {}
        self.helpDict = {}

    async def gameLoop(self, players, client):
        # dictionary safety
        keylist = list(players.keys())
        for key in keylist:
            await self.execute(key, players, client)

    async def execute(self, playerKey, players, client):
        pass

class GameRogue(GameTemplate):
    def __init__(self, savepath='games/rogue/gamedata.json'):
        self.savepath = savepath
        self.savegames = []
        self.commands = {
            # '.coins': self.fCoins,
            '.map': self.fMap,
            '.hello': self.fHello,
        }
        self.coins = 0
        self.room = Room(width=19)
        self.player = Player()
        self.room.insert(self.player)
        self.helpDict = {'rogue': ''}

    def save(self, client):
        # here we have to figure out how we balance
        # the Player class within the players dict
        savedict = {}
        for player in self.savegames:
            savedict[player.dict['id']] = player.save()
        with open(self.savepath, 'w') as file:
            json.dump(savedict, file)
        del savedict

    # in order to load, each dict needs a type field so we can load it
    def load(self, client):
        pass

    async def fCoins(self, message, client):
        string = 'You have {} coins\n'.format(self.coins)
        await message.channel.send(string)

    async def fMap(self, message, client):
        string = self.room.draw()
        await message.channel.send(mono(string))

    async def fHello(self, message, client):
        mess = drawText("It's dangerous to go alone!\nTake this.")
        await message.channel.send(mono(mess))