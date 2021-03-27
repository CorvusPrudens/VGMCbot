import os
from matplotlib import pyplot
# import time
import math
import numpy as np
import random as rand
import json

fish = {}

def avg(arr):
    acc = 0.0
    for item in arr:
        acc += item
    if acc == 0:
        return 0
    else:
        return acc/len(arr)

def stdd(arr):
    acc = 0
    mu = avg(arr)
    for item in arr:
        acc += (item - mu)**2
    return math.sqrt((1.0/len(arr))*acc)

def getCodeName(line):
    style = line.strip(' \n')
    return style.replace(' ', '').replace('```', '')

# this is truly horrible
async def sendBigMess(message, string):
    print(len(string))
    if len(string) < 1400:
        await message.channel.send(string)
    else:
        fragments = []
        totalLen = len(string)
        numMess = math.ceil(totalLen / 1350.0)
        idealLen = int(totalLen / numMess)
        minSize = int((totalLen / numMess)*0.25)
        rest = string
        regex_sentence = re.compile(r'([A-Za-z_][A-Za-z_.0-9]*)(\.)( {1,}|$|\n)')
        styling = {'```': []}

        while len(rest) > 0:
            if len(rest) <= idealLen:
                fragments.append(rest)
                break
            currentIndex = idealLen
            # the actual number of messages may deviate from numMess
            # if we are not able to match the ideal length, so don't
            # depend on numMess
            for style in styling:
                if len(styling[style]) > 0:
                    for codeName in styling[style]:
                        rest = style + codeName + '\n' + rest

            while rest[currentIndex] != '\n' and currentIndex > -1:
                currentIndex -= 1
            if currentIndex  < minSize:
                currentIndex = idealLen
                # try to find the end of a sentence
                matches = regex_sentence.findall(rest, endpos=currentIndex)
                for i in range(len(matches) - 1, -1, -1):
                    if len(matches[i]) == 0:
                        matches.remove(i)

                if len(matches) > 0:
                    currentIndex = rest[:currentIndex].rfind(matches[-1][0]) + len(''.join(matches[-1])) - 1
                else:
                    # last-ditch separation
                    currentIndex = idealLen
                rest = rest[:currentIndex] + '\n' + rest[currentIndex:]
                currentIndex += 1

            for style in styling:
                regex_style = re.compile(style)
                matches = regex_style.findall(rest, endpos=currentIndex)
                styleIndex = 0
                for match in matches:
                    styleIndex = rest[styleIndex:currentIndex].find(match) + len(match)
                    rightIndex =  rest[styleIndex:currentIndex].find('\n')
                    if rightIndex == -1:
                        rightIndex = currentIndex - styleIndex
                    codeName =  getCodeName(rest[styleIndex:styleIndex + rightIndex])
                    if codeName != '':
                        if codeName not in styling[style]:
                            styling[style].append(codeName)
                    else:
                        styling[style] = styling[style][:-1]


            for style in styling:
                if len(styling[style]) > 0:
                    for codeName in styling[style]:
                        rest = rest[:currentIndex] + style + rest[currentIndex:]
                        currentIndex += len(style)

            fragments.append(rest[:currentIndex])

            rest = rest[currentIndex + 1:]

        for fragment in fragments:
            if fragment.replace(' ', '').replace('\n', '') != '':
                await message.channel.send(fragment)

# def pretty(string):
#     string = string.lower()
#     gap = ord('a') - ord('A')
#     string = chr(ord(string[0]) - gap) + string[1:]
#     for i in range(len(string)):
#         if string[i] == ' ' and i < len(string) - 1:
#             old = ord(string[i + 1])
#             string = string[:i + 1] + chr(old - gap) + string[i + 2:]
#     return string
#
#
# files = os.listdir('fish_data')
# for name in files:
#     if 'size' in name:
#         with open('fish_data/' + name) as file:
#             for line in file:
#                 tokens = line.split(',')
#                 try:
#                     num = tokens[10]
#                     if tokens[10].isnumeric():
#                         fish[tokens[16]].append(float(tokens[10]))
#                     else:
#                         fish[tokens[16]].append(0)
#                 except KeyError:
#                     if tokens[10].isnumeric():
#                         fish[tokens[16]] = [float(tokens[10])]
#                     else:
#                         fish[tokens[16]] = [0]
#
#
# for key in fish:
#     for i in range(len(fish[key]) - 1, -1, -1):
#         if fish[key][i] == 0:
#             fish[key].pop(i)
#
# del fish['common']
# del fish['']
# del fish['KINGFISH GENUS']
# del fish['GRUNT FAMILY']
# # del fish['DOLPHIN']
#
# fish = dict(sorted(fish.items(), key=lambda item: len(item[1]), reverse=True))
#
# limit = 100
# limitCount = 0
# total = fish.keys()
# goners = []
# for key in total:
#     if limitCount >= limit:
#         goners.append(key)
#     limitCount += 1
#
# [fish.pop(key) for key in goners]
#
# fish = dict(sorted(fish.items(), key=lambda item: avg(item[1]), reverse=True))
#
# for key in fish:
#     string = '{:25}, {}, {:,.2f}, {:.2f}'.format(key, len(fish[key]), avg(fish[key]), stdd(fish[key]))
#     print(string)
#
# key = list(fish.keys())[1]
#
# fig, ax = pyplot.subplots()
# n, bins, patches = ax.hist(fish[key], bins='auto', density=True)
#
# mu = avg(fish[key])
# sigma = stdd(fish[key])
# y = ((1/(np.sqrt(2*np.pi)*sigma)) * np.exp(-0.5*(1/sigma*(bins-mu))**2))
#
# stdlist = []
# for i in range(10):
#     stdlist.append(rand.gauss(mu, sigma))
# print(stdlist)
#
# finalDict = {}
#
# for key in fish:
#     newKey = pretty(key)
#     finalDict[newKey] = {'mu': avg(fish[key]), 'sigma': stdd(fish[key]), 'pop': len(fish[key])}
#
# with open('fish.json', "w") as outfile:
#     json.dump(finalDict, outfile)
#
# # ax.plot(bins, y, '--')
# # ax.xaxis.set_major_locator(pyplot.MaxNLocator(15))
# # pyplot.show()

if __name__ == '__main__':
    fish = {}
    with open('fish.json') as file:
        fish = json.load(file)

    locations = {
        'boat': {'mu': 0, 'sigma': 0, 'max': 0, 'min': 0, 'fishlist': []},
        'cliffside': {'mu': 0, 'sigma': 0, 'max': 0, 'min': 0, 'fishlist': []},
        'lagoon': {'mu': 0, 'sigma': 0, 'max': 0, 'min': 0, 'fishlist': []},
    }

    ranges = [0, 50, 25, 75, 50, 100]
    pair = 0

    for key in locations:
        sizes = []
        fishkeys = list(fish.keys())[ranges[pair*2]:ranges[pair*2 + 1]]
        pair += 1
        for fk in fishkeys:
            sizes.append(fish[fk]['mu'])
        locations[key]['mu'] = avg(sizes)
        locations[key]['sigma'] = stdd(sizes)
        locations[key]['max'] = fish[fishkeys[0]]['mu']
        locations[key]['min'] = fish[fishkeys[-1]]['mu']
        locations[key]['fishlist'] = fishkeys

    with open('locations.json', 'w') as outfile:
        json.dump(locations, outfile)
