import discord
import asyncio

class extClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.printing())
        self.counter = 0

    # async def on_ready(self):
    #     print('Logged in as')
    #     print(self.user.name)
    #     print(self.user.id)
    #     print('------')

    # for games, we'll probably want to load and store data
    # as json, since it's easy to convert a dictionary to json.
    # this will also ensure easy adding and removing of keys if i
    # want to add and remove games

    async def printing(self):
        await self.wait_until_ready()
        while not self.is_closed():
            self.counter += 1
            # print(self.counter)
            await asyncio.sleep(1) # task runs every 60 seconds
