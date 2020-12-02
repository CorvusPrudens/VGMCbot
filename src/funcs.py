import random as rand
import re
import aiohttp
from data import *

################################################################################
########################## general functions ###################################
################################################################################

async def getHour():
    response = {'datetime': ''}
    async with aiohttp.ClientSession() as session:
        async with session.get(timeUrl) as r:
            if r.status == 200:
                response = await r.json()
    hour = timeRegex.search(response['datetime'])
    if hour == None:
        return None
    else:
        return int(hour.group(0))

def getUserFromMention(mention):
    try:
        return int(mentionRegex.search(mention).group(0))
    except AttributeError:
        return None

def extractValue(tokens, keyword):
    for i in range(len(tokens)):
        if keyword in tokens[i]:
            if i >= len(tokens) - 2:
                return None
            try:
                value = float(tokens[i + 2])
                return {'value': value, 'name': tokens[i + 1]}
            except ValueError:
                return None
    return None

def hasPermission(user, role):
    for ro in user.roles:
        if ro.name == role:
            return True
    return False

def helpMessage(message):
    tempstr = commandsHeader.format(rand.choice(cute))
    if hasPermission(message.author, leader):
        tempstr += leaderCommands
    return tempstr + peasantCommands

def loadBank(dict, path):
    try:
        with open(path, 'r') as file:
            for line in file:
                tokens = line.replace('\n', '').split(',')
                if len(line.replace('\n', '')) > 0:
                    dict[int(tokens[0])] = float(tokens[1])
    except FileNotFoundError:
        pass

def storeBank(dict, path):
    with open(path, 'w') as file:
        for key in dict:
            file.write(f'{key},{dict[key]}\n')

def getReactionName(reactStr):
    match = reactRegex.search(reactStr)
    if match != None:
        return match.group(0)
    else:
        return None

################################################################################
########################## on_reaction functions ###############################
################################################################################

async def reactionAdd(reaction, user):
    name = getReactionName(str(reaction))

    if name != None and name == 'VGMCoin':
        try:
            giver = bank[user.id]
        except KeyError:
            bank[user.id] = 0
        try:
            receiver = bank[reaction.message.author.id]
        except KeyError:
            bank[reaction.message.author.id] = 0

        if bank[user.id] >= 1:
            bank[user.id] -= 1
            bank[reaction.message.author.id] += 1
            storeBank(bank, cachePath)
        else:
            await reaction.message.remove_reaction(reaction.emoji, user)

async def reactionRemove(reaction, user):
    name = getReactionName(str(reaction))

    if name != None and name == 'VGMCoin':
        try:
            taker = bank[user.id]
        except KeyError:
            bank[user.id] = 0
        try:
            victim = bank[reaction.message.author.id]
        except KeyError:
            bank[reaction.message.author.id] = 0

        # This is a bit troll since people can be put into debt if someone
        # removes a coin while the debtor has less than one coin
        bank[reaction.message.author.id] -= 1
        bank[user.id] += 1
        storeBank(bank, cachePath)

################################################################################
########################## on_message functions ################################
################################################################################

async def preMention(message):
    # this global crap is messy and needs to be cleaned up
    global prevChoice
    if honkRegex.search(message.content.lower()) != None:
        currentChoice = rand.randrange(5)
        while currentChoice == prevChoice:
            currentChoice = rand.randrange(5)
        prevChoice = currentChoice
        url = imgur + honks[currentChoice] + end
        await message.channel.send(url)
    elif hankRegex.search(message.content.lower()) != None:
        await message.channel.send(hankUrl1 + hankUrl2 + hankUrl3)

async def fGive(message):
    if hasPermission(message.author, leader):
        # bit ugly but...
        sanitized = message.content.replace('<', ' <').replace('>', '> ')
        sanitized = sanitized.replace('  ', ' ')
        tokens = sanitized.split(' ')
        data = extractValue(tokens, 'give')
        user = getUserFromMention(data['name'])
        if data['value'] == None or user == None:
            mess = responses['giveErr'].format(message.author.mention, rand.choice(sad))
            await message.channel.send(mess)
        else:
            try:
                bank[user] += data['value']
            except KeyError:
                bank[user] = data['value']
            storeBank(bank, cachePath)
            mess = responses['give'].format(data['name'], bank[user], rand.choice(cute))
            if bank[user] == 1:
                mess = mess.replace('VGMCoins', 'VGMCoin')
            await message.channel.send(mess)
    else:
        mess = responses['permission'].format(message.author.mention, rand.choice(sad))
        await message.channel.send(mess)

async def fHelp(message):
    await message.channel.send(helpMessage(message))

async def fHmc(message):
    try:
        value = bank[message.author.id]
    except KeyError:
        value = 0
    mess = responses['hmc'].format(message.author.mention, value, rand.choice(cute))
    if value == 1:
        mess = mess.replace('VGMCoins', 'VGMCoin')
    await message.channel.send(mess)

async def fList(message):
    await message.channel.send(responses['list'].format(rand.choice(cute)))
    tempstr = ''
    templist = []
    longest = 0
    sortedBank = sorted(bank.items(), key=lambda item: item[1], reverse=True)
    sortedBank = dict(sortedBank)
    # can't really use longest yet, but maybe we'll find a use eventually
    for key in sortedBank:
        fetched = await client.fetch_user(key)
        templist.append([fetched.name, sortedBank[key]])
        if len(fetched.name) > longest:
            longest = len(fetched.name)
    for pair in templist:
        if pair[1] != 0:
            tempstr += responses['listItem'].format(pair[0], pair[1])
    await message.channel.send(tempstr)

async def fUwu(message):
    await message.channel.send(responses['uwu'].format(rand.choice(cute)))

async def fTime(message):
    time = timePartRegex.search(message.content.lower())
    if time != None:
        period = time.group(0)
        hour = await getHour()
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

async def fCount(message):
    await message.channel.send(str(client.counter))

# this dictionary allows us to cleanly call the defined
# functions without explicitly checking for the
# commands in an if elif etc block

# while it is technically 'data,' I chose to include it
# here for clarity and to make sure the functions are
# properly defined before passing them to the dict

funcDict = {
    'give': fGive,
    'help': fHelp,
    'hmc': fHmc,
    'list': fList,
    'uwu': fUwu,
    'morning': fTime,
    'night': fTime,
    'count': fCount
}

# here we construct the regex string so it's not a pain in the ass to update
commRegexString = '\\b'
for key in funcDict:
    commRegexString += '({})|'.format(key)
commRegex = re.compile(commRegexString[:-1] + '\\b')
