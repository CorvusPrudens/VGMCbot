import asyncio
import json
import re
import random as rand

import discord

from games import games
import data
import utils


class ExtendedClient(discord.Client):
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
            '.roll': self.fRoll,
        }

        self.data = data.Data()

        self.helpDict = {'normal': self.data.peasantCommands,
                         'leader': self.data.leaderCommands}

        self.games = games.Games('games/players.json', 'games/fishing/misc.json', self)

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
            await self.games.gameLoop()
            await asyncio.sleep(1) # task runs every second


    def gameDecorators(self, slash, guilds):
        self.games.gameDecorators(slash, guilds)


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
            await self.games.execComm(command, message)


    def mentioned(self, message):
        men = False
        if self.user.mentioned_in(message):
            men = True
        elif self.nameRegex.search(message.content) is not None:
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

        if name is not None and name == 'VGMCoin':
            try:
                self.data.ledger[str(user.id)]
            except KeyError:
                self.data.ledger[str(user.id)] = 0
            try:
                self.data.ledger[str(reaction.message.author.id)]
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

        if name is not None and name == 'VGMCoin':
            try:
                self.data.ledger[str(user.id)]
            except KeyError:
                self.data.ledger[str(user.id)] = 0
            try:
                self.data.ledger[str(reaction.message.author.id)]
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
        if self.data.honkRegex.search(message.content.lower()) is not None:
            currentChoice = rand.randrange(5)
            while currentChoice == self.data.prevChoice:
                currentChoice = rand.randrange(5)
            self.data.prevChoice = currentChoice
            url = self.data.imgur + self.data.honks[currentChoice] + self.data.end
            await message.channel.send(url)
        elif self.data.hankRegex.search(message.content.lower()) is not None:
            await message.channel.send(self.data.hankUrl1 + self.data.hankUrl2 + self.data.hankUrl3)

    async def fGive(self, message):
        if utils.hasPermission(message.author, self.data.leader):
            # bit ugly but...
            sanitized = message.content.replace('<', ' <').replace('>', '> ')
            sanitized = sanitized.replace('  ', ' ')
            tokens = sanitized.split(' ')
            data = utils.extractValue(tokens, '.give')
            user = utils.getUserFromMention(data['name'], self.data.mentionRegex)
            if data['value'] is None or user is None:
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
        if self.data.ledger is None or len(self.data.ledger) == 0:
            await message.channel.send("Looks like there's no connoisseurs, here... {}".format(rand.choice(self.data.sad)))
            return
        await message.channel.send(self.data.responses['list'].format(rand.choice(self.data.cute)))

        sortedLedger = sorted(self.data.ledger.items(), key=lambda item: item[1], reverse=True)
        sortedLedger = dict(sortedLedger)

        rows = [['Connoisseur', 'VGMCoins']]
        extra = ['To get some coins of your own, you can participate in [VGMC] activities! (or fish ^o^)']

        for key in sortedLedger:
            try:
                fetched = self.data.nameCache[key]
            except KeyError:
                user = await self.fetch_user(key)
                fetched = user.name
                self.data.nameCache[key] = fetched
            if sortedLedger[key] != 0:
                valstr = '{:,.2f}'.format(sortedLedger[key])
                rows.append([fetched, valstr])

        self.storeNameCache()
        # await message.channel.send(tempstr)
        await utils.sendBigMess(message, utils.tablegen(rows, header=True, width=16, extra=extra, lineWidth=55))

    async def fUwu(self, message):
        await message.channel.send(self.data.responses['uwu'].format(rand.choice(self.data.cute)))

    async def fTime(self, message):
        time = self.data.timePartRegex.search(message.content.lower())
        if time is not None:
            period = time.group(0)
            hour = utils.get_hour()
            if period == 'morning':
                if  hour is None or (hour>self.data.timeBound['morning'][0] and hour < self.data.timeBound['morning'][1]):
                    mess = self.data.responses['time'].format('morning', rand.choice(self.data.cute))
                    await message.channel.send(mess)
                else:
                    mess = self.data.responses['nottime'].format('morning', rand.choice(self.data.sad))
                    await message.channel.send(mess)
            elif period == 'night':
                if hour is None or (hour > self.data.timeBound['night'][0] or hour < self.data.timeBound['night'][1]):
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

    def roll(self, numChoices):
        return rand.randrange(1, numChoices + 1)

    def parseModifier(self, initmatch, string):
        if self.data.modifierRegex.search(string, pos=initmatch.end()) is None:
            return None

        end = initmatch.end()
        match = self.data.modifierRegex.search(string, pos=end)
        matches = []
        while match is not None:
            matches.append(match)
            end = match.end()
            match = self.data.modifierRegex.search(string, pos=end)
        return matches

    def extractModifier(self, matches):
        tot = []
        for match in matches:
            if match.group(1) == '+':
                tot.append(int(match.group(2)))
            else:
                tot.append(-int(match.group(2)))
        return sum(tot)

    def combineModifier(self, matches):
        return ''.join([x.group(0) for x in matches])


    def sign(self, num):
        if num < 0:
            return '-'
        else:
            return '+'

    async def fRoll(self, message):
        match = self.data.rollRegex.search(message.content)
        if match is not None:
            modifier = self.parseModifier(match, message.content)

            num1 = int(match.group(1))
            num2 = int(match.group(3))

            if num1 > 20:
                mess = f'sorry, the limit is 20 rolls at a time {rand.choice(self.data.sad)}'
                await message.channel.send(mess)
                return
            if len(match.group(3)) > 10:
                mess = f'sorry, the die can only go to 10 digits {rand.choice(self.data.sad)}'
                await message.channel.send(mess)
                return

            if num2 == 1:
                out = [1 for x in range(num1)]
            else:
                out = [self.roll(num2) for x in range(num1)]

            form = 'Roll {}: {}\n'
            string = ['[{}]\n'.format(match.group(0))] + [form.format(x + 1, y) for x, y in enumerate(out)]

            formatTotal = 'Total : {} '
            addit = 0
            if modifier is not None:
                addit = self.extractModifier(modifier)
                formatTotal += '({} {} {})'.format(sum(out), self.sign(addit), abs(addit))
                string[0] = string[0][:-2] + '{}]\n'.format(self.combineModifier(modifier))
            total = sum(out) + addit if sum(out) + addit > 1 else 1
            string.append(formatTotal.format(total))

            if num1 == 1:
                if num2 == 20:
                    if out[0] == 1:
                        string.append(f'\noof... {rand.choice(self.data.sad)}')
                    elif out[0] == 20:
                        string.append(f'\nwow natty!! {rand.choice(self.data.cute)}')
            await utils.sendBigMess(message, '```css\n' + ''.join(string) + '\n```')
            # await message.channel.send('```css\n' + ''.join(string) + '\n```')
        else:
            mess = f'sorry, looks like your roll isn\'t quite formatted right {rand.choice(self.data.sad)}'
            await message.channel.send(mess)
