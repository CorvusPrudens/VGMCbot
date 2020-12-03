import discord
import asyncio
import re
import games.games as games
import data
import utils
import random as rand

class extClient(discord.Client):
    def __init__(self, funcDict, peasantCommands, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.funcDict = funcDict
        # self.peasantCommands = peasantCommands

        # self.games = games.Games()
        #
        # self.commands.update(games.funcDict)
        # self.peasantCommands += games.commandString
        self.bg_task = self.loop.create_task(self.gameLoop())
        self.counter = 0

        self.data = data.Data()

        commRegexString = '\\b('
        for key in self.data.funDict:
            commRegexString += '({})|'.format(key)
        self.commRegex = re.compile(commRegexString[:-1] + ')\\b')

        # this dictionary allows us to cleanly call the defined
        # functions without explicitly checking for the
        # commands in an if elif etc block

        # while it is technically 'data,' I chose to include it
        # here for clarity and to make sure the functions are
        # properly defined before passing them to the dict

        self.funcDict = {
            'give': self.fGive,
            'help': self.fHelp,
            'hmc': self.fHmc,
            'list': self.fList,
            'uwu': self.fUwu,
            'morning': self.fTime,
            'night': self.fTime,
            'count': self.fCount
        }

    async def gameLoop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            self.counter += 1
            # print(self.counter)
            await asyncio.sleep(1) # task runs every 60 seconds

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

    async def execComm(self, message):
        await self.funcDict[command](message)

    ################################################################################
    ########################## on_reaction functions ###############################
    ################################################################################

    async def reactionAdd(self, reaction, user):
        name = utils.getReactionName(str(reaction), self.data.reactRegex)

        if name != None and name == 'VGMCoin':
            try:
                giver = self.data.bank[user.id]
            except KeyError:
                self.data.bank[user.id] = 0
            try:
                receiver = self.data.bank[reaction.message.author.id]
            except KeyError:
                self.data.bank[reaction.message.author.id] = 0

            if self.data.bank[user.id] >= 1:
                self.data.bank[user.id] -= 1
                self.data.bank[reaction.message.author.id] += 1
                self.storeBank()
            else:
                await reaction.message.remove_reaction(reaction.emoji, user)

    async def reactionRemove(self, reaction, user):
        name = utils.getReactionName(str(reaction), self.data.reactRegex)

        if name != None and name == 'VGMCoin':
            try:
                taker = self.data.bank[user.id]
            except KeyError:
                self.data.bank[user.id] = 0
            try:
                victim = self.data.bank[reaction.message.author.id]
            except KeyError:
                self.data.bank[reaction.message.author.id] = 0

            # This is a bit troll since people can be put into debt if someone
            # removes a coin while the debtor has less than one coin
            self.data.bank[reaction.message.author.id] -= 1
            self.data.bank[user.id] += 1
            self.storeBank()

    ################################################################################
    ########################## on_message functions ################################
    ################################################################################

    async def preMention(self, message):
        # this global crap is messy and needs to be cleaned up
        global prevChoice
        if self.data.honkRegex.search(message.content.lower()) != None:
            currentChoice = rand.randrange(5)
            while currentChoice == prevChoice:
                currentChoice = rand.randrange(5)
            prevChoice = currentChoice
            url = imgur + honks[currentChoice] + end
            await message.channel.send(url)
        elif self.data.hankRegex.search(message.content.lower()) != None:
            await message.channel.send(hankUrl1 + hankUrl2 + hankUrl3)

    async def fGive(self, message):
        if utils.hasPermission(message.author, leader):
            # bit ugly but...
            sanitized = message.content.replace('<', ' <').replace('>', '> ')
            sanitized = sanitized.replace('  ', ' ')
            tokens = sanitized.split(' ')
            data = utils.extractValue(tokens, 'give')
            user = utils.getUserFromMention(data['name'], self.data.mentionRegex)
            if data['value'] == None or user == None:
                mess = responses['giveErr'].format(message.author.mention, rand.choice(sad))
                await message.channel.send(mess)
            else:
                try:
                    self.data.bank[user] += data['value']
                except KeyError:
                    self.data.bank[user] = data['value']
                self.storeBank()
                mess = responses['give'].format(data['name'], self.data.bank[user], rand.choice(cute))
                if self.data.bank[user] == 1:
                    mess = mess.replace('VGMCoins', 'VGMCoin')
                await message.channel.send(mess)
        else:
            mess = responses['permission'].format(message.author.mention, rand.choice(sad))
            await message.channel.send(mess)

    async def fHelp(self, message):
        tempstr = commandsHeader.format(rand.choice(cute))
        if utils.hasPermission(message.author, leader):
            tempstr += leaderCommands
        await message.channel.send(tempstr + self.peasantCommands)

    async def fHmc(self, message):
        try:
            value = self.data.bank[message.author.id]
        except KeyError:
            value = 0
        mess = responses['hmc'].format(message.author.mention, value, rand.choice(cute))
        if value == 1:
            mess = mess.replace('VGMCoins', 'VGMCoin')
        await message.channel.send(mess)

    async def fList(self, message):
        await message.channel.send(responses['list'].format(rand.choice(cute)))
        tempstr = ''
        templist = []
        longest = 0
        sortedBank = sorted(self.data.bank.items(), key=lambda item: item[1], reverse=True)
        sortedBank = dict(sortedBank)
        # can't really use longest yet, but maybe we'll find a use eventually
        for key in sortedBank:
            fetched = await self.fetch_user(key)
            templist.append([fetched.name, sortedBank[key]])
            if len(fetched.name) > longest:
                longest = len(fetched.name)
        for pair in templist:
            if pair[1] != 0:
                tempstr += responses['listItem'].format(pair[0], pair[1])
        await message.channel.send(tempstr)

    async def fUwu(self, message):
        await message.channel.send(responses['uwu'].format(rand.choice(cute)))

    async def fTime(self, message):
        time = self.data.timePartRegex.search(message.content.lower())
        if time != None:
            period = time.group(0)
            hour = await utils.getHour(self.data.timeRegex)
            if period == 'morning':
                if hour>timeBound['morning'][0] and hour < timeBound['morning'][1]:
                    mess = responses['time'].format('morning', rand.choice(cute))
                    await message.channel.send(mess)
                else:
                    mess = responses['nottime'].format('morning', rand.choice(sad))
                    await message.channel.send(mess)
            elif period == 'night':
                if hour > timeBound['night'][0] or hour < timeBound['night'][1]:
                    mess = responses['time'].format('night', rand.choice(cute))
                    await message.channel.send(mess)
                else:
                    mess = responses['nottime'].format('night', rand.choice(sad))
                    await message.channel.send(mess)

    async def fCount(self, message):
        await message.channel.send(str(self.counter))
