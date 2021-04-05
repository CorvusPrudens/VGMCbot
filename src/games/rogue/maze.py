import utils
import numpy as np
import random
# this could be sped up by making a callable c module if necessary (seems like a lot of work, though)

def unflat(pos, width):
    return (pos % width, pos // width)

VISITED = 0b1

UP_N =    0b0001_0
DOWN_N =  0b0010_0
LEFT_N =  0b0100_0
RIGHT_N = 0b1000_0

UP_K =    0b0001_0000_0
DOWN_K =  0b0010_0000_0
LEFT_K =  0b0100_0000_0
RIGHT_K = 0b1000_0000_0

ROOM_KEY  = 0b0001_0000_0000_0
ROOM_ITEM = 0b0010_0000_0000_0

# the max distance would obviously be 255, but i dont
# expect we'll ever need that lol
DIST_MASK = 0b1111_1111_0000_0000_0000_0
DIST_SHIFT = 13

m2kd = {
    UP_N: 'up',
    DOWN_N: 'down',
    LEFT_N: 'left',
    RIGHT_N: 'right',
    UP_K: 'up_k',
    DOWN_K: 'down_k',
    LEFT_K: 'left_k',
    RIGHT_K: 'right_k',
}

m2ks = {
    ROOM_KEY: 'key',
    ROOM_ITEM: 'item',
}

def setDist(nprooms, pos, dist):
    nprooms[pos] |= (dist << DIST_SHIFT)

def getDist(roomint):
    return (roomint & DIST_MASK) >> DIST_SHIFT

def macro2key(roomint):
    doors = []
    for key in m2kd:
        if (roomint & key) > 0:
            doors.append(m2kd[key])
    return doors

def macro2sp(roomint):
    special = []
    for key in m2ks:
        if (roomint & key) > 0:
            special.append(m2ks[key])
    return special if len(special) > 0 else None


def setVisited(nprooms, pos, stackptr):
    nprooms[pos] |= VISITED
    setDist(nprooms, pos, stackptr)

def checkVisited(nprooms, pos):
    return (nprooms[pos] & VISITED) > 0

dirf = {
    'up': lambda pos : (pos[0] - 1, pos[1]),
    'down': lambda pos : (pos[0] + 1, pos[1]),
    'left': lambda pos : (pos[0], pos[1] - 1),
    'right': lambda pos : (pos[0], pos[1] + 1),
}


def valid(pos, w, h, nprooms, excluded, checkvis):
    check1 = pos[0] > -1 and pos[0] < h and pos[1] > -1 and pos[1] < w and pos not in excluded
    if check1:
        check2 = checkVisited(nprooms, pos) if checkvis else False
    else:
        check2 = False
    return check1 and not check2


def setDoors(ndrooms, key, pos1, pos2, special):
    if key == 'up':
        ndrooms[pos1] |= UP_N if special == 0 else UP_K
        ndrooms[pos2] |= DOWN_N if special == 0 else DOWN_K
    elif key == 'down':
        ndrooms[pos2] |= UP_N if special == 0 else UP_K
        ndrooms[pos1] |= DOWN_N if special == 0 else DOWN_K
    elif key == 'left':
        ndrooms[pos1] |= LEFT_N if special == 0 else LEFT_K
        ndrooms[pos2] |= RIGHT_N if special == 0 else RIGHT_K
    elif key == 'right':
        ndrooms[pos2] |= LEFT_N if special == 0 else LEFT_K
        ndrooms[pos1] |= RIGHT_N if special == 0 else RIGHT_K


def genOptions(pos, w, h, nprooms, excluded, checkvis=True):

    dird = {
        'up': 0,
        'down': 0,
        'left': 0,
        'right': 0,
    }

    keys = list(dird.keys())
    for key in keys:
        dird[key] = dirf[key](pos)
        if not valid(dird[key], w, h, nprooms, excluded, checkvis):
            del dird[key]

    return dird, len(dird)


class UnreachableError(Exception):
    pass

# excluded should be in the form of position tuples
# this could be varied so that only a certain
# number of the same steps can be taken
def depthSearch(w, h, start, excluded, max=None):
    stack = [(-1, -1) for x in range(w*h)]
    out = np.zeros((h, w), dtype='u4')
    stackptr = 0
    all_visited = w*h - len(excluded) if max is None else max - 1
    numVisited = 0
    numDead = 0

    furthest = 0
    furthestPos = start
    currentPos = start
    visitedCells = []

    while numVisited < all_visited + 1:

        if (stackptr > furthest):
            furthest = stackptr
            furthestPos = currentPos

        options, numopt = genOptions(currentPos, w, h, out, excluded)

        if numopt == 0:
            if not checkVisited(out, currentPos):
                setVisited(out, currentPos, stackptr)
                visitedCells.append(currentPos)
                numVisited += 1
                out[currentPos] |= ROOM_ITEM
                numDead += 1

            if stackptr > 0:
                stackptr -= 1
                currentPos = stack[stackptr]
            else:
                raise UnreachableError("unable to explore entire maze")
        else:
            setVisited(out, currentPos, stackptr)
            visitedCells.append(currentPos)
            numVisited += 1
            stack[stackptr] = currentPos
            stackptr += 1
            keylist = list(options.keys())
            newkey = random.choice(keylist)
            setDoors(out, newkey, currentPos, options[newkey], 0)
            currentPos = options[newkey]

    if not checkVisited(out, currentPos):
        setVisited(out, currentPos, stackptr)
        visitedCells.append(currentPos)
        numVisited += 1
        stackptr += 1
        out[currentPos] |= ROOM_ITEM
        numDead += 1
        if stackptr > furthest:
            furthestPos = currentPos
    out[furthestPos] |= ROOM_KEY
    return out, furthestPos, numDead, visitedCells
