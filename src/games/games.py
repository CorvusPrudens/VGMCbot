import json
from games.fishing import fishing
# from games.rogue import rogue

# TODO -- fix changing dictionary size while iterating -- can just
# copy the main dict before any iteration (memory intensive but safe?)

# IDEA -- for the roguelike, there should not be a map that always shows up
# however, there should be an item that allows you to print out a map and
# most importantly, that map should have different 'sizes' to accomodate
# different devices (whether through different fonts or characters and whatnot)

class Games:

    def __init__(self, playerPath, miscPath):
        self.players = {}
        self.misc = {}
        self.commands = {}
        self.games = {}
        self.helpDict = {}
        self.games['fishing'] = fishing.GameFishing()
        # self.games['rogue'] = rogue.GameRogue()
        self.playerPath = playerPath
        self.miscPath = miscPath

        for game in self.games:
            for key in self.games[game].commands:
                self.commands[key] = self.games[game].commands[key]
            self.helpDict.update(self.games[game].helpDict)
        self.load()

    async def execComm(self, command, message, client):
        await self.commands[command](message, client)

    async def gameLoop(self, client):
        for game in self.games:
            await self.games[game].gameLoop(self.players, client)

    def load(self, misc=True):
        try:
            with open(self.playerPath, 'r') as file:
                self.players = json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            pass
        if misc:
            try:
                with open(self.miscPath, 'r') as file:
                    self.misc = json.load(file)
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                pass

    def save(self, misc=True):
        with open(self.playerPath, 'w') as file:
            json.dump(self.players, file, indent=2)
        if misc:
            with open(self.miscPath, 'w') as file:
                json.dump(self.misc, file, indent=2)


# games = Games()
#
# fishing.self.initFishing(games.players, 'corvus')
# print(games.players)
