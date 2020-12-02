import json
import asyncio
from matplotlib import pyplot
import numpy as np
import math
import random as rand
import sys
sys.path.append('../')
from data import *

fishCommands = """
✿ forage -- scrounge around for a rod and lure if you're desparate!
✿ shop -- Take a look at the rods and lures for sale!
✿ buy <item> -- Buy something from the shop (where item = number on the left)
✿ locations -- Take a look at the places you can fish!
✿ goto <location> -- Go to the given location for fishing!
✿ inv -- Show your fishy inventory!
✿ cast -- Cast with your selected rod and lure!
"""

fishCatalog = {}
with open('fish.json') as file:
    fishCatalog = json.load(file)

fishLocations = {}
with open('locations.json') as file:
    fishLocations = json.load(file)

def detectAn(string):
    anChars = ['a', 'e', 'i', 'o', 'u']
    if string.lower()[0] in anChars:
        return 'n'
    else:
        return ''

# TODO record code ought to execute here too
# TODO consider adding image urls to fish list
def fishLine(locations, fish, fishcatch, threshold=2):
    catch = 'You caught a{} {}! ({:.2f} cm) {}\n'

    small = 'That\'s a pretty small one though... {}\n'
    big = 'Wow! That\'s impressive for a{} {} {}\n'

    rare = 'You don\'t see those every day around here {}\n'

    output = catch.format(detectAn(fishcatch['catch']), fishcatch['catch'], fishcatch['size']/10, 'UwU')
    if fishcatch['size'] <= fish[fishcatch['catch']]['mu'] + fish[fishcatch['catch']]['sigma']*-threshold:
        output += small.format(':c')
    if fishcatch['size'] >= fish[fishcatch['catch']]['mu'] + fish[fishcatch['catch']]['sigma']*threshold:
        output += big.format(detectAn(fishcatch['catch']), fishcatch['catch'], 'UwU')

    # mu = locations[fishcatch['location']]['mu']
    # sigma = locations[fishcatch['location']]['sigma']
    # fishsize = fish[fishcatch['catch']]['mu']
    #
    # if fishsize >= mu + sigma*threshold:
    #     output += rare.format('UwU')

    return output


# bias represents the efficacy of the combination of rod and hook
# and is calculated in terms of the standard deviation

def retrieveFish(locations, fish, currentLocation, bias=0):
    mu = locations[currentLocation]['mu']
    sigma = locations[currentLocation]['sigma']
    mu += bias*sigma
    size = rand.gauss(mu, sigma)
    # if size > locations[currentLocation]['max']:
    #     size = locations[currentLocation]['max']
    if size < locations[currentLocation]['min']:
        size = locations[currentLocation]['min']

    # catch = locations[currentLocation]['fishlist'][]
    catch = ''
    for i in range(len(locations[currentLocation]['fishlist']) - 1, -1, -1):
        if size >= fish[locations[currentLocation]['fishlist'][i]]['mu']:
            catch = locations[currentLocation]['fishlist'][i]
        else:
            break

    size = rand.gauss(fish[catch]['mu'] + fish[catch]['sigma']*bias, fish[catch]['sigma'])
    size = round(size, 1)

    return {'catch': catch, 'size': size, 'location': currentLocation}



# while it may seem obtuse, I'm going to operate on everything
# more or less as a dictionary. That way, saving is much easier
# than working with objects!

# TODO you should be able to forage for a branch instead of using vgmcoins
# and it should take a few minutes to find
def newPole(name='branch', efficacy=-0.8, durability=5, damage=0):
    return {'name': name, 'efficacy': efficacy, 'durability': durability, 'damage': damage}

def newLure(name='broken can', efficacy=-0.8, durability=5, damage=0):
    return {'name': name, 'efficacy': efficacy, 'durability': durability, 'damage': damage}

def newRecord(name='trout', size='20', location='lagoon'):
    return {'name': name, 'size': size, 'location'=location}

# for each game, well have an init and a loop to be
# run inside the games class

