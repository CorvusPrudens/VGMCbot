import aiohttp
import math
from copy import deepcopy
from data import *


class LineWidthError(Exception):
    pass

class ExtraIndexError(Exception):
    pass

class GameTemplate:
    def __init__(self, client):
        self.loopCommands = {}
        self.reactCommands = {}
        self.reactMessages = {}
        self.commands = {}
        self.helpDict = {}
        self.client = client

    async def gameLoop(self, players):
        keylist = list(players.keys())
        for key in keylist:
            await self.execute(key, players)

    async def reactLoop(self, reaction, user, add):
        id = reaction.message.id
        if id in self.reactMessages and self.reactMessages[id]['user'] == user.id:
            target = self.reactMessages[id]['target']
            target = reaction.message if target is None else target
            await self.reactCommands[self.reactMessages[id]['comm']](reaction, user, add, id)

    def newReactMessage(self, command, user, source, target=None):
        self.reactMessages[source.id] = {'comm': command, 'user': user, 'target': target, 'source': source}

    async def removeReactMessage(self, source):
        # delete all messages associated with interaction
        if self.reactMessages[source]['target'] is not None:
            await self.reactMessages[source]['target'].delete()
        await self.reactMessages[source]['source'].delete()
        del self.reactMessages[source]

    async def execute(self, playerKey, players):
        pass

    def decorators(self, slash, guild_ids):
        pass

################################################################################
########################## general functions ###################################
################################################################################

def remap(x, min1, max1, min2, max2):
    range1 = max1 - min1
    prop = (x - min1) / range1

    range2 = max2 - min2

    return range2*prop + min2


def expBias(x, bias, steep=1):
    # k = (1 - bias)**3
    k = bias
    return (x*k) / (x*k*steep - x + 1)

def clamp(x, minval, maxval):
    return min(max(x, minval), maxval)


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

def manageStyling(strings, styling):
    active = False
    stylingStart = f'```{styling}\n'
    stylingEnd = '```'
    regex_search = {
        'styleStart': re.compile(f'``` *{styling}' + r'\b'),
        'styleEnd': re.compile(f'```(?! *{styling}' + r'\b)'),
    }
    pos = 0
    for idx, string in enumerate(strings):
        if active:
            strings[idx] = stylingStart + string
        for key in regex_search:
            match = regex_search[key].search(string, pos=pos)
            while match is not None:
                if key == 'styleStart':
                    active = True
                elif key == 'styleEnd':
                    active = False
                pos = match.end()
                match = regex_search[key].search(string, pos=pos)
        if active:
            strings[idx] += stylingEnd


def breakMessage(string, maxlen=1399, minlen=500, buffer=100, styling='css'):
    # Message-break points in descending ideality

    if not isinstance(string, str):
        raise TypeError("string input must be a string")

    if maxlen < 500:
        raise ValueError("maxlen cannot be less than 500 characters")
    if buffer < 50:
        raise ValueError("character buffer must be greater than 50 characters")
    if 100 > minlen > maxlen:
        raise ValueError("minlen must be greater than 100 and less than maxlen")

    if not isinstance(styling, str):
        raise TypeError("styling kwarg must be a string")

    if len(string) == 0:
        return []

    # need a variable to track how long extra codeblock characters can be
    maxStyling = len(f'```{styling}```')

    regex_search = [
        re.compile(r'\n'),
        re.compile(r'([A-Za-z_][A-Za-z_.0-9]*)(\.)( {1,}|$|\n)'), # sentence end
        re.compile(r' ')
    ]

    combinedBuffer = (maxlen - (buffer + maxStyling))
    numMess = math.ceil(len(string) / combinedBuffer)
    idealLen = round(len(string) / numMess)

    outstrings = []
    prevError = 0

    while len(string) > maxlen - maxStyling:
        for search in regex_search:
            found = False
            endIndex = min(idealLen - prevError, maxlen - maxStyling)
            for i in range(endIndex - 10, minlen, -1):
                match = search.search(string, pos=i, endpos=endIndex)
                if match is not None:
                    outstrings.append(string[:match.end()])
                    string = string[match.end():]
                    prevError = i - idealLen
                    found = True
                    break
            # not sure if there's a better way to manage this
            if found:
                break
        if not found:
            # fallback message break
            outstrings.append(string[:idealLen] + '-')
            string = string[idealLen:]
            prevError = 0

    if len(string) > 0:
        outstrings.append(string)

    manageStyling(outstrings, styling)

    return outstrings

