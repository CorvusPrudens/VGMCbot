import pickle
# import math
# import copy
import re
import os
import datetime as time
# import numpy as np
# import random as rand

from discord_slash.utils.manage_commands import create_option #, create_choice

import utils
from games.rogue import player

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

# IDEA -- The map / room view should have HP and Manna bars to the right

# IDEA -- some locks should be soft -- ie they can be solved multiple ways or have
# partial / inideal solutions
# -> in order to get the key, you have to either fight the enemy before the chest
# _or_ find the hidden item that allows you to stealth around the enemy

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

def mono(string):
    return '```\n' + string + '\n```'

def monosyn(string):
    return '```css\n' + string + '\n```'

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


    # def save(self):
    #     # the only time this will be called is when
    #     # everything is deepcopied, so 'destroying' things
    #     # is no biggie
    #     for i in range(len(self.dict['rooms'])):
    #         self.dict['rooms'][i] = self.dict['rooms'][i].save()
    #     return self.dict


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
‣ /**begin** -- Begun new Rogue session.
‣ /**close** -- Close current Rogue session. Progress is saved.
‣ /**prefs** -- Manage Rogue preferences.
‣ /**del** -- (Debug) Delete current character.
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
            name="del", guild_ids=guild_ids,
            description="Delete character.",
        )
        async def _del(ctx):
            if ctx.author_id in self.players:
                del self.players[ctx.author_id]
                await ctx.send(mono('Deleted character.'), delete_after=5)
            else:
                await ctx.send(mono('You do not have a saved character.'), delete_after=5)



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
        if controlPref in player.controlOptions:
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
                self.players[id].dict['lastChannel'] = await self.client.fetch_channel(
                    self.players[id].dict['lastChannel']
                )


    def playerDeats(self, name, id, channel):
        char = name[0] if name[0].isalpha() else 'P'
        self.players[id] = player.Player(name=name, id=id, char='.{} '.format(char))
        self.players[id].setLastChannel(channel)
        return drawText('Welcome to rogue, {}'.format(name))


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
        await movemess.add_reaction('🇲')
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


    def getDoor(self, room, doorstr):
        for door in room.dict['doors']:
            if door['postr'] == doorstr:
                return door
        return None
    # NOTE -- doors should really be linked to each other in a more sophisticated
    # way
    def moveRooms(self, player, dir):
        lev = player.dict['levels'][player.dict['state']['level']]
        pos = player.dict['state']['room']
        level = player.dict['levels'][player.dict['state']['level']]
        if dir == 'up':
            player.dict['state']['room'] -= lev.dict['width']
            roomstr = 'down'
        elif dir == 'down':
            player.dict['state']['room'] += lev.dict['width']
            roomstr = 'up'
        elif dir == 'right':
            player.dict['state']['room'] += 1
            roomstr = 'left'
        elif dir == 'left':
            player.dict['state']['room'] -= 1
            roomstr = 'right'

        newroom = level.dict['rooms'][player.dict['state']['room']]
        pos = self.getDoor(newroom, roomstr)['pos']
        player.dict['x'] = pos[0]
        player.dict['y'] = pos[1]


    # needs to be renamed to 'interaction', since it's really just handling interactions
    async def rMove(self, reaction, user, add, messID):
        target = self.reactMessages[messID]['target']
        direction = str(reaction)
        id = user.id
        if direction in self.moveAlias:
            room = self.players[id].getRoom()
            playergrid = (room.dict['playerw'], room.dict['playerh'])
            # now for the actual moving
            prevpos = (self.players[id].dict['x'], self.players[id].dict['y'])
            matrix = self.moveDict[self.moveAlias[direction]]
            newpos = (prevpos[0] + matrix[0], prevpos[1] + matrix[1])
            if newpos[0] < 0 or newpos[1] < 0 or newpos[0] >= playergrid[0] or newpos[1] >= playergrid[1]:
                mess = 'you cannot proceed'
                for door in room.dict['doors']:
                    if door['pos'] == prevpos:
                        tempdir = door['postr']
                        self.moveRooms(self.players[id], tempdir)
                        mess = '...'

                # await message.channel.send(mono(mess))
            else:
                self.players[id].dict['x'] = newpos[0]
                self.players[id].dict['y'] = newpos[1]
                mess = room.dict['flav'][newpos]
                # await message.channel.send(mono(mess))
            room.animate(self.players[id])

            if self.players[id].dict['state']['state'] == 'combat':
                mess = 'You encountered a {}!'.format(self.players[id].dict['state']['initiator'])

            string = self.players[id].draw()
            self.save(self.players[id])
            await target.edit(content=monosyn(string) + '\n' + mono(mess))
        else:
            if direction == '🇲':
                if add:
                    currentLevel = self.players[id].dict['state']['level']
                    level = self.players[id].dict['levels'][currentLevel]
                    string = level.genMap(self.players[id])
                    mess = '...'
                    await target.edit(content=monosyn(string) + '\n' + mono(mess))
                else:
                    string = self.players[id].draw()
                    room = self.players[id].getRoom()
                    pos = (self.players[id].dict['x'], self.players[id].dict['y'])
                    mess = room.dict['flav'][pos]
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
