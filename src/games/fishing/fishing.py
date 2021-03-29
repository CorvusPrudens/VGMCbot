import json
import asyncio
import math
import copy
import re
import random as rand
from collections import namedtuple

import utils

user_regex = re.compile('((?<=(<@)[!&])|(?<=<@))[0-9]+(?=>)')

def getUserFromMention(mention):
    try:
        return int(user_regex.search(mention).group(0))
    except AttributeError:
        return None

class GameTemplate:
    def __init__(self):
        self.loopCommands = {}
        self.commands = {}
        self.helpDict = {}

    async def gameLoop(self, players, client):
        keylist = list(players.keys())
        for key in keylist:
            await self.execute(key, players, client)

    async def execute(self, playerKey, players, client):
        pass

class GameFishing(GameTemplate):
    def __init__(self):
        self.loopCommands = {
            'cast': self.lCast,
            'idle': self.lIdle,
            'forage': self.lForage,
        }
        self.commands = {
            '.goto': self.fGoto,
            '.shop': self.fShop,
            '.cast': self.fCast,
            '.locations': self.fLocations,
            '.inv': self.fInv,
            '.buy': self.fBuy,
            '.forage': self.fForage,
            '.setrod': self.fSetrod,
            '.setlure': self.fSetlure,
            '.listfish': self.fListfish,
        }
        self.totalCasts = 0

        commandString = """
Fishing Commands:
✿ .cast -- Cast with your selected rod and lure!
✿ .forage -- scrounge around for a rod and lure if you're desparate!
✿ .shop -- Take a look at the rods and lures for sale!
✿ .buy <item> -- Buy something from the shop (where item = number on the left)
✿ .locations -- Take a look at the places you can fish!
✿ .goto <location> -- Go to the given location for fishing!
✿ .inv -- Show your fishy inventory!
✿ .setrod <item> -- Set the selected rod as your primary (where item = number on the left)
✿ .setlure <item> -- Set the selected lure as your primary (where item = number on the left)
✿ .listfish -- List out all the record fish VGMC has caught!
"""
# ✿ .listfish -- List out all the record fish VGMC has caught!


        self.helpDict = {'fishing': commandString}

        self.lureShop = {
            # 'broken can': newLure()
            'hook': {'id': 1, 'price': 10, 'stats': self.newLure(name='hook', efficacy=-0.5, durability=10)},
            'popper': {'id': 2, 'price': 20, 'stats': self.newLure(name='popper', efficacy=-0.2, durability=20)},
            'spinner': {'id': 3, 'price': 40, 'stats': self.newLure(name='spinner', efficacy=0.1, durability=40)},
            'diver': {'id': 4, 'price': 100, 'stats': self.newLure(name='diver', efficacy=0.4, durability=80)}
        }

        self.rodShop = {
            'old pine rod': {'id': 5, 'price': 10, 'stats': self.newRod(name='old pine rod', efficacy=-0.5, durability=10)},
            'bamboo rod': {'id': 6, 'price': 50, 'stats': self.newRod(name='bamboo rod', efficacy=-0.1, durability=35)},
            'aluminum rod': {'id': 7, 'price': 100, 'stats': self.newRod(name='aluminum rod', efficacy=0.3, durability=80)},
            'carbon fiber composite rod': {'id': 8, 'price': 250, 'stats': self.newRod(name='carbon fiber composite rod', efficacy=0.7, durability=150)}
        }

        self.licenseShop = {
            'cliffside license': {'id': 9, 'price': 100, 'stats': self.newLicense()},
            'boat license': {'id': 10, 'price': 350, 'stats': self.newLicense(name='boat license', location='boat')},
        }

        self.fish = {}
        # since this will be run from src
        with open('games/fishing/fish.json') as file:
            self.fish = json.load(file)

        self.locations = {}
        with open('games/fishing/locations.json') as file:
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
        catch = '✿ You caught a{} **{}**! ({:,.2f} cm) {} ✿'

        small = '\nThat\'s a pretty small one though... {}'
        big = '\nWow! That\'s impressive for a{} {} {}'

        rare = '\nYou don\'t see those every day around here {}'

        output = catch.format(self.detectAn(fishcatch['name']), fishcatch['name'], fishcatch['size']/10, 'UwU')
        if fishcatch['size'] <= self.fish[fishcatch['name']]['mu'] + self.fish[fishcatch['name']]['sigma']*-threshold:
            output += small.format(':c')
        if fishcatch['size'] >= self.fish[fishcatch['name']]['mu'] + self.fish[fishcatch['name']]['sigma']*threshold:
            output += big.format(self.detectAn(fishcatch['name']), fishcatch['name'], 'UwU')

        return output


    # bias represents the efficacy of the combination of rod and hook
    # and is calculated in terms of the standard deviation

    def retrieveFish(self, currentLocation, bias=0):
        bias /= 2
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
        return {'name': name, 'efficacy': efficacy, 'durability': durability, 'damage': damage, 'type': 'rods', 'multi': True}

    def newLure(self, name='broken can', efficacy=-0.8, durability=5, damage=0):
        return {'name': name, 'efficacy': efficacy, 'durability': durability, 'damage': damage, 'type': 'lures', 'multi': True}

    def newRecord(self, name='trout', size='20', location='lagoon'):
        return {'name': name, 'size': size, 'location': location}

    def newLicense(self, name='cliff license', location='cliffside'):
        return {'name': name, 'type': 'licenses', 'multi': False, 'location': location}


    async def initFishing(self, message, client):
        try:
            client.games.players[str(message.author.id)]['games'].append('fishing')
        except KeyError:
            client.games.players[str(message.author.id)] = {'games': ['fishing']}
        templateDict = {
            'state': {'location': 'lagoon', 'state': 'idle', 'timeCast': -1, 'prevnibs': 0},
            'rods': [self.newRod()],
            'lures': [self.newLure()],
            'records': {},
            'licenses': [],
            'lastChannel': -1,
        }
        client.games.players[str(message.author.id)]['fishing'] = templateDict

        string1 = 'Hello {}, and welcome to the VGMSea! {}\n'.format(message.author.name, rand.choice(client.data.cute))
        string2 = 'Pick up a rod, get yourself a hook, and set out to catch some record breaking fish!\n'
        string3 = 'If you need help with the commands, just type .help fishing'

        await message.channel.send('✿'*20 + '\n' + string1 + string2 + string3 + '\n' + '✿'*20)

    async def lastChannel(self, message, client):
        currentPlayer = str(message.author.id)
        try:
            client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id
        except KeyError:
            await self.initFishing(message, client)
            client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id

    def setCastTime(self, message, client):
        # TODO location and efficacy should influence time
        currentPlayer = str(message.author.id)
        loc = client.games.players[currentPlayer]['fishing']['state']['location']

        totalEff = client.games.players[currentPlayer]['fishing']['rods'][0]['efficacy']
        totalEff += client.games.players[currentPlayer]['fishing']['lures'][0]['efficacy']

        min = self.locations[loc]['cast']['min']
        time = self.locations[loc]['cast']['range']
        swing = self.locations[loc]['cast']['swing']

        mintime = min + swing*-totalEff
        timerange = time + swing*-totalEff

        time = round(mintime + rand.random()*timerange, 2)
        client.games.players[currentPlayer]['fishing']['state']['timeCast'] = time

    def setForageTime(self, message, client):
        playerLoc = client.games.players[str(message.author.id)]['fishing']['state']['location']
        mintime = self.locations[playerLoc]['forage']['min']
        timerange = self.locations[playerLoc]['forage']['range']

        time = round(mintime + rand.random()*timerange, 2)
        client.games.players[str(message.author.id)]['fishing']['state']['timeCast'] = time


    async def fCast(self, message, client):
        currentPlayer = str(message.author.id)
        self.totalCasts += 1
        print('{} | {}'.format(message.author.name, self.totalCasts))
        try:
            currentState = client.games.players[currentPlayer]['fishing']['state']['state']
        except KeyError:
            await self.initFishing(message, client)
            currentState = client.games.players[currentPlayer]['fishing']['state']['state']
        if currentState != 'idle':
            mess = 'whoa chill u already {} {} o.o'.format(currentState, message.author.name)
            await message.channel.send(mess)
        else:
            len1 = len(client.games.players[currentPlayer]['fishing']['rods'])
            len2 = len(client.games.players[currentPlayer]['fishing']['lures'])
            if len1 > 0 and len2 > 0:
                client.games.players[currentPlayer]['fishing']['state']['state'] = 'cast'
                self.setCastTime(message, client)
                client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id
                loc = client.games.players[currentPlayer]['fishing']['state']['location']
                mess = 'Ok! You\'ve cast from the {} {}'.format(loc, rand.choice(client.data.cute))
                await message.channel.send(mess)
            else:
                string = 'You don\'t have any {}{} {}'
                if len1 == 0 and len2 == 0:
                    string = string.format('rods', ' _or_ lures', rand.choice(client.data.sad))
                elif len1 == 0:
                    string = string.format('rods', '', rand.choice(client.data.sad))
                else:
                    string = string.format('lures', '', rand.choice(client.data.sad))
                await message.channel.send(string)


    async def fShop(self, message, client):
        string = 'Hey {}, here\'s what we\'ve got! {}\n\n'.format(message.author.mention, rand.choice(client.data.cute))

        for key in self.lureShop:
            tempstr = '{}.) **{}** -- durability: {} -- efficacy: {} -- price: {}\n'
            string += tempstr.format(self.lureShop[key]['id'], key,
                                    self.lureShop[key]['stats']['durability'],
                                    self.lureShop[key]['stats']['efficacy'],
                                    self.lureShop[key]['price'])
        string += '\n'
        for key in self.rodShop:
            tempstr = '{}.) **{}** -- durability: {} -- efficacy: {} -- price: {}\n'
            string += tempstr.format(self.rodShop[key]['id'], key,
                                    self.rodShop[key]['stats']['durability'],
                                    self.rodShop[key]['stats']['efficacy'],
                                    self.rodShop[key]['price'])

        string += '\n'
        for key in self.licenseShop:
            tempstr = '{}.) **{}** -- price: {}\n'
            string += tempstr.format(self.licenseShop[key]['id'],
                                     key,
                                     self.licenseShop[key]['price'])

        string += '\nIf you\'d like to buy something, type .buy <left number>'
        await utils.sendBigMess(message, string)
        # await message.channel.send(string)
        await self.lastChannel(message, client)

    async def fGoto(self, message, client):
        try:
            currentState = client.games.players[str(message.author.id)]['fishing']['state']['state']
        except KeyError:
            await self.initFishing(message, client)
            currentState = client.games.players[str(message.author.id)]['fishing']['state']['state']

        if currentState == 'idle':
            sanitized = message.content.lower().replace('<', ' <').replace('>', '> ')
            sanitized = sanitized.replace('  ', ' ')
            tokens = sanitized.split(' ')

            for i in range(len(tokens)):
                targ = ''
                if tokens[i] == '.goto' and i < len(tokens) - 1:
                    targ = tokens[i + 1]
                    if targ == '':
                        targ = '<nowhere>'
                    if targ not in list(self.locations.keys()):
                        mess = 'I\'m sorry, I\'m not sure how to take you to {} {}\n'.format(targ, rand.choice(client.data.sad))
                        mess += 'If you\'re not sure where I can take you, just type .locations!'
                        await message.channel.send(mess)
                    else:
                        allowed = True
                        if self.locations[targ]["license"]:
                            allowed = False
                            for item in client.games.players[str(message.author.id)]['fishing']['licenses']:
                                if item['location'] == targ:
                                    allowed = True
                                    break
                        if allowed:
                            mess = 'Ok! Off we go to the {}! {}\n'.format(targ, rand.choice(client.data.cute))
                            await message.channel.send(mess)
                            client.games.players[str(message.author.id)]['fishing']['state']['location'] = targ
                        else:
                            mess = 'I\'m sorry {}, you don\'t have a license to fish at the {} {}'
                            mess = mess.format(message.author.name, targ, rand.choice(client.data.sad))
                            await message.channel.send(mess)
                    await self.lastChannel(message, client)
                    break
            client.games.save()
        else:
            mess = '**whoa whoa chill {}, u still {}**'.format(message.author.name, currentState)
            await message.channel.send(mess)

    async def fLocations(self, message, client):
        try:
            currentLocation = client.games.players[str(message.author.id)]['fishing']['state']['location']
        except KeyError:
            currentLocation = 'lagoon'
            await self.initFishing(message, client)
        string = """
Hey {}, here's the locations you can go to right now:

{} lagoon -- a great place for new fishers to learn the ropes! If you're out of supplies, you can forage around here.
{} cliffside -- a scenic locale where you can land a decent catch! Foraging is a bit slim on this windswept precipice. You need a cliff license to fish here.
{} boat -- just you, a boat, and some big ol\' fish. No foraging out in the surf. You need a boat license to fish here.

If you'd like to visit one, just type .goto <location> {}
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

    def itemEq(self, idx, item):
        name = f"[{item['name']}]" if idx == 0 else item['name']
        dur = '{:,.2f} / {}'.format(item['durability'] - item['damage'], item['durability'])
        return [name, dur, str(item['efficacy'])]

    async def fInv(self, message, client):
        currentPlayer = str(message.author.id)
        try:
            isFishing = client.games.players[currentPlayer]['fishing']
        except KeyError:
            await self.initFishing(message, client)

        rods = client.games.players[currentPlayer]['fishing']['rods']
        lures = client.games.players[currentPlayer]['fishing']['lures']
        licenses = client.games.players[currentPlayer]['fishing']['licenses']

        rods = [self.itemEq(x, y) for x, y in enumerate(rods)] if len(rods) > 0 else [['---']]
        lures = [self.itemEq(x, y) for x, y in enumerate(lures)] if len(lures) > 0 else [['---']]
        licenses = [[x['name']] for x in licenses] if len(licenses) > 0 else [['---']]

        rodHead = [['Rods', 'Condition', 'Efficacy']]
        lureHead = [['Lures', 'Condition', 'Efficacy']]
        liceHead = [['Licenses']]
        extra = ['[item] -> equipped']

        rods = utils.tablegen(rodHead + rods, header=True, numbered=True, extra=extra)
        lures = utils.tablegen(lureHead + lures, header=True, numbered=True)
        licenses = utils.tablegen(liceHead + licenses, header=True)
        greet = 'hey {}, here\'s what you\'ve got {}\n'.format(message.author.name, rand.choice(client.data.cute))

        await self.lastChannel(message, client)

        await utils.sendBigMess(message, greet + rods + lures + licenses)

    def extractValue(self, tokens, keyword):
        for i in range(len(tokens)):
            if keyword in tokens[i]:
                if i > len(tokens) - 2:
                    return None
                try:
                    value = int(tokens[i + 1])
                    return value
                except ValueError:
                    return None
        return None

    async def fBuy(self, message, client):
        sanitized = message.content.lower().replace('<', ' <').replace('>', '> ')
        sanitized = sanitized.replace('  ', ' ')
        tokens = sanitized.split(' ')
        currentPlayer = str(message.author.id)

        val = self.extractValue(tokens, '.buy')
        tempitem = {}
        type = ''

        if val != None:
            found = False
            for key in self.lureShop:
                if self.lureShop[key]['id'] == val:
                    found = True
                    tempitem = self.lureShop[key]
                    type = 'lures'
                    break

            if not found:
                for key in self.rodShop:
                    if self.rodShop[key]['id'] == val:
                        found = True
                        tempitem = self.rodShop[key]
                        type = 'rods'
                        break

            if not found:
                for key in self.licenseShop:
                    if self.licenseShop[key]['id'] == val:
                        found = True
                        tempitem = self.licenseShop[key]
                        type = 'licenses'
                        break

            if not found:
                mess = 'I\'m sorry, I don\'t think we have anything like that in the shop {}'
                await message.channel.send(mess.format(rand.choice(client.data.sad)))
            else:
                try:
                    bands = client.data.ledger[currentPlayer]
                except KeyError:
                    bands = 0
                if tempitem['price'] > bands:
                    mess = 'sorry {}, you don\'t have enough coins to get a{} **{}** {}'
                    itemname = tempitem['stats']['name']
                    mess = mess.format(message.author.name,
                                       self.detectAn(itemname),
                                       itemname,
                                       rand.choice(client.data.sad))
                    await message.channel.send(mess)
                else:
                    try:
                        currentItems = client.games.players[currentPlayer]['fishing'][type]
                    except KeyError:
                        await self.initFishing(message, client)
                        currentItems = client.games.players[currentPlayer]['fishing'][type]

                    taken = False
                    for item in currentItems:
                        if item['name'] == tempitem['stats']['name'] and not item['multi']:
                            taken = True
                            break
                    itemname = tempitem['stats']['name']
                    if not taken:
                        client.games.players[currentPlayer]['fishing'][type].insert(0, copy.deepcopy(tempitem['stats']))
                        mess = 'ok {}, a{} **{}** has been added to your inventory {}'
                        client.data.ledger[currentPlayer] -= tempitem['price']
                        money = client.data.ledger[currentPlayer]
                        mess2 = '\n(you now have {:,.2f} VGMCoins)'.format(money)
                        mess = mess.format(message.author.name,
                                           self.detectAn(itemname),
                                           itemname,
                                           rand.choice(client.data.cute))
                        await message.channel.send(mess + mess2)
                        client.games.save()
                        client.storeLedger()
                    else:
                        mess = 'sorry {}, you can\'t get two **{}s** {}'
                        mess = mess.format(message.author.name,
                                           itemname,
                                           rand.choice(client.data.sad))
                        await message.channel.send(mess)
        else:
            mess = 'I\'m sorry, I don\'t think we have anything like that in the shop {}'
            await message.channel.send(mess.format(rand.choice(client.data.sad)))


    async def fForage(self, message, client):
        currentPlayer = str(message.author.id)
        try:
            currentState = client.games.players[currentPlayer]['fishing']['state']['state']
        except KeyError:
            await self.initFishing(message, client)
            currentState = client.games.players[currentPlayer]['fishing']['state']['state']
        if currentState != 'idle':
            mess = 'whoa chill u already {} {} o.o'.format(currentState, message.author.name)
            await message.channel.send(mess)
        else:
            loc = client.games.players[currentPlayer]['fishing']['state']['location']
            if self.locations[loc]['forage']['allowed']:
                client.games.players[currentPlayer]['fishing']['state']['state'] = 'forage'
                # we'll use the cast time here as well
                self.setForageTime(message, client)
                client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id
                loc = client.games.players[currentPlayer]['fishing']['state']['location']
                mess = 'Ok! you\'re now foraging at the {} {}'.format(loc, rand.choice(client.data.cute))
                await message.channel.send(mess)
            else:
                mess = 'I\'m sorry {}, I don\'t think you\'ll find anything around the {} {}'
                mess = mess.format(message.author.name, loc, rand.choice(client.data.sad))
                await message.channel.send(mess)
            await self.lastChannel(message, client)

    async def fSetrod(self, message, client):
        currentPlayer = str(message.author.id)
        try:
            rods = client.games.players[currentPlayer]['fishing']['rods']
        except KeyError:
            await self.initFishing(message, client)
            rods = client.games.players[currentPlayer]['fishing']['rods']

        if len(rods) == 0:
            mess = 'you don\'t have any rods {}'.format(rand.choice(client.data.sad))
            await message.channel.send(mess)
        else:
            invalid = False
            tokens = message.content.split(' ')
            for i in range(len(tokens)):
                if tokens[i] == '.setrod':
                    if i == len(tokens) - 1:
                        rodNumber = 'NaN'
                    else:
                        try:
                            rodNumber = int(tokens[i + 1]) - 1
                            if rodNumber < 0:
                                rodNumber = 'NaN'
                        except ValueError:
                            rodNumber = 'NaN'
                    break
            try:
                selection = rods[rodNumber]
                rods.pop(rodNumber)
                rods.insert(0, selection)
                client.games.players[currentPlayer]['fishing']['rods'] = rods
                mess = 'Ok! A{} {} is now your primary rod {}'
                mess = mess.format(self.detectAn(selection['name']),
                                   selection['name'],
                                   rand.choice(client.data.cute))
                client.games.save()
                await message.channel.send(mess)
            except (TypeError, IndexError) as error:
                mess = 'I\'m sorry, I don\'t see anything like that in your inventory {}'
                mess = mess.format(rand.choice(client.data.sad))
                await message.channel.send(mess)

    async def fSetlure(self, message, client):
        currentPlayer = str(message.author.id)
        try:
            lures = client.games.players[currentPlayer]['fishing']['lures']
        except KeyError:
            await self.initFishing(message, client)
            lures = client.games.players[currentPlayer]['fishing']['lures']

        if len(lures) == 0:
            mess = 'you don\'t have any lures {}'.format(rand.choice(client.data.sad))
            await message.channel.send(mess)
        else:
            invalid = False
            tokens = message.content.split(' ')
            for i in range(len(tokens)):
                if tokens[i] == '.setlure':
                    if i == len(tokens) - 1:
                        lureNumber = 'NaN'
                    else:
                        try:
                            lureNumber = int(tokens[i + 1]) - 1
                            if lureNumber < 0:
                                lureNumber = 'NaN'
                        except ValueError:
                            lureNumber = 'NaN'
                    break
            try:
                selection = lures[lureNumber]
                lures.pop(lureNumber)
                lures.insert(0, selection)
                client.games.players[currentPlayer]['fishing']['lures'] = lures
                mess = 'Ok! A{} {} is now your primary lure {}'
                mess = mess.format(self.detectAn(selection['name']),
                                   selection['name'],
                                   rand.choice(client.data.cute))
                client.games.save()
                await message.channel.send(mess)
            except (TypeError, IndexError) as error:
                mess = 'I\'m sorry, I don\'t see anything like that in your inventory {}'
                mess = mess.format(rand.choice(client.data.sad))
                await message.channel.send(mess)


    def verifyRecord(self, userid, client, fish):
        try:
            return client.games.misc[fish['name']]['fisher'] == userid
        except KeyError:
            return False


    def sortFish(self, fishdict):
        sortedFish = sorted(fishdict.items(), key=lambda item: item[1]['size'], reverse=True)
        sortedFish = dict(sortedFish)
        return sortedFish


    async def fishTable(self, client, sortedFish, all=False, total=30, userid=None):
        extra = []

        if all:
            header = [['[Fish]', 'Size', 'Fisher']]
            tempmax = total
            extra = None
        else:
            tempmax = 15
            try:
                username = client.data.nameCache[str(userid)]
            except KeyError:
                user = await client.fetch_user(userid)
                username = user.name
                client.data.nameCache[str(userid)] = username
            header = [['Fish', 'Size']]
            extra += [username, '[Fish] -> VGMC record']

        sf = '{:,.2f}'
        templist = []
        for num, key in enumerate(sortedFish):
            if all:
                rf = '[{}]'
                fisher = client.data.nameCache[str(client.games.misc[key]['fisher'])]
                templist.append([rf.format(key), sf.format(sortedFish[key]['size']/10), fisher])
            else:
                rf = '[{}]' if self.verifyRecord(userid, client, sortedFish[key]) else '{}'
                templist.append([rf.format(key), sf.format(sortedFish[key]['size']/10)])
            if num > tempmax:
                break

        return utils.tablegen(header + templist, header=True, extra=extra)


    async def fListfish(self, message, client):
        arg1 = message.content.find('.listfish')
        arg1 = message.content[arg1 + 10:].split(' ')[0]
        if arg1 == '' or arg1.lower() == 'all':
            tempmax = 50
            if len(client.games.misc) == 0:
                mess = 'no records yet {}'.format(rand.choice(client.data.sad))
                await message.channel.send(mess)
                return
            mess = 'Here\'s the top {} fish from the VGMSea {}'
            await message.channel.send(mess.format(tempmax, rand.choice(client.data.cute)))
            sortedFish = self.sortFish(client.games.misc)
            tempstr = await self.fishTable(client, sortedFish, all=True, total=tempmax)
            client.storeNameCache()
        elif arg1.lower() == 'me':
            tempmax = 15
            try:
                mefish = client.games.players[str(message.author.id)]['fishing']['records']
            except KeyError:
                self.initFishing(message, client)
            if len(mefish) == 0:
                mess = 'no records yet {}'.format(rand.choice(client.data.sad))
                await message.channel.send(mess)
                return
            sortedFish = self.sortFish(mefish)
            mess = 'Here\'s your top {} fish from the VGMSea {}'
            await message.channel.send(mess.format(tempmax, rand.choice(client.data.cute)))
            tempstr = await self.fishTable(client, sortedFish, total=tempmax, userid=message.author.id)
        elif user_regex.search(arg1) is not None:
            tempmax = 15
            userid = getUserFromMention(arg1)
            try:
                mefish = client.games.players[str(userid)]['fishing']['records']
            except KeyError:
                mess = 'no records yet {}'.format(rand.choice(client.data.sad))
                await message.channel.send(mess)
                return
            if len(mefish) == 0:
                mess = 'no records yet {}'.format(rand.choice(client.data.sad))
                await message.channel.send(mess)
                return
            sortedFish = self.sortFish(mefish)
            mess = 'Here\'s {}\'s top {} fish from the VGMSea {}'
            await message.channel.send(mess.format(arg1, tempmax, rand.choice(client.data.cute)))
            tempstr = await self.fishTable(client, sortedFish, total=tempmax, userid=userid)
        else:
            mess = 'Sorry, I don\'t understand \"{}\" {}'
            await message.channel.send(mess.format(arg1, rand.choice(client.data.sad)))
            return

        await utils.sendBigMess(message, tempstr)


    async def lIdle(self, playerKey, players, client):
        pass

    def calcDamage(self, size):
        size /= 10
        srange = 150
        maxCoins = 8

        if size > srange:
            return maxCoins
        else:
            return round(math.sin(size*2*math.pi/(srange*4))*maxCoins, 2)

    def progBar(self, value, min, max, step=20):
        valrange = max - min
        adjval = value - min
        if adjval < 0:
            adjval = 0
        pos = adjval/valrange
        if pos > 1:
            pos = 1
        stepSize = 1/step
        string = ''
        for i in range(1, step + 1):
            if pos >= i*stepSize:
                string += '▰'
            else:
                string += '▱'
        return string

    def applyDamage(self, playerKey, players, client, size, playerName):
        damage = self.calcDamage(size)
        players[playerKey]['fishing']['rods'][0]['damage'] += damage/2
        players[playerKey]['fishing']['lures'][0]['damage'] += damage/2
        # lastChannel = await client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
        tempstr = ''

        if players[playerKey]['fishing']['rods'][0]['damage'] >= players[playerKey]['fishing']['rods'][0]['durability']:
            name = players[playerKey]['fishing']['rods'][0]['name']
            mess = '\noh no! your **{}** broke, {} {}'.format(name, playerName.name, rand.choice(client.data.sad))
            players[playerKey]['fishing']['rods'].pop(0)
            # await lastChannel.send(mess)
            tempstr += mess
        else:
            mess = '\n(**{}** condition: {:,.2f}/{})'
            damage = players[playerKey]['fishing']['rods'][0]['damage']
            durability = players[playerKey]['fishing']['rods'][0]['durability']
            mess = mess.format(players[playerKey]['fishing']['rods'][0]['name'],
                               durability - damage, durability)
            # await lastChannel.send(mess)
            tempstr += mess

        if players[playerKey]['fishing']['lures'][0]['damage'] >= players[playerKey]['fishing']['lures'][0]['durability']:
            name = players[playerKey]['fishing']['lures'][0]['name']
            mess = '\noh no! your **{}** broke, {} {}'.format(name, playerName.name, rand.choice(client.data.sad))
            players[playerKey]['fishing']['lures'].pop(0)
            # await lastChannel.send(mess)
            tempstr += mess
        else:
            mess = '\n(**{}** condition: {:,.2f}/{})'
            damage = players[playerKey]['fishing']['lures'][0]['damage']
            durability = players[playerKey]['fishing']['lures'][0]['durability']
            mess = mess.format(players[playerKey]['fishing']['lures'][0]['name'],
                               durability - damage, durability)
            # await lastChannel.send(mess)
            tempstr += mess
        return tempstr

    def addCoins(self, playerKey, players, value, client):
        # lastChannel = await client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
        mess = '\nI\'d say that\'s worth about {:,.2f} VGMCoin{} {}'
        ess = 's'
        if round(value, 2) == 1:
            ess = ''
        mess = mess.format(value, ess, rand.choice(client.data.cute))
        try:
            client.data.ledger[playerKey] += value
        except KeyError:
            client.data.ledger[playerKey] = value
        return mess
        # await lastChannel.send(mess)

    async def checkRecord(self, playerkey, players, catch, client):
        record = False
        try:
            if catch['size'] > client.games.misc[catch['name']]['size']:
                prevname = await client.fetch_user(client.games.misc[catch['name']]['fisher'])
                prev = client.games.misc[catch['name']]
                client.games.misc[catch['name']] = catch
                client.games.misc[catch['name']]['fisher'] = int(playerkey)
                mess = '\n**Wow! That\'s a new VGMC record! +5 coins! {} (you beat {}\'s record of {:,.2f} cm!)**'
                mess = mess.format(rand.choice(client.data.cute), prevname.name, prev['catch']/10)
                return mess
            else:
                return ''
        except KeyError:
            client.games.misc[catch['name']] = catch
            client.games.misc[catch['name']]['fisher'] = int(playerkey)
            mess = '\n**Wow! That\'s a new VGMC record! +5 coins!**'
            mess = mess.format(rand.choice(client.data.cute))
            return mess


    async def lCast(self, playerKey, players, client):
        players[playerKey]['fishing']['state']['timeCast'] -= 1
        if players[playerKey]['fishing']['state']['timeCast'] <= 0:
            lastChannel = await client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
            playerName = await client.fetch_user(int(playerKey))
            # 50 50 chance of catching
            # probability of catch related to efficacy
            totalEff = players[playerKey]['fishing']['rods'][0]['efficacy']
            totalEff += players[playerKey]['fishing']['lures'][0]['efficacy']
            # print(0.4 - 0.1*totalEff)

            hooked = False
            if rand.random() > 0.4 - 0.1*totalEff:
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
                tempstring = self.fishLine(catch)
                newClubRecord = 0
                # await lastChannel.send(self.fishLine(catch))

                try:
                    if players[playerKey]['fishing']['records'][catch['name']]['size'] < catch['size']:
                        prev = players[playerKey]['fishing']['records'][catch['name']]['size']
                        players[playerKey]['fishing']['records'][catch['name']] = catch
                        mess = '\n✿✿ hey that\'s a new personal best! {} '.format(rand.choice(client.data.cute))
                        mess += 'your previous best was {:,.2f} cm! ✿✿'.format(prev/10)
                        tempmess = await self.checkRecord(playerKey, players, catch, client)
                        mess += tempmess
                        if len(tempmess) > 0:
                            newClubRecord = 1
                        tempstring += mess
                        # add coins here
                except KeyError:
                    mess = '\n✿✿ oh that\'s your first {} {} ✿✿'.format(catch['name'], rand.choice(client.data.cute))
                    players[playerKey]['fishing']['records'][catch['name']] = catch
                    tempmess = await self.checkRecord(playerKey, players, catch, client)
                    mess += tempmess
                    if len(tempmess) > 0:
                        newClubRecord = 1
                    # await lastChannel.send(mess)
                    tempstring += mess
                    # add coins here
                tempstring += self.applyDamage(playerKey, players, client, catch['size'], playerName)
                tempstring += self.addCoins(playerKey, players, self.calcDamage(catch['size']) + newClubRecord*5, client)
                players[playerKey]['fishing']['state']['state'] = 'idle'
                await lastChannel.send(tempstring)
                client.storeLedger()
            else:
                mess = 'you got a nibble! but it got away {}'.format(rand.choice(client.data.sad))
                # await lastChannel.send(mess)
                mess +=  self.applyDamage(playerKey, players, client, 20, playerName)
                await lastChannel.send(mess)
                players[playerKey]['fishing']['state']['state'] = 'idle'
            client.games.save()

    async def lForage(self, playerKey, players, client):
        players[playerKey]['fishing']['state']['timeCast'] -= 1
        if players[playerKey]['fishing']['state']['timeCast'] <= 0:
            lastChannel = await client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
            playerName = await client.fetch_user(int(playerKey))
            if rand.random() > 0.5:
                #caught
                if rand.random() >= 0.6:
                    item = self.newRod(damage=rand.random()*4)
                else:
                    item = self.newLure(damage=rand.random()*4)

                mess = 'you found a{} **{}**, {} {}\nI\'ve added it to your inventory'
                mess = mess.format(self.detectAn(item['name']),
                                   item['name'],
                                   playerName.name,
                                   rand.choice(client.data.cute))

                players[playerKey]['fishing'][item['type']].insert(0, item)
                await lastChannel.send(mess)
                players[playerKey]['fishing']['state']['state'] = 'idle'
                client.games.save()

            else:
                mess = 'shoot {}, looks like you didn\'t find anything {}'.format(playerName.name, rand.choice(client.data.sad))
                await lastChannel.send(mess)
                players[playerKey]['fishing']['state']['state'] = 'idle'


# if __name__ == '__main__':
#     catch = retrieveFish(fishLocations, fishCatalog, 'boat', bias=0)
#     print(fishLine(fishLocations, fishCatalog, catch))
