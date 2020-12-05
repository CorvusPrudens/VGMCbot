import json
import asyncio
import random as rand

class Games:

    def __init__(self, playerPath):
        self.players = {}
        self.commands = {}
        self.commandString = ''
        self.games = {}
        self.games['fishing'] = GameFishing()
        self.playerPath = playerPath

        for game in self.games:
            for key in self.games[game].commands:
                self.commands[key] = self.games[game].commands[key]
            self.commandString += self.games[game].commandString
        try:
            with open(playerPath, 'r') as file:
                self.players = json.load(file)
        except FileNotFoundError:
            pass

    async def execComm(self, command, message, client):
        await self.commands[command](message, client)

    async def gameLoop(self, client):
        for game in self.games:
            await self.games[game].gameLoop(self.players, client)


# games = Games()
#
# fishing.self.initFishing(games.players, 'corvus')
# print(games.players)

class GameTemplate:
    def __init__(self):
        self.loopCommands = {}
        self.commands = {}
        self.commandString = ''

    async def gameLoop(self, players, client):
        for key in players:
            await self.execute(key, players, client)

    async def execute(self, playerKey, players, client):
        pass

class GameFishing(GameTemplate):
    def __init__(self):
        self.loopCommands = {
            'cast': self.lCast,
            'idle': self.lIdle,
        }
        self.commands = {
            'goto': self.fGoto,
            'shop': self.fShop,
            'cast': self.fCast,
            'locations': self.fLocations,
            'inv': self.fInv,
        }
        self.commandString = """
Fishing Commands:
✿ forage -- scrounge around for a rod and lure if you're desparate!
✿ shop -- Take a look at the rods and lures for sale!
✿ buy <item> -- Buy something from the shop (where item = number on the left)
✿ locations -- Take a look at the places you can fish!
✿ goto <location> -- Go to the given location for fishing!
✿ inv -- Show your fishy inventory!
✿ cast -- Cast with your selected rod and lure!
"""

        self.lureShop = {
            # 'broken can': newLure()
            'hook': {'id': 1, 'price': 10, 'stats': self.newLure(name='hook', efficacy=-0.5, durability=10)},
            'popper': {'id': 2, 'price': 20, 'stats': self.newLure(name='popper', efficacy=-0.2, durability=20)},
            'spinner': {'id': 3, 'price': 40, 'stats': self.newLure(name='spinner', efficacy=0.1, durability=40)},
            'diver': {'id': 4, 'price': 100, 'stats': self.newLure(name='diver', efficacy=0.4, durability=80)}
        }

        self.rodShop = {
            'old pine rod': {'id': 5, 'price': 10, 'stats': self.newLure(name='old wooden rod', efficacy=-0.5, durability=10)},
            'bamboo rod': {'id': 6, 'price': 50, 'stats': self.newLure(name='popper', efficacy=-0.1, durability=20)},
            'aluminum rod': {'id': 7, 'price': 100, 'stats': self.newLure(name='aluminum rod', efficacy=0.3, durability=40)},
            'carbon fiber composite rod': {'id': 8, 'price': 200, 'stats': self.newLure(name='carbon fiber composite rod', efficacy=0.7, durability=80)}
        }

        self.fish = {}
        # since this will be run from src
        with open('games/fish.json') as file:
            self.fish = json.load(file)

        self.locations = {}
        with open('games/locations.json') as file:
            self.locations = json.load(file)

    async def execute(self, playerKey, players, client):
        # if this is executing for a player, that means they
        # have all the dictionary keys necessary for this game
        # so we don't need to check
        state = players[playerKey]['fishing']['state']['state']
        await self.loopCommands[state](playerKey, players, client)

    def detectAn(self, string):
        anChars = ['a', 'e', 'i', 'o', 'u']
        if string.lower()[0] in anChars:
            return 'n'
        else:
            return ''

    # TODO record code ought to execute here too
    # TODO consider adding image urls to fish list
    def fishLine(self, fishcatch, threshold=2):
        catch = '✿ You caught a{} {}! ({:,.2f} cm) {} ✿\n'

        small = 'That\'s a pretty small one though... {}\n'
        big = 'Wow! That\'s impressive for a{} {} {}\n'

        rare = 'You don\'t see those every day around here {}\n'

        output = catch.format(self.detectAn(fishcatch['name']), fishcatch['name'], fishcatch['size']/10, 'UwU')
        if fishcatch['size'] <= self.fish[fishcatch['name']]['mu'] + self.fish[fishcatch['name']]['sigma']*-threshold:
            output += small.format(':c')
        if fishcatch['size'] >= self.fish[fishcatch['name']]['mu'] + self.fish[fishcatch['name']]['sigma']*threshold:
            output += big.format(self.detectAn(fishcatch['catch']), fishcatch['catch'], 'UwU')

        return output


    # bias represents the efficacy of the combination of rod and hook
    # and is calculated in terms of the standard deviation

    def retrieveFish(self, currentLocation, bias=0):
        min = 20.0
        mu = self.locations[currentLocation]['mu']
        sigma = self.locations[currentLocation]['sigma']
        mu += bias*sigma
        size = rand.gauss(mu, sigma)
        # if size > locations[currentLocation]['max']:
        #     size = locations[currentLocation]['max']
        if size < self.locations[currentLocation]['min']:
            size = self.locations[currentLocation]['min']

        # catch = locations[currentLocation]['fishlist'][]
        catch = ''
        for i in range(len(self.locations[currentLocation]['fishlist']) - 1, -1, -1):
            if size >= self.fish[self.locations[currentLocation]['fishlist'][i]]['mu']:
                catch = self.locations[currentLocation]['fishlist'][i]
            else:
                break

        size = rand.gauss(self.fish[catch]['mu'] + self.fish[catch]['sigma']*bias, self.fish[catch]['sigma'])
        size = round(size, 1)

        if size < min:
            size = min

        return {'name': catch, 'size': size, 'location': currentLocation}



    # while it may seem obtuse, I'm going to operate on everything
    # more or less as a dictionary. That way, saving is much easier
    # than working with objects!

    # TODO you should be able to forage for a branch instead of using vgmcoins
    # and it should take a few minutes to find
    def newRod(self, name='branch', efficacy=-0.8, durability=5, damage=0):
        return {'name': name, 'efficacy': efficacy, 'durability': durability, 'damage': damage}

    def newLure(self, name='broken can', efficacy=-0.8, durability=5, damage=0):
        return {'name': name, 'efficacy': efficacy, 'durability': durability, 'damage': damage}

    def newRecord(self, name='trout', size='20', location='lagoon'):
        return {'name': name, 'size': size, 'location': location}


    async def initFishing(self, message, client):
        try:
            client.games.players[message.author.id]['games'].append('fishing')
        except KeyError:
            client.games.players[message.author.id] = {'games': ['fishing']}
        templateDict = {
            'state': {'location': 'lagoon', 'state': 'idle', 'timeCast': -1, 'prevnibs': 0},
            'rods': [self.newRod()],
            'lures': [self.newLure()],
            'records': {},
            'lastChannel': -1,
        }
        client.games.players[message.author.id]['fishing'] = templateDict

        string1 = 'Hello {}, and welcome to the VGMSea! {}\n'.format(message.author.name, rand.choice(client.data.cute))
        string2 = 'Pick up a rod, get yourself a hook, and set out to catch some record breaking fish!\n'
        string3 = 'If you need help with the commands, just mention me and say help'

        await message.channel.send('✿'*20 + '\n' + string1 + string2 + string3 + '\n' + '✿'*20)

    async def lastChannel(self, message, client):
        try:
            client.games.players[message.author.id]['fishing']['lastChannel'] = message.channel
        except KeyError:
            await self.initFishing(message, client)
            client.games.players[message.author.id]['fishing']['lastChannel'] = message.channel

    def setCastTime(self, message, client):
        # TODO location and efficacy should influence time

        totalEff = client.games.players[message.author.id]['fishing']['rods'][0]['efficacy']
        totalEff += client.games.players[message.author.id]['fishing']['lures'][0]['efficacy']

        mintime = 2 + 1*-totalEff
        timerange = 5 + 1*-totalEff

        time = mintime + rand.random()*timerange
        client.games.players[message.author.id]['fishing']['state']['timeCast'] = time


    async def fCast(self, message, client):
        currentPlayer = message.author.id
        try:
            if client.games.players[currentPlayer]['fishing']['state']['state'] == 'cast':
                mess = 'hey chill {}, you\'ve already got a line out'.format(message.author.name)
                await message.channel.send(mess)
            else:
                len1 = len(client.games.players[currentPlayer]['fishing']['rods'])
                len2 = len(client.games.players[currentPlayer]['fishing']['lures'])
                if len1 > 0 and len2 > 0:
                    client.games.players[currentPlayer]['fishing']['state']['state'] = 'cast'
                    self.setCastTime(message, client)
                    client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel
                    loc = client.games.players[currentPlayer]['fishing']['state']['location']
                    mess = 'Ok! You\'ve cast from the {} {}'.format(loc, rand.choice(client.data.cute))
                    await message.channel.send(mess)
                else:
                    string = 'You don\'t have any {}{} {}'
                    if len1 == 0 and len2 == 0:
                        string.format('rods', ' _or_ lures', rand.choice(client.data.sad))
                    elif len1 == 0:
                        string.format('rods', '', rand.choice(client.data.sad))
                    else:
                        string.format('lures', '', rand.choice(client.data.sad))
                    await message.channel.send(string)
        except KeyError:
            await self.initFishing(message, client)
            client.games.players[currentPlayer]['fishing']['state']['state'] = 'cast'
            self.setCastTime(message, client)
            client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel
            loc = client.games.players[currentPlayer]['fishing']['state']['location']
            mess = 'Ok! You\'ve cast from the {} {}'.format(loc, rand.choice(client.data.cute))
            await message.channel.send(mess)
        # try:
        #     len1 = len(client.games.players[currentPlayer]['fishing']['rods'])
        #     len2 = len(client.games.players[currentPlayer]['fishing']['lures'])
        #     if len1 > 0 and len2 > 0:
        #         client.games.players[currentPlayer]['fishing']['state']['state'] = 'cast'
        #         client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel
        #         loc = client.games.players[currentPlayer]['fishing']['state']['location']
        #         mess = 'Ok! You\'ve cast from the {} {}'.format(loc, rand.choice(client.data.cute))
        #         await message.channel.send(mess)
        #     else:
        #         string = 'You don\'t have any {}{} {}'
        #         if len1 == 0 and len2 == 0:
        #             string.format('rods', ' _or_ lures', rand.choice(client.data.sad))
        #         elif len1 == 0:
        #             string.format('rods', '', rand.choice(client.data.sad))
        #         else:
        #             string.format('lures', '', rand.choice(client.data.sad))
        #         await message.channel.send(string)


    async def fShop(self, message, client):
        string = 'Hey {}, here\'s what we\'ve got! {}\n\n'.format(message.author.mention, rand.choice(client.data.cute))
        t = 0
        for key in self.lureShop:
            tempstr = '{}.) {} -- durability: {} -- efficacy: {} -- price: {}\n'
            string += tempstr.format(self.lureShop[key]['id'], key,
                                    self.lureShop[key]['stats']['durability'],
                                    self.lureShop[key]['stats']['efficacy'],
                                    self.lureShop[key]['price'])
        string += '\n'
        for key in self.rodShop:
            tempstr = '{}.) {} -- durability: {} -- efficacy: {} -- price: {}\n'
            string += tempstr.format(self.rodShop[key]['id'], key,
                                    self.rodShop[key]['stats']['durability'],
                                    self.rodShop[key]['stats']['efficacy'],
                                    self.rodShop[key]['price'])

        string += '\nIf you\'d like to buy something, mention me and say buy <left number>'
        await message.channel.send(string)
        self.lastChannel(message, client)

    async def fGoto(self, message, client):
        sanitized = message.content.lower().replace('<', ' <').replace('>', '> ')
        sanitized = sanitized.replace('  ', ' ')
        tokens = sanitized.split(' ')

        for i in range(len(tokens)):
            targ = ''
            if tokens[i] == 'goto' and i < len(tokens) - 1:
                targ = tokens[i + 1]
                if targ == '':
                    targ = '<nowhere>'
                if targ not in list(self.locations.keys()):
                    mess = 'I\'m sorry, I\'m not sure how to take you to {} {}\n'.format(targ, rand.choice(client.data.sad))
                    mess += 'If you\'re not sure where I can take you, just mention me and say locations!'
                    await message.channel.send(mess)
                else:
                    mess = 'Ok! Off we go to the {}! {}\n'.format(targ, rand.choice(client.data.cute))
                    await message.channel.send(mess)
                    try:
                        client.games.players[message.author.id]['fishing']['state']['location'] = targ

                    except KeyError:
                        await self.initFishing(message, client)
                        client.games.players[message.author.id]['fishing']['state']['location'] = targ
                await self.lastChannel(message, client)
                break

    async def fLocations(self, message, client):
        try:
            currentLocation = client.games.players[message.author.id]['fishing']['state']['location']
        except KeyError:
            currentLocation = 'lagoon'
            await self.initFishing(message, client)
        string = """
Hey {}, here's the locations you can go to right now:

{} lagoon -- a great place for new fishers to learn the ropes! If you're out of supplies, you can forage around here.
{} cliffside -- a scenic locale where you can land a decent catch! Foraging is a bit slim on this windswept precipice.
{} boat -- just you, a boat, and some big ol\' fish. No foraging out in the surf.

If you'd like to visit one, just mention me and say goto <location> {}
"""
        flowers = ['✿', '✿', '✿']
        locs = ['lagoon', 'cliffside', 'boat']
        for i in range(len(locs)):
            if locs[i] == currentLocation:
                flowers[i] = '->'
                break
        mess = string.format(message.author.name, flowers[0], flowers[1], flowers[2], rand.choice(client.data.cute))
        await message.channel.send(mess)
        await self.lastChannel(message, client)

    async def fInv(self, message, client):
        try:
            rods = client.games.players[message.author.id]['fishing']['rods']
            lures = client.games.players[message.author.id]['fishing']['lures']
        except KeyError:
            await self.initFishing(message, client)
            rods = client.games.players[message.author.id]['fishing']['rods']
            lures = client.games.players[message.author.id]['fishing']['lures']
        await self.lastChannel(message, client)

        len1 = len(rods)
        len2 = len(lures)
        string = 'hey {}, here\'s what you\'ve got {}\n'.format(message.author.name, rand.choice(client.data.cute))
        string += 'Lures:\n'
        if len2 > 0:
            for i in range(len(lures)):
                tempstr = '\t{}.) {} -- condition: {:.1f}/{} -- efficacy: {}\n'
                string += tempstr.format(i + 1, lures[i]['name'],
                                        lures[i]['durability'] - lures[i]['damage'],
                                        lures[i]['durability'],
                                        lures[i]['efficacy'])
        else:
            string += 'nothing {}'.format(rand.choice(client.data.sad))

        string += '\nRods:\n'
        if len1 > 0:
            for i in range(len(rods)):
                tempstr = '\t{}.) {} -- condition: {:.1f}/{} -- efficacy: {}\n'
                string += tempstr.format(i + 1, rods[i]['name'],
                                        rods[i]['durability'] - rods[i]['damage'],
                                        rods[i]['durability'],
                                        rods[i]['efficacy'])
        else:
            string += 'nothing {}'.format(rand.choice(client.data.sad))

        await message.channel.send(string)


    async def lCast(self, playerKey, players, client):
        players[playerKey]['fishing']['state']['timeCast'] -= 1
        if players[playerKey]['fishing']['state']['timeCast'] <= 0:
            # 50 50 chance of catching
            # probability of catch related to efficacy
            totalEff = players[playerKey]['fishing']['rods'][0]['efficacy']
            totalEff += players[playerKey]['fishing']['lures'][0]['efficacy']

            hooked = False
            if rand.random() > 0.6 - 0.1*totalEff:
                hooked = True
                players[playerKey]['fishing']['state']['prevnibs'] = 0
            else:
                players[playerKey]['fishing']['state']['prevnibs'] += 1
                if players[playerKey]['fishing']['state']['prevnibs'] > 4:
                    hooked = True
                    players[playerKey]['fishing']['state']['prevnibs'] = 0

            if hooked:
                #caught
                catch = self.retrieveFish(players[playerKey]['fishing']['state']['location'], bias=totalEff)
                await players[playerKey]['fishing']['lastChannel'].send(self.fishLine(catch))

                try:
                    if players[playerKey]['fishing']['records'][catch['name']] < catch['size']:
                        prev = players[playerKey]['fishing']['records'][catch['name']]
                        players[playerKey]['fishing']['records'][catch['name']] = catch['size']
                        mess = '✿✿hey that\'s a new personal best! {} '.format(rand.choice(client.data.cute))
                        mess += 'your previous best was {:,.2f} cm! ✿✿'.format(prev/10)
                        await players[playerKey]['fishing']['lastChannel'].send(mess)
                        # add coins here
                except KeyError:
                    mess = '✿✿ oh that\'s your first {} {} ✿✿'.format(catch['name'], rand.choice(client.data.cute))
                    players[playerKey]['fishing']['records'][catch['name']] = catch['size']
                    await players[playerKey]['fishing']['lastChannel'].send(mess)
                    # add coins here
                players[playerKey]['fishing']['state']['state'] = 'idle'
            else:
                mess = 'you got a nibble! but it got away {}'.format(rand.choice(client.data.sad))
                await players[playerKey]['fishing']['lastChannel'].send(mess)
                players[playerKey]['fishing']['state']['state'] = 'idle'

    async def lIdle(self, playerKey, players, client):
        pass
