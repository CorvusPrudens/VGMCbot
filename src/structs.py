import aiohttp
import discord
import asyncio
import re
from games import games
import data
import utils
import random as rand

class extClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            'count': self.fCount,
            'addimg': self.fAddimg,
            'mgmvote': self.fMgmvote,
            'mgmwin': self.fMgmwin,
        }

        self.data = data.Data()

        self.games = games.Games('games/players.csv')
        #
        # self.funcDict.update(self.games.commands)
        # print(self.funcDict)
        self.data.peasantCommands += self.games.commandString
        self.bg_task = self.loop.create_task(self.gameLoop())
        self.counter = 0

        commRegexString = '\\b('
        for key in self.funcDict:
            commRegexString += '({})|'.format(key)
        for key in self.games.commands:
            commRegexString += '({})|'.format(key)
        self.commRegex = re.compile(commRegexString[:-1] + ')\\b')

    async def gameLoop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            self.counter += 1
            await self.games.gameLoop(self)
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
                self.checkVoteAdd(reaction)
            else:
                self.data.bank[user.id] -= 1
                self.data.bank[reaction.message.author.id] += 1
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
            data = utils.extractValue(tokens, 'give')
            user = utils.getUserFromMention(data['name'], self.data.mentionRegex)
            if data['value'] == None or user == None:
                mess = self.data.responses['giveErr'].format(message.author.mention, rand.choice(self.data.sad))
                await message.channel.send(mess)
            else:
                try:
                    self.data.bank[user] += data['value']
                except KeyError:
                    self.data.bank[user] = data['value']
                self.storeBank()
                mess = self.data.responses['give'].format(data['name'], self.data.bank[user], rand.choice(self.data.cute))
                if self.data.bank[user] == 1:
                    mess = mess.replace('VGMCoins', 'VGMCoin')
                await message.channel.send(mess)
        else:
            mess = self.data.responses['permission'].format(message.author.mention, rand.choice(self.data.sad))
            await message.channel.send(mess)

    async def fHelp(self, message):
        tempstr = self.data.commandsHeader.format(rand.choice(self.data.cute))
        if utils.hasPermission(message.author, self.data.leader):
            tempstr += self.data.leaderCommands
        await message.channel.send(tempstr + self.data.peasantCommands)

    async def fHmc(self, message):
        try:
            value = self.data.bank[message.author.id]
        except KeyError:
            value = 0
        mess = self.data.responses['hmc'].format(message.author.mention, value, rand.choice(self.data.cute))
        if value == 1:
            mess = mess.replace('VGMCoins', 'VGMCoin')
        await message.channel.send(mess)

    async def fList(self, message):
        await message.channel.send(self.data.responses['list'].format(rand.choice(self.data.cute)))
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
                tempstr += self.data.responses['listItem'].format(pair[0], pair[1])
        await message.channel.send(tempstr)

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
                if tokens[i] == 'addimg':
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
