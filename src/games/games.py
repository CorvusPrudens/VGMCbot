import json
from games.fishing import fishing
from games.rogue import rogue

# TODO -- fix changing dictionary size while iterating -- can just
# copy the main dict before any iteration (memory intensive but safe?)

# IDEA -- for the roguelike, there should not be a map that always shows up
# however, there should be an item that allows you to print out a map and
# most importantly, that map should have different 'sizes' to accomodate
# different devices (whether through different fonts or characters and whatnot)

class Games:

    def __init__(self, playerPath, miscPath, client):
        self.players = {}
        self.misc = {}
        self.commands = {}
        self.games = {}
        self.helpDict = {}
        self.games['fishing'] = fishing.GameFishing(client)
        # self.games['rogue'] = rogue.GameRogue(client)
        self.playerPath = playerPath
        self.miscPath = miscPath

        for game in self.games:
            for key in self.games[game].commands:
                self.commands[key] = self.games[game].commands[key]
            self.helpDict.update(self.games[game].helpDict)
        self.load()

    async def loadAsync(self):
        if 'rogue' in self.games:
            await self.games['rogue'].load()

    def gameDecorators(self, slash, guild_ids):
        for game in self.games:
            self.games[game].decorators(slash, guild_ids)


    async def execComm(self, command, message):
        await self.commands[command](message)

    async def execCommReact(self, reaction, user, add=True):
        for game in self.games:
            await self.games[game].reactLoop(reaction, user, add)

    async def gameLoop(self):
        for game in self.games:
            await self.games[game].gameLoop(self.players)

    def load(self, misc=True):
        try:
            with open(self.playerPath, 'r') as file:
                self.players = json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            print("NOT FOUND", e)
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