# ~~this is truly horrible~~
# fixed! now it's lovely <3
async def sendBigMess(message, string):
    for fragment in breakMessage(string):
        await message.channel.send(fragment)

def rowGen(colWidth, dot, row=None, sep='='):
    # optional feature, may remove later
    if row and re.search('^[=\-*~#]$', row[0]) is not None:
        sep = row[0]
        row = None

    if row:
        rf = ' {} {}|'
        string = [rf.format(x, (y - len(x))*' ') for x, y in zip(row, colWidth)]
    else:
        rf = '{}+'
        string = [rf.format(sep*(x + 2)) for x in colWidth]
        string[0] = string[0][:len(dot) - 1] + ' ' + string[0][len(dot):]
        string[-1] = string[-1][:-2] + '  '
    string[-1] = string[-1][:-1] + ';\n'
    return dot + ''.join(string)

def splitStrings(strings, maxlen):
    breaks = ('\n', ' ')
    outstrings = []
    for string in strings:
        if len(string.replace('\n', '')) <= maxlen:
            outstrings.append(string)
        else:
            tempstr = deepcopy(string)
            while len(tempstr) > maxlen:
                found = False
                for br in breaks:
                    if found:
                        break
                    for i in range(maxlen, -1, -1):
                        if tempstr[i] == br:
                            outstrings.append(tempstr[:i])
                            tempstr = tempstr[i + 1:]
                            found = True
                            break
                if not found:
                    outstrings.append(tempstr[:maxlen - 1] + '-')
                    tempstr = tempstr[maxlen - 1:]
            if len(tempstr) > 0:
                outstrings.append(tempstr)
    return outstrings

# cell format
def cf(cell, width):
    regex_special = re.compile(r'\[.*\]')
    ell = '..]' if regex_special.search(cell) is not None else '...'
    return cell if len(cell) <= width else cell[:width - 3] + ell

def tablegen(data, header=False, dot='✿', numbered=False, extra=None, name='', width=32, lineWidth=60):
    # all tables are formatted with css highlighting
    # empty cells are not counted if the input is numbered

    if len(data) == 0:
        return ''

    if header:
        data = data[:1] + [['=']] + data[1:]

    if numbered:
        fmt = '{}.{} {}'
        spc = math.floor(math.log(len(data), 10)) + 1
        num = 1
        offset = 2 if header else 0
        for idx, item in enumerate(data[offset:]):
            if item[0] != '' and re.search('^[=\-*~#]$', item[0]) is None:
                nstr = str(num)
                data[idx + offset][0] = fmt.format(nstr, ' '*(spc - len(nstr)), item[0])
                num += 1

    rowlen = len(max(data, key=len))
    for row in data:
        if len(row) < rowlen:
            row += ['' for x in range(rowlen - len(row))]

    colWidth = []
    for col in range(rowlen):
        tw = len(max([x[col] for x in data], key=len))
        tw = tw if tw < width else width # max width
        tw = tw if tw > 4 else 4 # min width
        colWidth.append(tw)

    # shortening long entries
    for idx, row in enumerate(data):
        # data[idx] = [x if len(x) <= width else x[:width - 3] + '...' for x in row]
        data[idx] = [cf(x, width) for x in row]

    string = [rowGen(colWidth, dot, row=x) for x in data + ['=']]

    if extra is not None:
        genWidth = len(string[0])
        if (genWidth >= lineWidth - 5):
            raise LineWidthError("Table width of {} exceeds {} characters.".format(genWidth, lineWidth))
        broken = splitStrings(extra, (lineWidth - genWidth) - 1)
        offset = 1 if header else 0
        try:
            for idx, line in enumerate(broken):
                string[idx + offset] = string[idx + offset][:-1] + ' ' + line + '\n'
        except IndexError:
            raise ExtraIndexError("Extra strings too long for given table.")

    return '```css\n' + ''.join(string) + '```'



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
