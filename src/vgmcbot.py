import asyncio
import sys
import discord
import structs

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
client = structs.extClient(funcDict, peasantCommands, intents=intents)
# regex = Regex()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    client.loadBank()
    # loadBank(bank, cachePath)
    # client.addCommands()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Just so the bot doesn't feel neurotic
    await asyncio.sleep(0.5)

    await client.preMention(message)

    # Proper parsing would be best here, but this
    # will work for now
    if client.user.mentioned_in(message):
        # This means that the first command left-to-right is
        # the one that is executed. I think this is fine.
        command = client.commRegex.search(message.content.lower())
        if command != None:
            await client.execComm(command, message)
            # await client.funcDict[command.group(0)](message, client)
        else:
            mess = 'what\'s up gamer {}'.format(rand.choice(client.data.cute))
            await message.channel.send(mess)

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
