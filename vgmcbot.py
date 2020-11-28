import discord
from random import choice
from re import compile
from time import sleep
from sys import argv

if len(argv) != 2:
    print('Please provide the bot token as a command line argument!')
    exit(1)

client = discord.Client()
botID = '782113493797044224'
cachePath = 'bank.csv'

imgur = 'https://i.imgur.com/'
end = '.jpg'
honks = [
    '9LXSJdC',
    'BzYrnYp',
    'kq3B5UK',
    'z44rteZ',
    'Ewh9N3k'
]

commandsHeader = "When you mention me, I'll do a command for you! {}"

leaderCommands = """
✿ give @<username> <value> coins -- this will give <username> the <value> of coins!
"""

peasantCommands = """
✿ help -- I'll list out all these commands for you!
✿ hmc -- "How Many Coins;" this'll tell you how many you've got!
"""

leader = 'CAW CAW CAW'

bank = {}

responses = {
    'give': "Ok! {} now has {:,.2f} VGMCoins {}",
    'giveErr': """I'm sorry {}, I didn't quite catch that.
The \"give\" syntax is \"give @<username> <number> coins\" {}""",
    'permission': "sorry {}, you don't have permission to give coins {}",
    'hmc': 'hey {}, looks like you have {} VGMCoins {}'
}

cute = [
    '(✿◠‿◠)',
    '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧',
    '(▰˘◡˘▰)',
    '(づ｡◕‿‿◕｡)づ',
    'v(=∩_∩=)ﾌ',
    '(~￣▽￣)~',
    'ヾ(〃^∇^)ﾉ',
    'Ｏ(≧▽≦)Ｏ',
    'UwU'
]

sad = [
    'ಥ_ಥ',
    '(◕︵◕)',
    'o(╥﹏╥)o',
    '(⊙﹏⊙✿)',
    '◄.►',
    '┐(‘～`；)┌',
    '(∩︵∩)',
    '●︿●',
    'ਉ_ਉ'
]

honkRegex = compile('\\b(honk)s*\\b')
mentionRegex = compile('((?<=(<@)[!&])|(?<=<@))[0-9]+(?=>)')
name = ''

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
    tempstr = commandsHeader.format(choice(cute))
    if hasPermission(message.author, leader):
        tempstr += leaderCommands
    return tempstr + peasantCommands

def loadBank(dict, path):
    try:
        with open(path, 'r') as file:
            for line in file:
                tokens = line.split(',')
                dict[int(tokens[0])] = float(tokens[1])
    except FileNotFoundError:
        pass

def storeBank(dict, path):
    with open(path, 'w') as file:
        for key in dict:
            file.write(f'{key},{dict[key]}\n')


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    loadBank(bank, cachePath)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    sleep(1)

    if honkRegex.search(message.content) != None:
        url = imgur + choice(honks) + end
        await message.channel.send(url)

    # Proper parsing would be best here, but this
    # will work for now
    if client.user.mentioned_in(message):
        responded = False
        tokens = message.content.split(' ')
        name = '{0.user}'.format(client)[:-5]
        # server = message.guild
        if 'give' in tokens:
            if hasPermission(message.author, leader):
                data = extractValue(tokens, 'give')
                user = getUserFromMention(data['name'])
                if data['value'] == None or user == None:
                    await message.channel.send(responses['giveErr'].format(message.author.mention, choice(sad)))
                else:
                    try:
                        bank[user] += data['value']
                    except KeyError:
                        bank[user] = data['value']
                    storeBank(bank, cachePath)
                    mess = responses['give'].format(data['name'], bank[user], choice(cute))
                    if bank[user] == 1:
                        mess = mess.replace('VGMCoins', 'VGMCoin')
                    await message.channel.send(mess)
            else:
                await message.channel.send(responses['permission'].format(message.author.mention, choice(sad)))
            responded = True
        elif 'help' in tokens:
            await message.channel.send(helpMessage(message))
            responded = True
        elif 'hmc' in tokens:
            try:
                value = bank[message.author.id]
            except KeyError:
                value = 0
            mess = responses['hmc'].format(message.author.mention, value, choice(cute))
            if value == 1:
                mess = mess.replace('VGMCoins', 'VGMCoin')
            await message.channel.send(mess)
            responded = True

        if not responded:
            await message.channel.send('what\'s up gamer {}'.format(choice(cute)))

# To make this secure, we can just make this a cli argument
client.run(argv[1])