fishLureShop = {
    # 'broken can': newLure()
    'hook': {'id': 0, 'price': 10, 'stats': newLure(name='hook', efficacy=-0.5, durability=10)},
    'popper': {'id': 1, 'price': 20, 'stats': newLure(name='popper', efficacy=-0.2, durability=20)},
    'spinner': {'id': 2, 'price': 40, 'stats': newLure(name='spinner', efficacy=0.1, durability=40)},
    'diver': {'id': 3, 'price': 100, 'stats': newLure(name='diver', efficacy=0.4, durability=80)}
}

fishRodShop = {
    'old pine rod': {'id': 4, 'price': 10, 'stats': newLure(name='old wooden rod', efficacy=-0.5, durability=10)},
    'bamboo rod': {'id': 5, 'price': 50, 'stats': newLure(name='popper', efficacy=-0.1, durability=20)},
    'aluminum rod': {'id': 6, 'price': 100, 'stats': newLure(name='aluminum rod', efficacy=0.3, durability=40)},
    'carbon fiber composite rod': {'id': 7, 'price': 200, 'stats': newLure(name='carbon fiber composite rod', efficacy=0.7, durability=80)}
}

async def initFishing(message, client):
    try:
        client.games.players[message.author.id]['games'].append('fishing')
    except KeyError:
        client.games.players[message.author.id] = {'games': ['fishing']}
    templateDict = {
        'state': {'location': 'lagoon', 'state': 'idle', 'timeCast': -1},
        'poles': [newPole()],
        'lures': [newLure()],
        'records': {},
    }
    client.games.players[message.author.id]['fishing'] = templateDict

    fetched = await client.fetch_user(message.author.id)
    string1 = 'Hello {}, Welcome to the VGMSea! {}\n'.format(fetched, rand.choice(cute))
    string2 = 'Pick up a rod, get yourself a hook, and set out to catch some record breaking fish!\n'
    string3 = 'If you need help with the commands, just mention me and say help'

    await message.channel.send(string1 + string2 + string3)


def fCast(players, currentPlayer):
    try:
        players[currentPlayer]['fishing']['state']['state'] = 'cast'
    except KeyError:
        initFishing(players, currentPlayer)
        players[currentPlayer]['fishing']['state']['state'] = 'cast'


async def fShop(message, client):
    string = 'Hey {}, here\'s what we\'ve got! {}\n'.format(message.author.mention, rand.choice(cute))
    t = 0
    for key in fishLureShop:
        tempstr = '{}.) {} -- durability: {} -- efficacy: {} -- price: {}\n'
        string += tempstr.format(fishLureShop[key]['id'], key,
                                fishLureShop[key]['stats']['durability'],
                                fishLureShop[key]['stats']['efficacy'],
                                fishLureShop[key]['price'])
    for key in fishRodShop:
        tempstr = '{}.) {} -- durability: {} -- efficacy: {} -- price: {}\n'
        string += tempstr.format(fishRodShop[key]['id'], key,
                                fishRodShop[key]['stats']['durability'],
                                fishRodShop[key]['stats']['efficacy'],
                                fishRodShop[key]['price'])

    string += 'If you\'d like to buy something, mention me and say buy <left number>'
    await message.channel.send(string)

async def fGoto(message, client):
    sanitized = message.content.replace('<', ' <').replace('>', '> ')
    sanitized = sanitized.replace('  ', ' ')
    tokens = sanitized.split(' ')

    for i in range(len(tokens)):
        targ = ''
        if tokens[i] == 'goto' and i < len(tokens) - 1:
            targ = tokens[i + 1]
        if targ == '':
            targ = '<nowhere>'
        if targ not in list(fishLocations.keys()):
            mess = 'I\'m sorry, I\'m not sure how to take you to {} {}\n'.format(targ, choice(sad))
            mess += 'If you\'re not sure where I can take you, just mention me and say locations!'
            await message.channel.send(mess)
        else:
            mess = 'Ok! Off we go to the {}! {}\n'.format(targ, choice(cute))
            await message.channel.send(mess)
            try:
                client.games.players[message.author.id]['fishing']['state']['location'] = targ
            except KeyError:
                await initFishing(message, client)
                client.games.players[message.author.id]['fishing']['state']['location'] = targ

fishingFuncs = {
    'goto': fGoto,
    'shop': fShop,
}

if __name__ == '__main__':
    catch = retrieveFish(fishLocations, fishCatalog, 'boat', bias=0)
    print(fishLine(fishLocations, fishCatalog, catch))
