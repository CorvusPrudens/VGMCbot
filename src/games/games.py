import time
import requests
import fishing

class Games:

    def __init__(self):
        self.players = {}
        self.commands = fishing.funcDict
        self.commandString = fishing.fishCommands

    def gameLoop(self):
        pass

# games = Games()
#
# fishing.initFishing(games.players, 'corvus')
# print(games.players)
