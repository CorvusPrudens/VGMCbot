import aiohttp
import math
from data import *


################################################################################
########################## general functions ###################################
################################################################################

def getUserFromMention(mention, regex):
    try:
        return int(regex.search(mention).group(0))
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



# def loadBank(dict, path):
#     try:
#         with open(path, 'r') as file:
#             for line in file:
#                 tokens = line.replace('\n', '').split(',')
#                 if len(line.replace('\n', '')) > 0:
#                     dict[int(tokens[0])] = float(tokens[1])
#     except FileNotFoundError:
#         pass
#
# def storeBank(dict, path):
#     with open(path, 'w') as file:
#         for key in dict:
#             file.write(f'{key},{dict[key]}\n')

def loadj(dict, path):
    with open(path, 'r') as file:
        dict = json.load(path)

def storej(dict, path):
    with open(path, 'w') as file:
        json.dump(dict, path)

def getReactionName(reactStr, regex):
    match = regex.search(reactStr)
    if match != None:
        return match.group(0)
    else:
        return None

def sanitizedTokens(string):
    sanitized = string.replace('<', ' <').replace('>', '> ')
    sanitized = sanitized.replace('  ', ' ')
    return sanitized.split(' ')
