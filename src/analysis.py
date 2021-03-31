import utils
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import numpy as np
from games.fishing import fishing

# TODO -- each location needs a custom curve so that the
# fishing gear can serve a niche for each area

# catch analysis, to be run from src folder
def scale(val, min1, max1, min2, max2):
    range1 = max1 - min1
    prop = (val - min1) / range1

    range2 = max2 - min2

    return range2*prop + min2

def an(location, bias):
    catch, valid = fish.retrieveFish(location, bias=bias)
    return catch['size']/10 if valid else 0

def genTimeSize(efficacy, numSteps=100):

    # time generator
    tg = lambda z : [[fish.calcCastTime(y, z) for x in range(numSteps)] for y in fish.locations]
    averageTimes = [[sum(x) / len(x) for x in tg(y)] for y in efficacy]

    # size generator
    sg = lambda z : [[an(y, z) for x in range(numSteps)] for y in fish.locations]
    averageSizes = [[sum(x) / len(x) for x in sg(y)] for y in efficacy]

    return averageTimes, averageSizes

def genData(averageTimes, averageSizes, exp=1.2):

    cph = lambda t, s : ((60**2) / t) * ((fish.calcDamage(s*10)**exp) - fish.calcDamage(s*10))
    coins = []
    for time, size in zip(averageTimes, averageSizes):
        coins.append([cph(x, y) for x, y in zip(time, size)])

    timeplt = [[x[y] for x in averageTimes] for y, _ in enumerate(averageTimes[0])]
    sizeplt = [[x[y] for x in averageSizes] for y, _ in enumerate(averageSizes[0])]
    coinplt = [[x[y] for x in coins] for y, _ in enumerate(coins[0])]

    return timeplt, sizeplt, coinplt

def genPrice(numSteps):
    prices = [0] + [fish.lureShop[x]['price'] + fish.rodShop[y]['price'] for x, y in zip(fish.lureShop, fish.rodShop)]
    durabilities = [fish.newLure()['durability'] + fish.newRod()['durability']]
    durabilities += [fish.lureShop[x]['stats']['durability'] + fish.rodShop[y]['stats']['durability'] for x, y in zip(fish.lureShop, fish.rodShop)]
    priceContour = []
    durabilityContour = []
    priceSteps = int(numSteps / (len(prices) - 1))
    durabilitySteps = int(numSteps / (len(durabilities) - 1))
    # for idx, price in enumerate(prices, 1):
    #     priceContour += [scale(x, 0, priceSteps, prices[idx - 1], price) for x in range(priceSteps)]
    for i in range(1, len(prices)):
        priceContour += [scale(x, 0, priceSteps, prices[i - 1], prices[i]) for x in range(priceSteps)]

    for i in range(1, len(durabilities)):
        durabilityContour += [scale(x, 0, durabilitySteps, durabilities[i - 1], durabilities[i]) for x in range(durabilitySteps)]

    while len(priceContour) < numSteps:
        priceContour.append(priceContour[-1])

    while len(durabilityContour) < numSteps:
        durabilityContour.append(durabilityContour[-1])

    print(len(durabilityContour))
    return priceContour, durabilityContour

def genLike(linEff):
    return [fish.catchChance(x) for x in linEff]


def updateCoins(times, sizes, costs, likely, exp=1.2):
    cph = lambda t, s, c, l : (((60**2) / t) * l) * (((fish.calcDamage(s*10)*exp)**1) - (fish.calcDamage(s*10) * c))
    coins = []
    for time, size, cost, like in zip(times, sizes, costs, likely):
        coins.append([cph(x, y, cost, like) for x, y in zip(time, size)])
    return [[x[y] for x in coins] for y, _ in enumerate(coins[0])]

# okay so here we're shortening way too much with comprehensions and lambdas
if __name__ == '__main__':
    # worst gear catch rate, roi in all locations
    # best gear catch rate, roi in all locations
    # foraging roi in forage locations

    fish = fishing.GameFishing()
    header = [x for x in fish.locations]

    worstEff = fish.minEff
    bestEff = fish.maxEff
    numSteps = 25
    linEff = [scale(x, 0, numSteps, worstEff, bestEff) for x in range(numSteps)]

    exp = 1.35
    priceContour, durabilityContour = genPrice(numSteps)
    avgTime, avgSize = genTimeSize(linEff, numSteps=5000)
    timeplt, sizeplt, coinplt = genData(avgTime, avgSize, exp=exp)
    likely = genLike(linEff)

    colors = ['red', 'green', 'blue', 'yellow']
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, constrained_layout=False, sharex=True, figsize=(8, 8))

    for column, color, name in zip(timeplt, colors, header):
        ax1.plot(linEff, column, color=color, label=name)

    ax1.set_title('Cast times')
    ax1.set_ylabel('time (s)')

    for column, color in zip(sizeplt, colors):
        ax2.plot(linEff, column, color=color)

    ax2.set_title('Fish Size')
    ax2.set_ylabel('Size (cm)')

    cpd = [x / y for x, y in zip(priceContour, durabilityContour)]
    ax3.plot(linEff, cpd, color='red')
    ax3.set_title('Cost')
    ax3.set_ylabel('Coins per durability')

    coinplt = updateCoins(avgTime, avgSize, cpd, likely, exp=exp)

    for column, color in zip(coinplt, colors):
        ax4.plot(linEff, column, color=color)

    ax4.set_title('Profit')
    ax4.set_xlabel('efficacy')
    ax4.set_ylabel('Coins per Hour')

    fig.legend()
    fig.suptitle('Fishing Analysis', fontsize=16)

    # Make a horizontal slider to control the frequency.
    axfreq = plt.axes([0.25, 0.00, 0.65, 0.03], facecolor='blue')
    slider = Slider(
        ax=axfreq,
        label='Exponent',
        valmin=1,
        valmax=1.5,
        valinit=exp,
    )

    def update(val):
        # timeplt, sizeplt, coinplt = genData(linEff, numSteps=100, exp=slider.val)
        # ax1.clear()
        # ax2.clear()
        ax4.clear()
        ax4.set_title('Profit')
        ax4.set_xlabel('efficacy')
        ax4.set_ylabel('Coins per Hour')
        # for column, color, name in zip(timeplt, colors, header):
        #     ax1.plot(linEff, column, color=color, label=name)
        # for column, color in zip(sizeplt, colors):
        #     ax2.plot(linEff, column, color=color)

        coinplt = updateCoins(avgTime, avgSize, cpd, likely, exp=slider.val)

        for column, color in zip(coinplt, colors):
            ax4.plot(linEff, column, color=color)


        fig.canvas.draw()

    slider.on_changed(update)

    # resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
    # button = Button(resetax, 'Reset', color="blue", hovercolor='0.975')
    #
    # def reset(event):
    #     slider.reset()
    # button.on_clicked(reset)

    plt.show()
