import asyncio
import sys
import random as rand
from data import *
from utils import *
from commands import *


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    loadBank(bank, cachePath)
    client.addCommands()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Just so the bot doesn't feel neurotic
    await asyncio.sleep(0.5)

    await preMention(message)

    # Proper parsing would be best here, but this
    # will work for now
    if client.user.mentioned_in(message):
        # This means that the first command left-to-right is
        # the one that is executed. I think this is fine.
        command = commRegex.search(message.content.lower())
        if command != None:
            await funcDict[command.group(0)](message, client)
        else:
            mess = 'what\'s up gamer {}'.format(rand.choice(cute))
            await message.channel.send(mess)

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user or not reaction.custom_emoji:
        return
    await reactionAdd(reaction, user)

# this event explicitly needs the members privileged intent
# worth?
@client.event
async def on_reaction_remove(reaction, user):
    if user == client.user or not reaction.custom_emoji:
        return
    await reactionRemove(reaction, user)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please provide the bot token as a command line argument!')
        exit(1)

    client.run(sys.argv[1])
