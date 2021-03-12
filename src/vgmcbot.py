import sys

import discord

import structs


intents = discord.Intents.default()
intents.reactions = True
intents.members = True
client = structs.extClient(intents=intents)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    client.loadBank()
    client.loadNameCache()
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
    if user == client.user or not reaction.custom_emoji:
        return
    await client.reactionAdd(reaction, user)


# this event explicitly needs the members privileged intent
# worth?
@client.event
async def on_reaction_remove(reaction, user):
    if user == client.user or not reaction.custom_emoji:
        return
    await client.reactionRemove(reaction, user)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please provide the bot token as a command line argument!')
        exit(1)

    client.run(sys.argv[1])
