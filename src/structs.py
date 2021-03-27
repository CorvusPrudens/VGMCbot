import aiohttp
import discord
import asyncio
import json
import re
import random as rand

from games import games
import data
import utils


class extendedClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # this dictionary allows us to cleanly call the defined
        # functions without explicitly checking for the
        # commands in an if elif etc block

        self.funcDict = {
            '.give': self.fGive,
            '.help': self.fHelp,
            '.hmc': self.fHmc,
            '.coins': self.fHmc,
            '.list': self.fList,
            '.uwu': self.fUwu,
            '.morning': self.fTime,
            '.night': self.fTime,
            '.count': self.fCount,
            '.addimg': self.fAddimg,
            '.mgmvote': self.fMgmvote,
            '.mgmwin': self.fMgmwin,
            '.gimme': self.fGimme,
        }

        self.data = data.Data()

        self.helpDict = {'normal': self.data.peasantCommands,
                         'leader': self.data.leaderCommands}

        self.games = games.Games('games/players.json', 'games/fishing/misc.json')
        #
        # self.funcDict.update(self.games.commands)
        # print(self.funcDict)
        self.helpDict.update(self.games.helpDict)

        helpOptions = ''
        for key in self.helpDict:
            helpOptions += key + ', '
        helpOptions = helpOptions[:-2]
        self.helpDict['normal'] = self.helpDict['normal'].format(helpOptions)
        self.bg_task = self.loop.create_task(self.gameLoop())
        self.counter = 0

        commRegexString = '('
        for key in self.funcDict:
            commRegexString += '(\\{})|'.format(key)
        for key in self.games.commands:
            commRegexString += '(\\{})|'.format(key)
        self.commRegex = re.compile(commRegexString[:-1] + ')\\b')

        # WARNING: HARDCODED
        self.nameRegex = re.compile('\\b@(({})|({}))\\b'.format('VGMCbot', 'VGMCtest'))

    async def gameLoop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            self.counter += 1
            await self.games.gameLoop(self)
            await asyncio.sleep(1) # task runs every second


    def loadBank(self):
        try:
            with open(self.data.cachePath, 'r') as file:
                for line in file:
                    tokens = line.replace('\n', '').split(',')
                    if len(line.replace('\n', '')) > 0:
                        self.data.bank[int(tokens[0])] = float(tokens[1])
        except FileNotFoundError:
            pass

    def storeBank(self):
        with open(self.data.cachePath, 'w') as file:
            for key in self.data.bank:
                file.write(f'{key},{self.data.bank[key]}\n')

    def loadLedger(self):
        try:
            with open(self.data.ledgerPath, 'r') as file:
                self.data.ledger = json.load(file)
        except FileNotFoundError:
            pass

    def storeLedger(self):
        with open(self.data.ledgerPath, 'w') as file:
            json.dump(self.data.ledger, file, indent=2)

    def loadNameCache(self):
        try:
            with open(self.data.nameCachePath, 'r') as file:
                self.data.nameCache = json.load(file)
        except FileNotFoundError:
            pass

    def storeNameCache(self):
        with open(self.data.nameCachePath, 'w') as file:
            json.dump(self.data.nameCache, file, indent=2)

    async def execComm(self, command, message):
        try:
            await self.funcDict[command](message)
        except KeyError:
            await self.games.execComm(command, message, self)

    async def getHour(self):
        response = {'datetime': ''}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.data.timeUrl) as r:
                if r.status == 200:
                    response = await r.json()
        hour = self.data.timeRegex.search(response['datetime'])
        if hour == None:
            return None
        else:
            return int(hour.group(0))

    def mentioned(self, message):
        men = False
        if self.user.mentioned_in(message):
            men = True
        elif self.nameRegex.search(message.content) != None:
            men = True
        return men

    ################################################################################
    ########################## on_reaction functions ###############################
    ################################################################################

    def checkVoteAdd(self, reaction):
        for i in range(len(self.data.mgm)):
            if reaction.message.id == self.data.mgm[i]['id']:
                self.data.mgm[i]['votes'] += 1
                break

    async def reactionAdd(self, reaction, user):
        name = utils.getReactionName(str(reaction), self.data.reactRegex)

        if name != None and name == 'VGMCoin':
            try:
                giver = self.data.ledger[str(user.id)]
            except KeyError:
                self.data.ledger[str(user.id)] = 0
            try:
                receiver = self.data.ledger[str(reaction.message.author.id)]
            except KeyError:
                self.data.ledger[str(reaction.message.author.id)] = 0

            if self.data.ledger[str(user.id)] >= 1:
                self.data.ledger[str(user.id)] -= 1
                self.data.ledger[str(reaction.message.author.id)] += 1
                self.storeLedger()
                self.checkVoteAdd(reaction)
            else:
                self.data.ledger[str(user.id)] -= 1
                self.data.ledger[str(reaction.message.author.id)] += 1
                # this then triggers the reactionRemove event
                self.checkVoteAdd(reaction)
                await reaction.message.remove_reaction(reaction.emoji, user)

    def checkVoteRemove(self, reaction):
        for i in range(len(self.data.mgm)):
            if reaction.message.id == self.data.mgm[i]['id']:
                self.data.mgm[i]['votes'] -= 1
                break

    async def reactionRemove(self, reaction, user):
        name = utils.getReactionName(str(reaction), self.data.reactRegex)

        if name != None and name == 'VGMCoin':
            try:
                taker = self.data.ledger[str(user.id)]
            except KeyError:
                self.data.ledger[str(user.id)] = 0
            try:
                victim = self.data.ledger[str(reaction.message.author.id)]
            except KeyError:
                self.data.ledger[str(reaction.message.author.id)] = 0

            # This is a bit troll since people can be put into debt if someone
            # removes a coin while the debtor has less than one coin
            self.data.ledger[str(reaction.message.author.id)] -= 1
            self.data.ledger[str(user.id)] += 1
            self.storeLedger()
            self.checkVoteRemove(reaction)

    ################################################################################
    ########################## on_message functions ################################
    ################################################################################

    async def preMention(self, message):
        if self.data.honkRegex.search(message.content.lower()) != None:
            currentChoice = rand.randrange(5)
            while currentChoice == self.data.prevChoice:
                currentChoice = rand.randrange(5)
            self.data.prevChoice = currentChoice
            url = self.data.imgur + self.data.honks[currentChoice] + self.data.end
            await message.channel.send(url)
        elif self.data.hankRegex.search(message.content.lower()) != None:
            await message.channel.send(self.data.hankUrl1 + self.data.hankUrl2 + self.data.hankUrl3)

    async def fGive(self, message):
        if utils.hasPermission(message.author, self.data.leader):
            # bit ugly but...
            sanitized = message.content.replace('<', ' <').replace('>', '> ')
            sanitized = sanitized.replace('  ', ' ')
            tokens = sanitized.split(' ')
            data = utils.extractValue(tokens, '.give')
            user = utils.getUserFromMention(data['name'], self.data.mentionRegex)
            if data['value'] == None or user == None:
                mess = self.data.responses['giveErr'].format(message.author.mention, rand.choice(self.data.sad))
                await message.channel.send(mess)
            else:
                try:
                    self.data.ledger[str(user)] += data['value']
                except KeyError:
                    self.data.ledger[str(user)] = data['value']
                self.storeLedger()
                mess = self.data.responses['give'].format(data['name'], self.data.ledger[str(user)], rand.choice(self.data.cute))
                if round(self.data.ledger[str(user)], 2) == 1:
                    mess = mess.replace('VGMCoins', 'VGMCoin')
                await message.channel.send(mess)
        else:
            mess = self.data.responses['permission'].format(message.author.mention, rand.choice(self.data.sad))
            await message.channel.send(mess)

    async def fHelp(self, message):
        tempstr = self.data.commandsHeader.format(rand.choice(self.data.cute))
        tokens = message.content.lower().split(' ')
        type = 'normal'
        for i in range(len(tokens)):
            if tokens[i] == '.help':
                if i != len(tokens) - 1:
                    type = tokens[i + 1]
                    break
        try:
            tempstr += self.helpDict[type]
            await message.channel.send(tempstr)
        except KeyError:
            mess = 'I\'m sorry, I don\'t think we have any commands like that {}'
            mess = mess.format(rand.choice(self.data.sad))
            await message.channel.send(mess)

    async def fHmc(self, message):
        try:
            value = self.data.ledger[str(message.author.id)]
        except KeyError:
            value = 0
        mess = self.data.responses['hmc'].format(message.author.mention, value, rand.choice(self.data.cute))
        if value == 1:
            mess = mess.replace('VGMCoins', 'VGMCoin')
        await message.channel.send(mess)


    async def fList(self, message):
        if self.data.ledger is None:
            await message.channel.send("Looks like there's no connoisseurs, here... {}".format(rand.choice(self.data.sad)))
            return
        await message.channel.send(self.data.responses['list'].format(rand.choice(self.data.cute)))
        tempstr = '```\n'
        templist = []
        longest = 0
        longestValue = 0
        sortedLedger = sorted(self.data.ledger.items(), key=lambda item: item[1], reverse=True)
        sortedLedger = dict(sortedLedger)
        maxNameLen = 16
        for key in sortedLedger:
            try:
                fetched = self.data.nameCache[key]
            except KeyError:
                user = await self.fetch_user(key)
                fetched = user.name
                self.data.nameCache[key] = fetched
            if len(fetched) > longest:
                longest = len(fetched)
            valstr = '{:,.2f}'.format(sortedLedger[key])
            if len(valstr) > longestValue:
                longestValue = len(valstr)

        if len('VGMCoins') > longestValue:
            longestValue = len('VGMCoins')

        longest = maxNameLen if longest > maxNameLen else longest

        header = '✿ Connoisseur' + ' '*(longest - 10) + '| VGMCoins' + ' '*(longestValue - 8) + ' ;\n'
        headfoot = '✿ ' + '='*(longest + 1) + '+' + '='*(longestValue + 1) + ' ;\n'

        tempstr += header
        tempstr += headfoot

        for key in sortedLedger:
            if sortedLedger[key] == 0:
                continue
            fetched = self.data.nameCache[key]
            if len(fetched) > longest:
                fetched = fetched[:longest - 3] + '...'
            nameSpace = ' '*(longest - len(fetched))
            valstr = '{:,.2f}'.format(sortedLedger[key])
            valueSpace = ' '*(longestValue - len(valstr))
            tempstr += '✿ {}{} | {}{} ;\n'.format(fetched, nameSpace, valstr, valueSpace)

            templist.append([fetched, sortedLedger[key]])

        tempstr += headfoot + '```'
        self.storeNameCache()
        # await message.channel.send(tempstr)
        await utils.sendBigMess(message, tempstr)

    async def fUwu(self, message):
        await message.channel.send(self.data.responses['uwu'].format(rand.choice(self.data.cute)))

    async def fTime(self, message):
        time = self.data.timePartRegex.search(message.content.lower())
        if time != None:
            period = time.group(0)
            hour = await self.getHour()
            if period == 'morning':
                if  hour == None or (hour>self.data.timeBound['morning'][0] and hour < self.data.timeBound['morning'][1]):
                    mess = self.data.responses['time'].format('morning', rand.choice(self.data.cute))
                    await message.channel.send(mess)
                else:
                    mess = self.data.responses['nottime'].format('morning', rand.choice(self.data.sad))
                    await message.channel.send(mess)
            elif period == 'night':
                if hour == None or (hour > self.data.timeBound['night'][0] or hour < self.data.timeBound['night'][1]):
                    mess = self.data.responses['time'].format('night', rand.choice(self.data.cute))
                    await message.channel.send(mess)
                else:
                    mess = self.data.responses['nottime'].format('night', rand.choice(self.data.sad))
                    await message.channel.send(mess)

    async def fCount(self, message):
        await message.channel.send(str(self.counter))

    async def fAddimg(self, message):
        # print(message.content)
        if utils.hasPermission(message.author, self.data.leader):
            tokens = utils.sanitizedTokens(message.content)
            for i in range(len(tokens)):
                if tokens[i] == '.addimg':
                    if i < len(tokens) - 1:
                        self.data.mgm.append({'url': tokens[i + 1], 'votes': 0, 'id': -1})
                        mess = self.data.responses['addimg'].format(rand.choice(self.data.cute))
                        await message.channel.send(mess)
                    else:
                        mess = self.data.responses['addimgErr'].format(rand.choice(self.data.sad))
                        await message.channel.send(mess)
        else:
            mess = self.data.responses['addimgPerm'].format(message.author.mention, rand.choice(self.data.sad))
            await message.channel.send(mess)

    async def fMgmvote(self, message):
        if utils.hasPermission(message.author, self.data.leader):
            if len(self.data.mgm) == 0:
                mess = self.data.responses['mgmvoteErr'].format(rand.choice(self.data.sad))
                await message.channel.send(mess)
            else:
                deats = '(make sure you react to the images, not the text above)'
                mess = 'Ok everyone, vote with your coins! {} {}'.format(rand.choice(self.data.cute), deats)
                await message.channel.send(mess)
                for i in range(len(self.data.mgm)):
                    string = 'Image {}'.format(i + 1)
                    await message.channel.send(string)
                    newMess = await message.channel.send(self.data.mgm[i]['url'])
                    self.data.mgm[i]['id'] = newMess.id
                await message.channel.send('have fun! {}'.format(rand.choice(self.data.cute)))
        else:
            mess = self.data.responses['mgmvotePerm'].format(message.author.mention, rand.choice(self.data.sad))
            await message.channel.send(mess)

    def mgmkey(self, dict):
        return dict['votes']

    async def fMgmwin(self, message):
        if utils.hasPermission(message.author, self.data.leader):
            self.data.mgm.sort(key=self.mgmkey, reverse=True)
            if len(self.data.mgm) > 4:
                self.data.mgm = self.data.mgm[:4]

            mess = 'And the winners are....'
            await message.channel.send(mess)
            await asyncio.sleep(1)
            for img in self.data.mgm:
                ess = 's'
                if img['votes'] == 1:
                    ess = ''
                mess = '{} vote{}:'.format(img['votes'], ess)
                await message.channel.send(mess)
                await message.channel.send(img['url'])
            await message.channel.send('Thanks for voting everyone! {}'.format(rand.choice(self.data.cute)))
            self.data.mgm = []
        else:
            mess = self.data.responses['mgmwinPerm'].format(message.author.mention, rand.choice(self.data.sad))
            await message.channel.send(mess)

    async def fGimme(self, message):
        mess = f'sorry... no {rand.choice(self.data.sad)}'
        await message.channel.send(mess)
