import sys

import discord
from discord_slash import SlashCommand

import structs


intents = discord.Intents.default()
intents.reactions = True
intents.members = True
client = structs.ExtendedClient(intents=intents)

#slash = SlashCommand(client, sync_commands=True) # Declares slash commands through the client.
#guild_ids = [566052452114366482] # for quick debug (final needs to be global)
#client.gameDecorators(slash, guild_ids)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # client.loadBank()
    client.loadLedger()
    client.loadNameCache()
    # await client.games.loadAsync() # WARNING -- uncomment for production!!
    # loadBank(bank, cachePath)
    # client.addCommands()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await client.preMention(message)

    command = client.commRegex.search(message.content.lower())
    if command != None:
        await client.execComm(command.group(0), message)


@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return
    elif not reaction.custom_emoji:
        await client.games.execCommReact(reaction, user, add=True)
    else:
        await client.reactionAdd(reaction, user)


# this event explicitly needs the members privileged intent
# worth?
@client.event
async def on_reaction_remove(reaction, user):
    if user == client.user:
        return
    elif not reaction.custom_emoji:
        await client.games.execCommReact(reaction, user, add=False)
    else:
        await client.reactionRemove(reaction, user)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please provide the bot token as a command line argument!')
        exit(1)

    client.run(sys.argv[1])
