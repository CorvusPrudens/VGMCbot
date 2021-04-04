import pickle
import math
import copy
import re
import os
import datetime as time
import numpy as np
import random as rand

from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice

import utils
from games.rogue.enemies import *
from games.rogue import rooms

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

doorTemplate = {
    'type': 'normal',
    'position': (0, 0),
    'state': 'open',
}

def newDoor(type, pos, state):
    return {'type': type, 'pos': pos, 'state': state}

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

def langList(items):
    string = []
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return ' and '.join(items)
    else:
        for idx, item in enumerate(items):
            if (idx) < len(items) - 1:
                string.append(item + ', ')
            else:
                string.append('and ' + item)
    return ''.join(string)

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


def genRect(dict, tempmap, width, height, fill, location, doors):
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
    # TODO -- this should be in terms of playerw and playerh
    for y in range(3):
        for x in range(3):
            dict['ptog'][(x, y)] = (x*((dict['width'] - 1)//2),
                                   y*((dict['height'] - 1)//2))
            dict['flav'][(x, y)] = rooms.flavorText.flavor(location, (x, y))

            if (x, y) in doorTrans and doorTrans[(x, y)] in doors:
                dict['doors'].append(newDoor('normal', (x, y), 'open'))

    # doors (hardcoded 2 pixels)
    unlit = 0
    if height % 2 == 0:
        if 'left' in doors:
            tempmap[od(0, height/2 - 1, width)] = unlit
            tempmap[od(0, height/2, width)] = unlit

        if 'right' in doors:
            tempmap[od(width - 1, height/2 - 1, width)] = unlit
            tempmap[od(width - 1, height/2, width)] = unlit
    else:
        if 'left' in doors:
            tempmap[od(0, math.floor(height/2), width)] = unlit
        if 'right' in doors:
            tempmap[od(width - 1, math.floor(height/2), width)] = unlit

    if width % 2 == 0:
        if 'up' in doors:
            tempmap[od(width/2 - 1, 0, width)] = unlit
            tempmap[od(width/2, 0, width)] = unlit

        if 'down' in doors:
            tempmap[od(width/2 - 1, height - 1, width)] = unlit
            tempmap[od(width/2, height - 1, width)] = unlit
    else:
        if 'up' in doors:
            tempmap[od(width/2, 0, width)] = unlit
        if 'down' in doors:
            tempmap[od(width/2, height - 1, width)] = unlit


def genCircle(tempmap, width, height, fill, location):
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
    # TODO -- this should be in terms of playerw and playerh
    for y in range(3):
        for x in range(3):
            dict['ptog'][(x, y)] = (x*((dict['width'] - 1)//2),
                                   y*((dict['height'] - 1)//2))
            dict['flav'][(x, y)] = rooms.flavorText.flavor(location, (x, y))

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


def genRoom(name, width, height, shape, doors=doorList, fill=True, location='rim'):
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
            string += str(roomdict['map'][od(x, y, roomdict['draww'])])
        print(string)

def mono(string):
    return '```\n' + string + '\n```'

def monosyn(string):
    return '```css\n' + string + '\n```'

# printRoom(bigg)

rectTemplate = genRoom('chamber', 7, 5, 'rect')

class Room:
    def __init__(self, initdict=rectTemplate, name=None, width=None, height=None, shape=None):
        self.dict = copy.deepcopy(initdict)

        self.dict['name'] = name if name is not None else self.dict['name']
        self.dict['width'] = width if width is not None else self.dict['width']
        self.dict['height'] = height if height is not None else self.dict['height']
        self.dict['shape'] = shape if shape is not None else self.dict['shape']

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

levelTemplate = {
    'type': 'level',
    'name': 'Emitter Precipice',
    'width': 5,
    'height': 5,
    'rooms': [Room()],
}

class Level:
    def __init__(self, initdict=levelTemplate):
        self.dict = copy.deepcopy(initdict)
        self.dict['rooms'][0].insert(Enemy(initdict=sentry))

    def addRoom(self, room):
        self.dict['rooms'].append(room)

    def generateLevel(self, area='Emitter Precipice'):
         if area == 'Emitter Precipice':
             # todo -- levels should have random start, random end,
             # and use and moderate-length path between them
             w = self.width

             size = lambda mu, sig : utils.clamp(int(random.gauss(mu, sig)), 2, 5) * 2 + 1
             rm = lambda w, h, d : genRoom('rect', w, h, 'rect', doors=d)
             rs = lambda d : rm(size(3.5, 1), size(3.5, 1), d)
             listdoors = [copy.deepcopy(doorList) for x in range(numRooms)]
             doors = [x.pop(random.randrange(len(x))) for x in listdoors]
             temprooms = [Room(initdict=rs(x)) for x in doors]


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
    'prefs': {
        'movement': 'above'
    },
    'session': None,
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


class GameRogue(utils.GameTemplate):

    def __init__(self, client, savepath='games/rogue/saves/'):
        super(GameRogue, self).__init__(client)
        self.savepath = savepath
        self.players = {}
        self.commands = {
            '.hello': self.fHello,
            '.move': self.fMove,
        }

        commandString = """
Rogue Commands:
‣ .**map** -- Debug: Display current room.
‣ .**hello** -- Say hello.
‣ .**move** -- Move in the room.
"""

        self.reactCommands = {
            'rMove': self.rMove,
            'rNewSess': self.rNewSess,
        }

        self.helpDict = {'rogue': commandString}

        self.moveAlias = {
            'up': 'up',
            'u': 'up',
            'north': 'up',
            'n': 'up',
            '⬆️': 'up',
            'down': 'down',
            'd': 'down',
            'south': 'down',
            's': 'down',
            '⬇️': 'down',
            'left': 'left',
            'l': 'left',
            'west': 'left',
            'w': 'left',
            '⬅️': 'left',
            'right': 'right',
            'r': 'right',
            'east': 'right',
            'e': 'right',
            '➡️': 'right',
        }

        self.moveDict = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0),
        }
        tempdict = {}
        for key in self.moveAlias:
            if len(key) == 1:
                self.commands['.m' + key] = self.fMove
                tempdict['.m' + key] = ''

        self.moveRegex = regexFromDict(self.moveDict, bound=True)
        self.moveShort = regexFromDict(tempdict)
        del tempdict

    async def beginSess(self, ctx=None, channel=None, id=None):
        t = time.datetime.now().strftime('%b %d, %I:%M%p, %G')
        if ctx is not None:
            await ctx.send(mono('Session {}'.format(t)), delete_after=5)
            channel = ctx.channel
            id = ctx.author_id
        else:
            await channel.send(mono('Session {}'.format(t)), delete_after=5)

        session = await self.sMap(channel, id)
        self.players[id].dict['session'] = session


    def decorators(self, slash, guild_ids):

        @slash.slash(name="ping", guild_ids=guild_ids)
        async def _ping(ctx): # Defines a new "context" (ctx) command called "ping."
            await ctx.send(f"Pong! ({self.client.latency*1000}ms)")

        @slash.slash(
            name="begin", guild_ids=guild_ids,
            description="Begin a new Rogue session.",
        )
        async def _begin(ctx):
            await self.verifyPlayerSlash(ctx.author_id, ctx)
            if (self.players[ctx.author_id].dict['session'] == None or
                    self.players[ctx.author_id].dict['session'] not in self.reactMessages):
                await self.beginSess(ctx=ctx)
            else:
                mess = 'You already have an active session. Would you like to make a new one?'
                outmess = await ctx.send(mono(mess))
                await outmess.add_reaction('👍')
                await outmess.add_reaction('👎')
                self.newReactMessage('rNewSess', ctx.author_id, outmess)

        @slash.slash(
            name="close", guild_ids=guild_ids,
            description="Close your current session.",
        )
        async def _close(ctx):
            await self.verifyPlayerSlash(ctx.author_id, ctx)
            if self.players[ctx.author_id].dict['session'] in self.reactMessages:
                await self.removeReactMessage(self.players[ctx.author_id].dict['session'])
                self.save(self.players[ctx.author_id])
                mess = mono('Session closed.')
                await ctx.send(mess, delete_after=5)
            else:
                mess = mono('You have no active session.')
                await ctx.send(mess, delete_after=5)

        @slash.slash(
            name="prefs", guild_ids=guild_ids,
            description="Set your Rogue preferences.",
            options=[
                create_option(
                    name='Controls',
                    description='Controls options.',
                    choices=[
                        # create_choice(
                        #     name='above',
                        #     value='above'
                        # ),
                        # create_choice(
                        #     name='below',
                        #     value='below'
                        # )
                        'above',
                        'below'
                    ],
                    required=False,
                    option_type=3,
                ),
                create_option(
                    name='Character',
                    description='Your character\'s character.',
                    required=False,
                    option_type=3,
                ),
            ],
            connector={'controls': 'controls', 'character': 'character'}
        )
        async def _prefs(ctx, **kwargs):
            await self.managePrefs(ctx, kwargs)

    async def managePrefs(self, ctx, kwargs):
        pdict = {
            'controls': self.prefControls,
            'character': self.prefCharacter,
        }
        id = ctx.author_id
        await self.verifyPlayerSlash(id, ctx)
        succeeded = []
        failed = []
        string = ''
        for arg in kwargs:
            if pdict[arg](id, kwargs[arg]):
                succeeded.append(arg)
            else:
                failed.append(arg)
        if len(succeeded) > 0:
            string += 'Successfully set {}.\n'.format(langList(succeeded))
        if len(failed) > 0:
            string += 'Failed to set {} (invalid input).'.format(langList(failed))
        if len(succeeded) == 0 and len(failed) == 0:
            string = 'No preferences modified.'
        else:
            self.save(self.players[id])
        await ctx.send(content=mono(string), delete_after=5)

    async def rNewSess(self, reaction, user, add, messID):
        options = ['👍', '👎']
        if str(reaction) in options:
            if str(reaction) == options[0]:
                await self.removeReactMessage(self.players[user.id].dict['session'])
                await self.beginSess(channel=reaction.message.channel, id=user.id)
            else:
                pass
            await self.removeReactMessage(messID)


    def prefControls(self, id, controlPref):
        if controlPref in controlOptions:
            self.players[id].dict['prefs']['movement'] = controlPref
            return True
        return False

    def prefCharacter(self, id, charPref):
        charPref = charPref.strip(' ')
        if len(charPref) == 1 and charPref.isalpha():
            self.players[id].dict['char'] = '.{} '.format(charPref)
            return True
        return False

    def save(self, player):
        tempchan = player.dict['lastChannel']
        player.dict['lastChannel'] = tempchan.id
        with open(self.savepath + str(player.dict['id']) + '.pkl', 'wb') as file:
            pickle.dump(player, file, -1)
        player.dict['lastChannel'] = tempchan

    async def load(self):
        files = os.listdir(self.savepath)
        for file in files:
            id = int(file.replace('.pkl', ''))
            with open(self.savepath + file, 'rb') as input:
                self.players[id] = pickle.load(input)
                self.players[id].dict['lastChannel'] = await self.client.fetch_channel(self.players[id].dict['lastChannel'])

    def playerDeats(self, name, id, channel):
        char = name[0] if name[0].isalpha() else 'P'
        self.players[id] = Player(name=name, id=id, char='.{} '.format(char))
        self.players[id].setLastChannel(channel)
        mess = drawText('Welcome to rogue, {}'.format(name))

    async def addPlayer(self, message):
        name = message.author.name
        id = message.author.id
        mess = self.playerDeats(name, id, message.channel)
        await message.channel.send(mono(mess), delete_after=5)

    async def addPlayerSlash(self, id, ctx):
        name = ctx.author.name
        mess = self.playerDeats(name, id, ctx.channel)
        await ctx.channel.send(mono(mess), delete_after=5)


    async def fCoins(self, message):
        string = 'You have {} coins\n'.format(self.coins)
        await message.channel.send(string)

    async def verifyPlayer(self, key, message):
        if key not in self.players:
            await self.addPlayer(message)

    async def verifyPlayerSlash(self, id, ctx):
        if id not in self.players:
            await self.addPlayerSlash(id, ctx)


    async def printControls(self, channel):
        movemess = await channel.send(mono('Movement controls'))
        await movemess.add_reaction('⬅️')
        await movemess.add_reaction('➡️')
        await movemess.add_reaction('⬆️')
        await movemess.add_reaction('⬇️')
        return movemess


    async def sMap(self, channel, id):
        string = monosyn(self.players[id].draw())
        room = self.players[id].getRoom()
        pos = (self.players[id].dict['x'], self.players[id].dict['y'])
        mess = room.dict['flav'][pos]
        string += '\n' + mono(mess)
        # printRoom(self.players[id].dict['levels'][0].dict['rooms'][0].dict)
        self.save(self.players[id])
        if self.players[id].dict['prefs']['movement'] == 'above':
            movemess = await self.printControls(channel)
            outmess = await channel.send(string)
        elif self.players[id].dict['prefs']['movement'] == 'below':
            outmess = await channel.send(string)
            movemess = await self.printControls(channel)
        self.newReactMessage('rMove', id, movemess, target=outmess)
        return movemess.id


    async def rMove(self, reaction, user, add, messID):
        target = self.reactMessages[messID]['target']
        direction = str(reaction)
        if direction in self.moveAlias:
            id = user.id
            room = self.players[id].getRoom()
            playergrid = (room.dict['playerw'], room.dict['playerh'])
            # now for the actual moving
            prevpos = (self.players[id].dict['x'], self.players[id].dict['y'])
            matrix = self.moveDict[self.moveAlias[direction]]
            newpos = (prevpos[0] + matrix[0], prevpos[1] + matrix[1])
            if newpos[0] < 0 or newpos[1] < 0 or newpos[0] >= playergrid[0] or newpos[1] >= playergrid[1]:
                mess = 'you cannot proceed'
                # await message.channel.send(mono(mess))
            else:
                self.players[id].dict['x'] = newpos[0]
                self.players[id].dict['y'] = newpos[1]
                mess = room.dict['flav'][newpos]
                # await message.channel.send(mono(mess))

            string = self.players[id].draw()
            self.save(self.players[id])
            await target.edit(content=monosyn(string) + '\n' + mono(mess))


    async def fMove(self, message):
        id = message.author.id
        await self.verifyPlayer(id, message)
        self.players[id].setLastChannel(message.channel)

        tokens = message.content.lower().split(' ')
        index = -1
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
                direction = match.group(0)
        room = self.players[id].getRoom()
        playergrid = (room.dict['playerw'], room.dict['playerh'])
        # now for the actual moving
        prevpos = (self.players[id].dict['x'], self.players[id].dict['y'])
        matrix = self.moveDict[self.moveAlias[direction]]
        newpos = (prevpos[0] + matrix[0], prevpos[1] + matrix[1])
        if newpos[0] < 0 or newpos[1] < 0 or newpos[0] >= playergrid[0] or newpos[1] >= playergrid[1]:
            mess = 'you cannot proceed'
            await message.channel.send(mono(mess))
        else:
            self.players[id].dict['x'] = newpos[0]
            self.players[id].dict['y'] = newpos[1]
            mess = 'you moved somewhere (should be in dict or smth)'
            await message.channel.send(mono(mess))


    # async def

    async def fHello(self, message):
        id = message.author.id
        await self.verifyPlayer(id, message)
        self.players[id].setLastChannel(message.channel)

        mess = drawText("It's dangerous to go alone!\nTake this.")
        await message.channel.send(mono(mess))

    # TODO -- integrate this with the game loop
    async def execute(self, playerKey, players):
        pass
        # if playerKey in self.players:
        #     state = self.players[playerKey].dict['state']
        #     await self.loopCommands[state](playerKey, players)


if __name__ == '__main__':
    pass
    # player = Player()
    # rd = genRoom('circle', 5, 5, 'circle')
    # room = Room(initdict=rd)
