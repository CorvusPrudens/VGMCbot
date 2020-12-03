import aiohttp
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
