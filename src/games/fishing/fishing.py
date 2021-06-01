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


class GameFishing(utils.GameTemplate):
    def __init__(self, client):
        super(GameFishing, self).__init__(client)

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
            '.recycle': self.fRecycle,
        }
        self.totalCasts = 0

        commandString = """
Fishing Commands:
✿ .**cast** -- Cast with your selected rod and lure!
✿ .**forage** -- scrounge around for a rod and lure if you're desparate!
✿ .**shop** -- Take a look at the rods and lures for sale!
✿ .**buy** <item> -- Buy something from the shop (where item = number on the left)
✿ .**locations** -- Take a look at the places you can fish!
✿ .**goto** <location> -- Go to the given location for fishing!
✿ .**inv** -- Show your fishy inventory!
✿ .**recycle** -- Recycle your extra cans!
✿ .**setrod** <item> -- Set the selected rod as your primary (where item = number on the left)
✿ .**setlure** <item> -- Set the selected lure as your primary (where item = number on the left)
✿ .**listfish** <target> -- List out all the record fish of <target> (options: all, me, @mention)!
"""
# ✿ .listfish -- List out all the record fish VGMC has caught!


        self.helpDict = {'fishing': commandString}

        self.lureShop = {
            # 'broken can': newLure()
            'hook': {'id': 1, 'price': 5, 'stats': self.newLure(name='hook', efficacy=-0.5, durability=5)},
            'popper': {'id': 2, 'price': 20, 'stats': self.newLure(name='popper', efficacy=-0.2, durability=20)},
            'spinner': {'id': 3, 'price': 80, 'stats': self.newLure(name='spinner', efficacy=0.1, durability=80)},
            'diver': {'id': 4, 'price': 240, 'stats': self.newLure(name='diver', efficacy=0.4, durability=240)}
        }

        self.rodShop = {
            'old pine rod': {'id': 5, 'price': 10, 'stats': self.newRod(name='old pine rod', efficacy=-0.5, durability=10)},
            'bamboo rod': {'id': 6, 'price': 50, 'stats': self.newRod(name='bamboo rod', efficacy=-0.1, durability=40)},
            'aluminum rod': {'id': 7, 'price': 200, 'stats': self.newRod(name='aluminum rod', efficacy=0.3, durability=160)},
            'carbon fiber rod': {'id': 8, 'price': 800, 'stats': self.newRod(name='carbon fiber rod', efficacy=0.7, durability=640)}
        }

        self.licenseShop = {
            'cliffside license': {'id': 9, 'price': 20, 'stats': self.newLicense()},
            'boat license': {'id': 10, 'price': 300, 'stats': self.newLicense(name='boat license', location='boat')},
            'sail boat': {'id': 11, 'price': 1200, 'stats': self.newLicense(name='sail boat', location='oilrig')},
        }

        self.minEff = self.newLure()['efficacy'] + self.newRod()['efficacy']
        self.maxEff = list(self.lureShop.items())[-1][1]['stats']['efficacy'] + list(self.rodShop.items())[-1][1]['stats']['efficacy']

        self.fish = {}
        # since this will be run from src
        with open('games/fishing/fish.json') as file:
            self.fish = json.load(file)

        self.locations = {}
        with open('games/fishing/locations.json') as file:
            self.locations = json.load(file)

        self.maxSize = self.locations[max(self.locations, key = lambda x : self.locations[x]['mu'])]['mu']
        self.minSize = self.locations[min(self.locations, key = lambda x : self.locations[x]['min'])]['min']


    async def execute(self, playerKey, players):
        # if this is executing for a player, that means they
        # have all the dictionary keys necessary for this game
        # so we don't need to check
        state = players[playerKey]['fishing']['state']['state']
        await self.loopCommands[state](playerKey, players)

    def detectAn(self, string):
        anChars = ['a', 'e', 'i', 'o', 'u']
        if string.lower()[0] in anChars:
            return 'n'
        else:
            return ''

    # TODO record code ought to execute here too
    # TODO consider adding image urls to fish list
    def fishLine(self, fishcatch, threshold=2.5):
        catch = '✿ You caught a{} **{}**! ({:,.2f} cm) {} ✿'

        small = '\nThat\'s a pretty small one though... {}'
        big = '\nWow! That\'s impressive for a{} {} {}'

        rare = '\nYou don\'t see those every day around here {}'

        loc = fishcatch['location']
        loc_mu = self.locations[loc]['mu']
        scale = self.locations[loc]['mu-scaled'] / loc_mu

        fish_mu = self.fish[fishcatch['name']]['mu'] * scale
        fish_sigma = self.fish[fishcatch['name']]['sigma'] * scale

        output = catch.format(self.detectAn(fishcatch['name']), fishcatch['name'], fishcatch['size']/10, 'UwU')
        if fishcatch['size'] <= fish_mu + fish_sigma*-threshold:
            output += small.format(':c')
        if fishcatch['size'] >= fish_mu + fish_sigma*threshold:
            output += big.format(self.detectAn(fishcatch['name']), fishcatch['name'], 'UwU')

        return output


    # bias represents the efficacy of the combination of rod and hook
    # and is calculated in terms of the standard deviation

    def retrieveFish(self, currentLocation, bias=0):
        # bias /= 2
        # bias *= 1.5
        # bias = abs(bias)*bias
        bias = utils.remap(bias, self.minEff, self.maxEff, 0, 1)

        numPoints = len(self.locations[currentLocation]['curve'])
        bias = self.locations[currentLocation]['curve'][int(utils.clamp(bias * numPoints, 0, 99))]

        valid = False if bias < 0.001 else True

        # slope = self.locations[currentLocation]['slope']
        # bias = utils.expBias(bias, slope)
        # bias = utils.remap(bias, 0, 1, -1, 1)

        scaledBias = utils.remap(bias, 0, 1, 0.1, 2)

        # bias = utils.remap(bias, 0, 1, -1, 1)

        minval = 20.0
        scaled_mu = self.locations[currentLocation]['mu-scaled'] * scaledBias
        mu = self.locations[currentLocation]['mu']
        sigma = self.locations[currentLocation]['sigma']
        mu += bias*sigma
        size = rand.gauss(mu, sigma)
        # if size > locations[currentLocation]['max']:
        #     size = locations[currentLocation]['max']
        size = max(size, self.locations[currentLocation]['min'])

        # catch = locations[currentLocation]['fishlist'][]
        # catch = ''
        # silly workaround to catch being too small:
        # catch = rand.choice(self.locations[currentLocation]['fishlist'])
        for i in range(len(self.locations[currentLocation]['fishlist']) - 1, -1, -1):
            if size >= self.fish[self.locations[currentLocation]['fishlist'][i]]['mu']:
                catch = self.locations[currentLocation]['fishlist'][i]
            else:
                break

        scaleFac = scaled_mu/mu
        fmu = self.fish[catch]['mu'] * scaleFac
        fsig = self.fish[catch]['sigma'] * scaleFac
        # mu_bias = max(fmu + fsig*bias, fsig)
        size = rand.gauss(fmu, fsig)
        size = round(size, 1)

        if size < minval:
            size = minval

        return {'name': catch, 'size': size, 'location': currentLocation}, valid

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

    def checkNumRecords(self, playerid):
        num = 0
        for record in self.client.games.misc:
            num = num + 1 if str(self.client.games.misc[record]['fisher']) == playerid else num
        return num


    async def initFishing(self, message):
        playerid = str(message.author.id)
        try:
            self.client.games.players[playerid]['games'].append('fishing')
        except KeyError:
            self.client.games.players[playerid] = {'games': ['fishing']}

        if playerid not in self.client.data.ledger:
            self.client.data.ledger[playerid] = 0

        templateDict = {
            'state': {'location': 'lagoon', 'state': 'idle', 'timeCast': -1, 'prevnibs': 0},
            'rods': [self.newRod()],
            'lures': [self.newLure()],
            'records': {},
            'licenses': [],
            'lastChannel': -1,
            'stats': {},
        }
        self.client.games.players[playerid]['fishing'] = templateDict

        string1 = 'Hello {}, and welcome to the VGMSea! {}\n'.format(message.author.name, rand.choice(self.client.data.cute))
        string2 = 'Pick up a rod, get yourself a hook, and set out to catch some record breaking fish!\n'
        string3 = 'If you need help with the commands, just type .help fishing'

        await message.channel.send('✿'*20 + '\n' + string1 + string2 + string3 + '\n' + '✿'*20)

    async def lastChannel(self, message):
        currentPlayer = str(message.author.id)
        try:
            self.client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id
        except KeyError:
            await self.initFishing(message)
            self.client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id

    def calcCastTime(self, location, efficacy):
        # min = self.locations[location]['cast']['min']
        # time = self.locations[location]['cast']['range']
        # swing = self.locations[location]['cast']['swing']
        # mintime = min + swing*-efficacy
        # timerange = time + swing*-efficacy
        # return round(mintime + rand.random()*timerange, 2)

        effNorm = utils.remap(efficacy, self.minEff, self.maxEff, 0, 1)
        raw = utils.expBias(1 - effNorm, 0.4)
        raw *= self.locations[location]['cast']['range'] * (1 - effNorm/2)
        raw += self.locations[location]['cast']['min']
        swing = (1 - effNorm/2) * self.locations[location]['cast']['swing']
        return round(rand.random()*swing + raw, 2)


    def setCastTime(self, message):
        # TODO location and efficacy should influence time
        currentPlayer = str(message.author.id)
        loc = self.client.games.players[currentPlayer]['fishing']['state']['location']

        totalEff = self.client.games.players[currentPlayer]['fishing']['rods'][0]['efficacy']
        totalEff += self.client.games.players[currentPlayer]['fishing']['lures'][0]['efficacy']

        time = self.calcCastTime(loc, totalEff)
        self.client.games.players[currentPlayer]['fishing']['state']['timeCast'] = time

    def setForageTime(self, message):
        playerLoc = self.client.games.players[str(message.author.id)]['fishing']['state']['location']
        mintime = self.locations[playerLoc]['forage']['min']
        timerange = self.locations[playerLoc]['forage']['range']

        time = round(mintime + rand.random()*timerange, 2)
        self.client.games.players[str(message.author.id)]['fishing']['state']['timeCast'] = time


    async def fCast(self, message):
        currentPlayer = str(message.author.id)
        self.totalCasts += 1
        print('{} | {}'.format(message.author.name, self.totalCasts))
        try:
            currentState = self.client.games.players[currentPlayer]['fishing']['state']['state']
        except KeyError:
            # await self.initFishing(message, self.client)
            await self.initFishing(message)
            currentState = self.client.games.players[currentPlayer]['fishing']['state']['state']
        if currentState != 'idle':
            mess = 'whoa chill u already {} {} o.o'.format(currentState, message.author.name)
            await message.channel.send(mess)
        else:
            len1 = len(self.client.games.players[currentPlayer]['fishing']['rods'])
            len2 = len(self.client.games.players[currentPlayer]['fishing']['lures'])
            if len1 > 0 and len2 > 0:
                self.client.games.players[currentPlayer]['fishing']['state']['state'] = 'cast'
                self.setCastTime(message)
                self.client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id
                loc = self.client.games.players[currentPlayer]['fishing']['state']['location']
                mess = 'Ok! You\'ve cast from the {} {}'.format(loc, rand.choice(self.client.data.cute))
                await message.channel.send(mess)
                try:
                    self.client.games.players[currentPlayer]['fishing']['stats']['casts'] += 1
                except KeyError:
                    self.client.games.players[currentPlayer]['fishing']['stats']['casts'] = 1

            else:
                string = 'You don\'t have any {}{} {}'
                if len1 == 0 and len2 == 0:
                    string = string.format('rods', ' _or_ lures', rand.choice(self.client.data.sad))
                elif len1 == 0:
                    string = string.format('rods', '', rand.choice(self.client.data.sad))
                else:
                    string = string.format('lures', '', rand.choice(self.client.data.sad))
                await message.channel.send(string)


    def formatShop(self, item, name):
        shortname = name.replace(' rod', '')
        row = ['{}. {}{}'.format(item["id"], (2 - len(str(item["id"])))*' ', shortname)]
        if 'durability' in item['stats']:
            row += [str(item['stats']['durability']), str(item['stats']['efficacy'])]
        else:
            row += ['---', '---']
        row += [str(item['price'])]
        return row


    async def fShop(self, message):
        string = 'Hey {}, here\'s what we\'ve got! {}\n\n'.format(message.author.mention, rand.choice(self.client.data.cute))

        header = [['Item', 'Durability', 'Efficacy', 'Price']]

        lures = [self.formatShop(self.lureShop[x], x) for x in self.lureShop]
        rods = [self.formatShop(self.rodShop[x], x) for x in self.rodShop]
        licenses = [self.formatShop(self.licenseShop[x], x) for x in self.licenseShop]

        string += '\nIf you\'d like to buy something, type .buy <left number>'
        await self.lastChannel(message)

        data =  header + [['[Lures]'], ['-']] + lures + [[' '], ['[Rods]'], ['-']] + rods + [[' '], ['[Special]'], ['-']] + licenses

        string = utils.tablegen(data, header=True)
        string += '\nIf you\'d like to buy something, type .buy <left number>'
        await utils.sendBigMess(message, string)


    async def fGoto(self, message):
        try:
            currentState = self.client.games.players[str(message.author.id)]['fishing']['state']['state']
        except KeyError:
            await self.initFishing(message)
            currentState = self.client.games.players[str(message.author.id)]['fishing']['state']['state']

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
                        mess = 'I\'m sorry, I\'m not sure how to take you to {} {}\n'.format(targ, rand.choice(self.client.data.sad))
                        mess += 'If you\'re not sure where I can take you, just type .locations!'
                        await message.channel.send(mess)
                    else:
                        allowed = True
                        if self.locations[targ]["license"]:
                            allowed = False
                            for item in self.client.games.players[str(message.author.id)]['fishing']['licenses']:
                                if item['location'] == targ:
                                    allowed = True
                                    break
                        if allowed:
                            mess = 'Ok! Off we go to the {}! {}\n'.format(targ, rand.choice(self.client.data.cute))
                            await message.channel.send(mess)
                            self.client.games.players[str(message.author.id)]['fishing']['state']['location'] = targ
                        else:
                            mess = self.locations[targ]['rejection']
                            mess = mess.format(message.author.name, rand.choice(self.client.data.sad))
                            await message.channel.send(mess)
                    await self.lastChannel(message)
                    break
            self.client.games.save()
        else:
            mess = '**whoa whoa chill {}, u still {}**'.format(message.author.name, currentState)
            await message.channel.send(mess)

    async def fLocations(self, message):
        try:
            currentLocation = self.client.games.players[str(message.author.id)]['fishing']['state']['location']
        except KeyError:
            currentLocation = 'lagoon'
            await self.initFishing(message)

        locs = [key for key in self.locations]
        flowers = ['**->**' if x == currentLocation else '✿' for x in self.locations]

        string = "Hey {}, here's the locations you can go to right now:\n\n".format(message.author.name)

        sf = '{} **{}** -- {}\n\n'
        form = lambda idx, key: sf.format(flowers[idx], key, self.locations[key]['description'])
        descriptions = [form(x, y) for x, y in enumerate(self.locations)]
        descriptions.reverse()
        descriptions = ''.join(descriptions)

        string += descriptions
        string += "If you'd like to visit one, just type .goto <location> {}".format(rand.choice(self.client.data.cute))

        await self.lastChannel(message)
        await utils.sendBigMess(message, string)


    def itemEq(self, idx, item):
        name = f"[{item['name']}]" if idx == 0 else item['name']
        dur = '{:,.2f}/{}'.format(item['durability'] - item['damage'], item['durability'])
        return [name, dur, str(item['efficacy'])]

    async def fInv(self, message):
        currentPlayer = str(message.author.id)
        try:
            isFishing = self.client.games.players[currentPlayer]['fishing']
        except KeyError:
            await self.initFishing(message)

        rods = self.client.games.players[currentPlayer]['fishing']['rods']
        lures = self.client.games.players[currentPlayer]['fishing']['lures']
        licenses = self.client.games.players[currentPlayer]['fishing']['licenses']

        playerRod = rods[0]['efficacy'] if len(rods) > 0 else 0
        playerLure = lures[0]['efficacy'] if len(lures) > 0 else 0
        extra2 = ['Equipped efficacy -> {:,.2f}'.format(playerRod + playerLure)]

        rods = [self.itemEq(x, y) for x, y in enumerate(rods)] if len(rods) > 0 else [['---']]
        lures = [self.itemEq(x, y) for x, y in enumerate(lures)] if len(lures) > 0 else [['---']]
        licenses = [[x['name']] for x in licenses] if len(licenses) > 0 else [['---']]

        rodHead = [['Rods', 'Condition', 'Efficacy']]
        lureHead = [['Lures', 'Condition', 'Efficacy']]
        liceHead = [['Special Items']]
        extra1 = ['{:,.2f} VGMCoins'.format(self.client.data.ledger[currentPlayer]), '[item] -> equipped']

        rods = utils.tablegen(rodHead + rods, header=True, numbered=True, extra=extra1, width=14)
        lures = utils.tablegen(lureHead + lures, header=True, numbered=True, extra=extra2, width=14)
        licenses = utils.tablegen(liceHead + licenses, header=True)
        greet = 'hey {}, here\'s what you\'ve got {}\n'.format(message.author.name, rand.choice(self.client.data.cute))

        await self.lastChannel(message)

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

    async def fBuy(self, message):
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
                await message.channel.send(mess.format(rand.choice(self.client.data.sad)))
            else:
                try:
                    bands = self.client.data.ledger[currentPlayer]
                except KeyError:
                    bands = 0
                if tempitem['price'] > bands:
                    mess = 'sorry {}, you don\'t have enough coins to get a{} **{}** {}'
                    itemname = tempitem['stats']['name']
                    mess = mess.format(message.author.name,
                                       self.detectAn(itemname),
                                       itemname,
                                       rand.choice(self.client.data.sad))
                    await message.channel.send(mess)
                else:
                    try:
                        currentItems = self.client.games.players[currentPlayer]['fishing'][type]
                    except KeyError:
                        await self.initFishing(message)
                        currentItems = self.client.games.players[currentPlayer]['fishing'][type]

                    taken = False
                    for item in currentItems:
                        if item['name'] == tempitem['stats']['name'] and not item['multi']:
                            taken = True
                            break
                    itemname = tempitem['stats']['name']
                    if not taken:
                        self.client.games.players[currentPlayer]['fishing'][type].insert(0, copy.deepcopy(tempitem['stats']))
                        mess = 'ok {}, a{} **{}** has been added to your inventory {}'

                        try:
                            self.client.games.players[currentPlayer]['fishing']['stats']['spent'] += tempitem['price']
                        except KeyError:
                            self.client.games.players[currentPlayer]['fishing']['stats']['spent'] = tempitem['price']

                        self.client.data.ledger[currentPlayer] -= tempitem['price']
                        money = self.client.data.ledger[currentPlayer]
                        mess2 = '\n(you now have {:,.2f} VGMCoins)'.format(money)
                        mess = mess.format(message.author.name,
                                           self.detectAn(itemname),
                                           itemname,
                                           rand.choice(self.client.data.cute))
                        await message.channel.send(mess + mess2)
                        self.client.games.save()
                        self.client.storeLedger()
                    else:
                        mess = 'sorry {}, you can\'t get two **{}s** {}'
                        mess = mess.format(message.author.name,
                                           itemname,
                                           rand.choice(self.client.data.sad))
                        await message.channel.send(mess)
        else:
            mess = 'I\'m sorry, I don\'t think we have anything like that in the shop {}'
            await message.channel.send(mess.format(rand.choice(self.client.data.sad)))


    async def fForage(self, message):
        currentPlayer = str(message.author.id)
        try:
            currentState = self.client.games.players[currentPlayer]['fishing']['state']['state']
        except KeyError:
            await self.initFishing(message)
            currentState = self.client.games.players[currentPlayer]['fishing']['state']['state']
        if currentState != 'idle':
            mess = 'whoa chill u already {} {} o.o'.format(currentState, message.author.name)
            await message.channel.send(mess)
        else:
            loc = self.client.games.players[currentPlayer]['fishing']['state']['location']
            if self.locations[loc]['forage']['allowed']:
                self.client.games.players[currentPlayer]['fishing']['state']['state'] = 'forage'
                # we'll use the cast time here as well
                self.setForageTime(message)
                self.client.games.players[currentPlayer]['fishing']['lastChannel'] = message.channel.id
                loc = self.client.games.players[currentPlayer]['fishing']['state']['location']
                mess = 'Ok! you\'re now foraging at the {} {}'.format(loc, rand.choice(self.client.data.cute))
                await message.channel.send(mess)
            else:
                mess = 'I\'m sorry {}, I don\'t think you\'ll find anything around the {} {}'
                mess = mess.format(message.author.name, loc, rand.choice(self.client.data.sad))
                await message.channel.send(mess)
            await self.lastChannel(message)

    async def fSetrod(self, message):
        currentPlayer = str(message.author.id)
        try:
            rods = self.client.games.players[currentPlayer]['fishing']['rods']
        except KeyError:
            await self.initFishing(message)
            rods = self.client.games.players[currentPlayer]['fishing']['rods']

        if len(rods) == 0:
            mess = 'you don\'t have any rods {}'.format(rand.choice(self.client.data.sad))
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
                self.client.games.players[currentPlayer]['fishing']['rods'] = rods
                mess = 'Ok! A{} {} is now your primary rod {}'
                mess = mess.format(self.detectAn(selection['name']),
                                   selection['name'],
                                   rand.choice(self.client.data.cute))
                self.client.games.save()
                await message.channel.send(mess)
            except (TypeError, IndexError) as error:
                mess = 'I\'m sorry, I don\'t see anything like that in your inventory {}'
                mess = mess.format(rand.choice(self.client.data.sad))
                await message.channel.send(mess)

    async def fSetlure(self, message):
        currentPlayer = str(message.author.id)
        try:
            lures = self.client.games.players[currentPlayer]['fishing']['lures']
        except KeyError:
            await self.initFishing(message)
            lures = self.client.games.players[currentPlayer]['fishing']['lures']

        if len(lures) == 0:
            mess = 'you don\'t have any lures {}'.format(rand.choice(self.client.data.sad))
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
                self.client.games.players[currentPlayer]['fishing']['lures'] = lures
                mess = 'Ok! A{} {} is now your primary lure {}'
                mess = mess.format(self.detectAn(selection['name']),
                                   selection['name'],
                                   rand.choice(self.client.data.cute))
                self.client.games.save()
                await message.channel.send(mess)
            except (TypeError, IndexError) as error:
                mess = 'I\'m sorry, I don\'t see anything like that in your inventory {}'
                mess = mess.format(rand.choice(self.client.data.sad))
                await message.channel.send(mess)


    def verifyRecord(self, userid, fish):
        try:
            return self.client.games.misc[fish['name']]['fisher'] == userid
        except KeyError:
            return False


    def sortFish(self, fishdict):
        sortedFish = sorted(fishdict.items(), key=lambda item: item[1]['size'], reverse=True)
        sortedFish = dict(sortedFish)
        return sortedFish


    async def fishTable(self, sortedFish, all=False, total=30, userid=None):
        extra = []

        if all:
            header = [['[Fish]', 'Size', 'Fisher']]
            tempmax = total
            extra = None
        else:
            tempmax = 15
            try:
                username = self.client.data.nameCache[str(userid)]
            except KeyError:
                user = await self.client.fetch_user(userid)
                username = user.name
                self.client.data.nameCache[str(userid)] = username
            header = [['Fish', 'Size']]
            extra += [username, '[Fish] -> VGMC record']

        sf = '{:,.2f}'
        templist = []
        for num, key in enumerate(sortedFish):
            if all:
                rf = '[{}]'
                fisher = self.client.data.nameCache[str(self.client.games.misc[key]['fisher'])]
                templist.append([rf.format(key), sf.format(sortedFish[key]['size']/10), fisher])
            else:
                rf = '[{}]' if self.verifyRecord(userid, sortedFish[key]) else '{}'
                templist.append([rf.format(key), sf.format(sortedFish[key]['size']/10)])
            if num > tempmax:
                break

        return utils.tablegen(header + templist, header=True, extra=extra)


    async def fListfish(self, message):
        arg1 = message.content.find('.listfish')
        arg1 = message.content[arg1 + 10:].split(' ')[0]
        if arg1 == '' or arg1.lower() == 'all':
            tempmax = 50
            if len(self.client.games.misc) == 0:
                mess = 'no records yet {}'.format(rand.choice(self.client.data.sad))
                await message.channel.send(mess)
                return
            mess = 'Here\'s the top {} fish from the VGMSea {}'
            await message.channel.send(mess.format(tempmax, rand.choice(self.client.data.cute)))
            sortedFish = self.sortFish(self.client.games.misc)
            tempstr = await self.fishTable(sortedFish, all=True, total=tempmax)
            self.client.storeNameCache()
        elif arg1.lower() == 'me':
            tempmax = 15
            try:
                mefish = self.client.games.players[str(message.author.id)]['fishing']['records']
            except KeyError:
                self.initFishing(message)
            if len(mefish) == 0:
                mess = 'no records yet {}'.format(rand.choice(self.client.data.sad))
                await message.channel.send(mess)
                return
            sortedFish = self.sortFish(mefish)
            mess = 'Here\'s your top {} fish from the VGMSea {}'
            await message.channel.send(mess.format(tempmax, rand.choice(self.client.data.cute)))
            tempstr = await self.fishTable(sortedFish, total=tempmax, userid=message.author.id)
        elif user_regex.search(arg1) is not None:
            tempmax = 15
            userid = getUserFromMention(arg1)
            try:
                mefish = self.client.games.players[str(userid)]['fishing']['records']
            except KeyError:
                mess = 'no records yet {}'.format(rand.choice(self.client.data.sad))
                await message.channel.send(mess)
                return
            if len(mefish) == 0:
                mess = 'no records yet {}'.format(rand.choice(self.client.data.sad))
                await message.channel.send(mess)
                return
            sortedFish = self.sortFish(mefish)
            mess = 'Here\'s {}\'s top {} fish from the VGMSea {}'
            await message.channel.send(mess.format(arg1, tempmax, rand.choice(self.client.data.cute)))
            tempstr = await self.fishTable(sortedFish, total=tempmax, userid=userid)
        else:
            mess = 'Sorry, I don\'t understand \"{}\" {}'
            await message.channel.send(mess.format(arg1, rand.choice(self.client.data.sad)))
            return

        await utils.sendBigMess(message, tempstr)


    async def fRecycle(self, message):
        currentPlayer = str(message.author.id)
        try:
            currentState = self.client.games.players[currentPlayer]['fishing']['state']['state']
        except KeyError:
            await self.initFishing(message)
            currentState = self.client.games.players[currentPlayer]['fishing']['state']['state']
        if currentState != 'idle':
            mess = 'whoa wait let\'s chill until you\'re done with that {} {} o.o'.format(currentState, message.author.name)
            await message.channel.send(mess)

        if len(self.client.games.players[currentPlayer]['fishing']['rods']) > 0:
            worstIndex = -1
            worstDamage = -1

            for index, lure in enumerate(self.client.games.players[currentPlayer]['fishing']['lures']):
                if lure['name'] == self.newLure()['name'] and lure['damage'] > worstDamage:
                    worstIndex = index
                    worstDamage = lure['damage']

            if worstIndex == -1:
                mess = 'hey {}, looks like you don\'t have any broken cans {}'
                mess = mess.format(message.author.name, rand.choice(self.client.data.sad))
            else:
                self.client.games.players[currentPlayer]['fishing']['lures'].pop(worstIndex)
                mess = 'ok {}, I **responsibly** recycled your worst broken can {}'
                mess = mess.format(message.author.name, rand.choice(self.client.data.cute))
                self.client.games.save()
        else:
            mess = 'hey {}, looks like you don\'t have any broken cans {}'
            mess = mess.format(message.author.name, rand.choice(self.client.data.sad))

        await message.channel.send(mess)
        pass

    async def lIdle(self, playerKey, players):
        pass

    def calcDamage(self, size):
        if size <= 0:
            return 0
        # size /= 10
        # srange = 150
        maxCoins = 10
        #
        # if size > srange:
        #     return maxCoins
        # else:
        #     return round(math.sin(size*2*math.pi/(srange*4))*maxCoins, 2)

        # exponential (too much)
        # sizeRaw = max(utils.remap(size, self.minSize, self.maxSize, 0, 1), 0.001)
        # sizeRaw = min(sizeRaw, 1.3)
        # sizeRaw = min(utils.expBias(sizeRaw, 0.19, steep=0.5), 2)
        # return round(sizeRaw*maxCoins, 2)

        sizeRaw = utils.clamp(utils.remap(size, self.minSize, self.maxSize, 0.01, 1), 0.01, 2)
        return sizeRaw*maxCoins


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

    def applyDamage(self, playerKey, players, size, playerName):
        damage = self.calcDamage(size)
        players[playerKey]['fishing']['rods'][0]['damage'] += damage/2
        players[playerKey]['fishing']['lures'][0]['damage'] += damage/2
        # lastChannel = await client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
        tempstr = ''

        if players[playerKey]['fishing']['rods'][0]['damage'] >= players[playerKey]['fishing']['rods'][0]['durability']:
            name = players[playerKey]['fishing']['rods'][0]['name']
            mess = '\noh no! your **{}** broke, {} {}'.format(name, playerName.name, rand.choice(self.client.data.sad))
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
            mess = '\noh no! your **{}** broke, {} {}'.format(name, playerName.name, rand.choice(self.client.data.sad))
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

    def addCoins(self, playerKey, players, value):
        # lastChannel = await client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
        mess = '\nI\'d say that\'s worth about {:,.2f} VGMCoin{} {}'
        ess = 's'
        if round(value, 2) == 1:
            ess = ''
        mess = mess.format(value, ess, rand.choice(self.client.data.cute))
        try:
            self.client.data.ledger[playerKey] += value
        except KeyError:
            self.client.data.ledger[playerKey] = value
        return mess
        # await lastChannel.send(mess)

    async def checkRecord(self, playerkey, players, catch):
        record = False
        try:
            if catch['size'] > self.client.games.misc[catch['name']]['size']:
                # prevname = await self.client.fetch_user(self.client.games.misc[catch['name']]['fisher'])
                try:
                    prevname = self.client.data.nameCache[str(self.client.games.misc[catch['name']]['fisher'])]
                except KeyError:
                    prevname = await self.client.fetch_user(int(self.client.games.misc[catch['name']]['fisher']))
                    prevname = prevname.name
                prev = self.client.games.misc[catch['name']]
                self.client.games.misc[catch['name']] = catch
                self.client.games.misc[catch['name']]['fisher'] = playerkey
                mess = '\n**Wow! That\'s a new VGMC record! {} (you beat {}\'s record of {:,.2f} cm!) +1 coin!**'
                mess = mess.format(rand.choice(self.client.data.cute), prevname, prev['catch']/10)
                return mess
            else:
                return ''
        except KeyError:
            self.client.games.misc[catch['name']] = catch
            self.client.games.misc[catch['name']]['fisher'] = int(playerkey)
            mess = '\n**Wow! That\'s a new VGMC record! +1 coin!**'
            mess = mess.format(rand.choice(self.client.data.cute))
            return mess

    def catchChance(self, totalEff):
        return utils.remap(totalEff, self.minEff, self.maxEff, 0.4, 0.7)

    async def lCast(self, playerKey, players):
        players[playerKey]['fishing']['state']['timeCast'] -= 1
        if players[playerKey]['fishing']['state']['timeCast'] <= 0:
            lastChannel = await self.client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
            playerName = await self.client.fetch_user(int(playerKey))
            # 50 50 chance of catching
            # probability of catch related to efficacy
            totalEff = players[playerKey]['fishing']['rods'][0]['efficacy']
            totalEff += players[playerKey]['fishing']['lures'][0]['efficacy']
            # print(0.4 - 0.1*totalEff)

            hooked = False
            chances = self.catchChance(totalEff)
            if rand.random() <= chances:
                hooked = True
                players[playerKey]['fishing']['state']['prevnibs'] = 0
            else:
                players[playerKey]['fishing']['state']['prevnibs'] += 1
                if players[playerKey]['fishing']['state']['prevnibs'] > 4:
                    hooked = True
                    players[playerKey]['fishing']['state']['prevnibs'] = 0

            if hooked:
                #caught
                catch, valid = self.retrieveFish(players[playerKey]['fishing']['state']['location'], bias=totalEff)

                if not valid:
                    tempstring = 'shoot! it got away... i think the fish here are too big for your gear {}'.format(rand.choice(self.client.data.sad))
                    tempstring += self.applyDamage(playerKey, players, catch['size'], playerName)
                    players[playerKey]['fishing']['state']['state'] = 'idle'
                    await lastChannel.send(tempstring)
                    try:
                        players[playerKey]['fishing']['stats']['nibbles'] += 1
                    except KeyError:
                        players[playerKey]['fishing']['stats']['nibbles'] = 1
                    self.client.storeLedger()
                    self.client.games.save()
                    return
                else:
                    try:
                        players[playerKey]['fishing']['stats']['hooked'] += 1
                    except KeyError:
                        players[playerKey]['fishing']['stats']['hooked'] = 1
                    tempstring = self.fishLine(catch)
                newClubRecord = 0
                # await lastChannel.send(self.fishLine(catch))

                try:
                    if players[playerKey]['fishing']['records'][catch['name']]['size'] < catch['size']:
                        prev = players[playerKey]['fishing']['records'][catch['name']]['size']
                        players[playerKey]['fishing']['records'][catch['name']] = catch
                        mess = '\n✿✿ hey that\'s a new personal best! {} **+1 coin** '.format(rand.choice(self.client.data.cute))
                        mess += 'your previous best was {:,.2f} cm! ✿✿'.format(prev/10)
                        tempmess = await self.checkRecord(playerKey, players, catch)
                        mess += tempmess
                        newClubRecord += 0.2
                        if len(tempmess) > 0:
                            newClubRecord += 0.2 # new record

                        tempstring += mess
                        # add coins here
                except KeyError:
                    mess = '\n✿✿ oh that\'s your first {} {} **+0.5 coins** ✿✿'.format(catch['name'], rand.choice(self.client.data.cute))
                    players[playerKey]['fishing']['records'][catch['name']] = catch
                    tempmess = await self.checkRecord(playerKey, players, catch)
                    mess += tempmess
                    newClubRecord += 0.1
                    if len(tempmess) > 0:
                        newClubRecord += 0.2 # new record
                    # await lastChannel.send(mess)
                    tempstring += mess
                    # add coins here
                tempstring += self.applyDamage(playerKey, players, catch['size'], playerName)
                money = self.calcDamage(catch['size'])*1.35 + newClubRecord*5
                tempstring += self.addCoins(playerKey, players, money)

                # Stats collection

                try:
                    players[playerKey]['fishing']['stats']['earned'] += money
                except KeyError:
                    players[playerKey]['fishing']['stats']['earned'] = money

                try:
                    players[playerKey]['fishing']['stats']['numfish'][catch['name']] += 1
                except KeyError:
                    try:
                        players[playerKey]['fishing']['stats']['numfish'][catch['name']] = 1
                    except KeyError:
                        players[playerKey]['fishing']['stats']['numfish'] = {catch['name']: 1}

                # endstats
                players[playerKey]['fishing']['state']['state'] = 'idle'
                await lastChannel.send(tempstring)
                self.client.storeLedger()
            else:
                mess = 'you got a nibble! but it got away {}'.format(rand.choice(self.client.data.sad))
                # await lastChannel.send(mess)
                mess +=  self.applyDamage(playerKey, players, 10, playerName)
                await lastChannel.send(mess)
                players[playerKey]['fishing']['state']['state'] = 'idle'

                try:
                    players[playerKey]['fishing']['stats']['nibbles'] += 1
                except KeyError:
                    players[playerKey]['fishing']['stats']['nibbles'] = 1


            totalRecords = self.checkNumRecords(str(playerKey))
            try:
                if totalRecords > players[playerKey]['fishing']['stats']['records']:
                    players[playerKey]['fishing']['stats']['records'] = totalRecords
            except KeyError:
                players[playerKey]['fishing']['stats']['records'] = totalRecords
            self.client.games.save()

    async def lForage(self, playerKey, players):
        players[playerKey]['fishing']['state']['timeCast'] -= 1
        if players[playerKey]['fishing']['state']['timeCast'] <= 0:
            lastChannel = await self.client.fetch_channel(players[playerKey]['fishing']['lastChannel'])
            playerName = await self.client.fetch_user(int(playerKey))
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
                                   rand.choice(self.client.data.cute))

                players[playerKey]['fishing'][item['type']].insert(0, item)
                await lastChannel.send(mess)
                players[playerKey]['fishing']['state']['state'] = 'idle'
                self.client.games.save()

            else:
                mess = 'shoot {}, looks like you didn\'t find anything {}'.format(playerName.name, rand.choice(self.client.data.sad))
                await lastChannel.send(mess)
                players[playerKey]['fishing']['state']['state'] = 'idle'


# if __name__ == '__main__':
#     catch = retrieveFish(fishLocations, fishCatalog, 'boat', bias=0)
#     print(fishLine(fishLocations, fishCatalog, catch))
