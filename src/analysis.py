import utils
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import numpy as np
from games.fishing import fishing


# catch analysis, to be run from src folder
def scale(val, min1, max1, min2, max2):
    range1 = max1 - min1
    prop = (val - min1) / range1

    range2 = max2 - min2

    return range2*prop + min2

def genTimeSize(efficacy, numSteps=100):
    # an = lambda x, y : fish.calcDamage(fish.retrieveFish(x, bias=y)['size'])**1.2
    an = lambda x, y : fish.retrieveFish(x, bias=y)['size']/10

    # time generator
    tg = lambda z : [[fish.calcCastTime(y, z) for x in range(numSteps)] for y in fish.locations]
    averageTimes = [[sum(x) / len(x) for x in tg(y)] for y in efficacy]

    # size generator
    sg = lambda z : [[an(y, z) for x in range(numSteps)] for y in fish.locations]
    averageSizes = [[sum(x) / len(x) for x in sg(y)] for y in efficacy]

    return averageTimes, averageSizes

def genData(averageTimes, averageSizes, exp=1.2):

    cph = lambda t, s : ((60**2) / t) * (fish.calcDamage(s*10)**exp)
    coins = []
    for time, size in zip(averageTimes, averageSizes):
        coins.append([cph(x, y) for x, y in zip(time, size)])

    timeplt = [[x[y] for x in averageTimes] for y, _ in enumerate(averageTimes[0])]
    sizeplt = [[x[y] for x in averageSizes] for y, _ in enumerate(averageSizes[0])]
    coinplt = [[x[y] for x in coins] for y, _ in enumerate(coins[0])]

    return timeplt, sizeplt, coinplt

def updateCoins(times, sizes, exp=1.2):
    cph = lambda t, s : ((60**2) / t) * (fish.calcDamage(s*10)**exp)
    coins = []
    for time, size in zip(times, sizes):
        coins.append([cph(x, y) for x, y in zip(time, size)])
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
    numSteps = 10
    linEff = [scale(x, 0, numSteps, worstEff, bestEff) for x in range(numSteps)]

    avgTime, avgSize = genTimeSize(linEff, numSteps=10000)
    timeplt, sizeplt, coinplt = genData(avgTime, avgSize, exp=1.2)

    colors = ['red', 'green', 'blue', 'yellow']
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, constrained_layout=False, sharex=True, figsize=(8, 8))

    for column, color, name in zip(timeplt, colors, header):
        ax1.plot(linEff, column, color=color, label=name)

    ax1.set_title('Cast times')
    ax1.set_ylabel('time (s)')

    for column, color in zip(sizeplt, colors):
        ax2.plot(linEff, column, color=color)

    ax2.set_title('Fish Size')
    ax2.set_ylabel('Size (cm)')

    for column, color in zip(coinplt, colors):
        ax3.plot(linEff, column, color=color)

    ax3.set_title('Fish Size')
    ax3.set_xlabel('efficacy')
    ax3.set_ylabel('Coins per Hour')

    fig.legend()
    fig.suptitle('Fishing Analysis', fontsize=16)

    # Make a horizontal slider to control the frequency.
    axfreq = plt.axes([0.25, 0.00, 0.65, 0.03], facecolor='blue')
    slider = Slider(
        ax=axfreq,
        label='Exponent',
        valmin=1,
        valmax=1.5,
        valinit=1,
    )

    def update(val):
        # timeplt, sizeplt, coinplt = genData(linEff, numSteps=100, exp=slider.val)
        # ax1.clear()
        # ax2.clear()
        ax3.clear()
        # for column, color, name in zip(timeplt, colors, header):
        #     ax1.plot(linEff, column, color=color, label=name)
        # for column, color in zip(sizeplt, colors):
        #     ax2.plot(linEff, column, color=color)

        coinplt = updateCoins(avgTime, avgSize, exp=slider.val)

        for column, color in zip(coinplt, colors):
            ax3.plot(linEff, column, color=color)

        fig.canvas.draw()

    slider.on_changed(update)

    # resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
    # button = Button(resetax, 'Reset', color="blue", hovercolor='0.975')
    #
    # def reset(event):
    #     slider.reset()
    # button.on_clicked(reset)

    plt.show()
