import pickle
import math
import copy
import re
import os
import numpy as np
import random as rand
from games.rogue.enemies import *

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
    # print(formatter)
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
    'playerw': 3,
    'playerh': 3,
    'draww': -1,
    'drawh': -1,
    'ptog': {},
    'map': [],
    'things': [],
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

def od(x, y, width):
    return int(x + y*width)

def regexFromDict(dic, command=False, bound=False):
    if bound:
        string = '\\b('
    else:
        string = '('
    for key in dic:
        if command:
            string += '(\\{})|'.format(key)
        else:
            string += '({})|'.format(key)
    return re.compile(string[:-1] + ')\\b')

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

def genRoom(name, width, height, shape, fill=True):
    dict = copy.deepcopy(roomTemplate)
    dict['name'] = name
    dict['width'] = width
    dict['height'] = height
    width = width*3 + 2
    height = height*2 + 4
    dict['draww'] = width
    dict['drawh'] = height
    tempmap = np.zeros((width*height,), dtype='u1')

    # note -- this will cause errors if the height is less than four
    wallTile = 2
    litTile = 1
    if shape == 'rect':
        # smallest size for a rect is 5x5
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
                        if (x + 1) % 3 == 0:
                            tempmap[od(x, y, width)] = litTile
        # if width
        # dict['playerw']
        for y in range(3):
            for x in range(3):
                dict['ptog'][(x, y)] = (x*((dict['width'] - 1)//2),
                                       y*((dict['height'] - 1)//2))

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

bigg = genRoom('sq', 18, 9, 'rect')

def printRoom(roomdict):
    for y in range(roomdict['drawh']):
        string = ''
        for x in range(roomdict['draww']):
            string += str(roomdict['map'][od(x, y, roomdict['draww'])])
        print(string)

def mono(string):
    return '```\n' + string + '\n```'

def monosyn(string):
    return '```css\n' + string + '\n```'

# printRoom(bigg)

rectTemplate = genRoom('chamber', 7, 7, 'rect')

class Room:
    def __init__(self, initdict=rectTemplate, name=None, width=None, height=None, shape=None):
        self.dict = copy.deepcopy(initdict)
        if name != None:
            self.dict['name'] = name
        if width != None:
            self.dict['width'] = width
        if height != None:
            self.dict['height'] = height
        if shape != None:
            self.dict['shape'] = shape

    def draw(self, player):
        tempbuff = formatRoom(self.dict)
        for thing in self.dict['things']:
            tempbuff = self.add(tempbuff, thing)
        tempbuff = self.addPlayer(tempbuff, player)
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

class Level:
    def __init__(self, initdict={'type': 'level', 'name': 'Emitter Precipice', 'rooms': [Room()]}):
        self.dict = initdict
        self.dict['rooms'][0].insert(Enemy(initdict=sentry))

    def addRoom(self, room):
        self.dict['rooms'].append(room)

    def save(self):
        # the only time this will be called is when
        # everything is deepcopied, so 'destroying' things
        # is no biggie
        for i in range(len(self.dict['rooms'])):
            self.dict['rooms'][i] = self.dict['rooms'][i].save()
        return self.dict

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



playerTemplate = {
    'id': '-1',
    'lastChannel': None,
    'type': 'player',
    'name': 'Player',
    'x': 0,
    'y': 0,
    'char': '.C ',
    'levels': [Level()], # need to make home level
    'state': {
        'level': 0,
        'room': 0,
        'state': 'exploration',
    },
}

class Player:
    def __init__(self, initdict=playerTemplate, name=None, char=None, id=None):
        self.dict = copy.deepcopy(initdict)
        if name != None:
            self.dict['name'] = name
        if char != None:
            self.dict['char'] = char
        if id != None:
            self.dict['id'] = id

    def save(self):
        out = copy.deepcopy(self.dict)
        for i in range(len(out['levels'])):
            out['levels'][i] = out['levels'][i].save()
        return out

    def setLastChannel(self, message):
        self.dict['lastChannel'] = message.channel

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

    async def encounter(self):
        # for now, if the player is close to an enemy, combat will start
        room = self.getRoom()
        pos = room.getPlayerPos(self)
        for thing in room.dict['things']:
            dist = (pos[0] - thing.dict['x'])**2 + (pos[1] - thing.dict['y'])**2
            if dist <= 2:
                self.dict['state']['state'] = 'combat'
                mess = 'you have entered combat'
                await self.dict['lastChannel'].send(mess)

    def combat(self):
        pass



class GameTemplate:
    def __init__(self):
        self.loopCommands = {}
        self.commands = {}
        self.helpDict = {}

    async def gameLoop(self, players, client):
        # dictionary safety
        keylist = list(players.keys())
        for key in keylist:
            await self.execute(key, client)

    async def execute(self, playerKey, client):
        pass

class GameRogue(GameTemplate):
    def __init__(self, savepath='games/rogue/saves/'):
        self.savepath = savepath
        self.players = {}
        # self.load()
        self.commands = {
            # '.coins': self.fCoins,
            '.map': self.fMap,
            '.hello': self.fHello,
            '.move': self.fMove,
        }
        # self.coins = 0
        # self.room = Room(width=19)
        # self.players.append(Player())
        # self.room.insert(self.player)
        self.helpDict = {'rogue': ''}
        self.moveDict = {
            'up': (0, -1),
            'u': (0, -1),
            'north': (0, -1),
            'n': (0, -1),
            'down': (0, 1),
            'd': (0, 1),
            'south': (0, 1),
            's': (0, 1),
            'left': (-1, 0),
            'l': (-1, 0),
            'west': (-1, 0),
            'w': (-1, 0),
            'right': (1, 0),
            'r': (1, 0),
            'east': (1, 0),
            'e': (1, 0),
        }
        tempdict = {}
        for key in self.moveDict:
            if len(key) == 1:
                self.commands['.m' + key] = self.fMove
                tempdict['.m' + key] = ''

        self.moveRegex = regexFromDict(self.moveDict, bound=True)
        self.moveShort = regexFromDict(tempdict)
        del tempdict

    def save(self, player):
        with open(self.savepath + player.dict['id'] + '.pkl', 'wb') as file:
            pickle.dump(player, file, -1)

    def load(self):
        files = os.listdir(self.savepath)
        for file in files:
            id = file.replace('.pkl', '')
            with open(self.savepath + file, 'rb') as input:
                self.players[id] = pickle.load(input)

    async def addPlayer(self, message, client):
        name = await client.fetch_user(message.author.id)
        id = str(message.author.id)
        self.players[id] = Player(name=name.name, id=id)
        self.players[id].setLastChannel(message)
        await message.channel.send('u have been initted')

    async def fCoins(self, message, client):
        string = 'You have {} coins\n'.format(self.coins)
        await message.channel.send(string)

    async def fMap(self, message, client):
        id = str(message.author.id)
        try:
            string = self.players[id].draw()
        except  KeyError:
            await self.addPlayer(message, client)
            string = self.players[id].draw()
        # printRoom(self.players[id].dict['levels'][0].dict['rooms'][0].dict)
        self.players[id].setLastChannel(message)
        self.save(self.players[id])
        await message.channel.send(monosyn(string))

    async def fMove(self, message, client):
        id = str(message.author.id)
        tokens = message.content.lower().split(' ')
        index = -1
        self.players[id].setLastChannel(message)
        for i in range(len(tokens)):
            if tokens[i] == '.move':
                index = i
                break
        if index == -1:
            match = self.moveShort.search(message.content.lower())
            if match == None:
                mess = 'invalid move command'
                await message.channel.send(mono(mess))
                return
            else:
                direction = match.group(0)[2:]
        elif index == len(tokens) - 1:
            mess = 'invalid move command'
            await message.channel.send(mono(mess))
            return
        else:
            match = self.moveRegex.search(tokens[index + 1])
            if match == None:
                mess = 'invalid move command'
                await message.channel.send(mono(mess))
                return
            else:
                direction = match.group(0)[2:]
        room = self.players[id].getRoom()
        playergrid = (room.dict['playerw'], room.dict['playerh'])
        # now for the actual moving
        prevpos = (self.players[id].dict['x'], self.players[id].dict['y'])
        matrix = self.moveDict[direction]
        newpos = (prevpos[0] + matrix[0], prevpos[1] + matrix[1])
        if newpos[0] < 0 or newpos[1] < 0 or newpos[0] >= playergrid[0] or newpos[1] >= playergrid[1]:
            mess = 'you did not move'
            await message.channel.send(mono(mess))
        else:
            self.players[id].dict['x'] = newpos[0]
            self.players[id].dict['y'] = newpos[1]
            mess = 'you moved somewhere (should be in dict or smth)'
            await message.channel.send(mono(mess))

    async def fHello(self, message, client):
        mess = drawText("It's dangerous to go alone!\nTake this.")
        await message.channel.send(mono(mess))

    # TODO -- integrate this with the game loop
    async def execute(self, playerKey, client):
        state = players[playerKey]['fishing']['state']['state']
        await self.loopCommands[state](playerKey, client)
