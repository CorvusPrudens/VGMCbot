import discord
from re import compile

################################################################################
########################## main globals ########################################
################################################################################

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
client = discord.Client(intents=intents)
botID = '782113493797044224'
cachePath = 'bank.csv'
prevChoice = 0
leader = 'Leader'
bank = {}
timeBound = {
    'morning': [5, 12],
    'night': [17, 5]
}

################################################################################
########################## text data ###########################################
################################################################################

imgur = 'https://i.imgur.com/'
end = '.jpg'
honks = [
    '9LXSJdC',
    'BzYrnYp',
    'kq3B5UK',
    'z44rteZ',
    'Ewh9N3k'
]

hankUrl1 = "https://static.wikia.nocookie.net/kingofthehill/images/c/c4/"
hankUrl2 = "Hank_Hill.png/revision/latest/top-crop/width/360/height/450?cb=20140504043948"
commandsHeader = "When you mention me, I'll do a command for you! {}"
leaderCommands = """
✿ give @<username> <value> coins -- this will give <username> the <value> of coins!
"""

peasantCommands = """
✿ help -- I'll list out all these commands for you!
✿ hmc -- "How Many Coins;" this'll tell you how many you've got!
✿ list -- List out all the VGMConnoisseurs!
✿ uwu -- UwU
✿ morning -- I'll saw good morning!
✿ night -- I'll say goodnight!
"""

responses = {
    'give': "Ok! {} now has {:,.2f} VGMCoins {}",
    'giveErr': """I'm sorry {}, I didn't quite catch that.
The \"give\" syntax is \"give @<username> <number> coins\" {}""",
    'permission': "sorry {}, you don't have permission to give coins {}",
    'hmc': 'hey {}, looks like you have {} VGMCoins {}',
    'list': 'get ready {}\n',
    'listItem': '✿ {}\n  -- {:,.2f} VGMCoins\n',
    'uwu': 'UwU {}',
    'time': '✧ good {} gamer {} ✧',
    'nottime': 'b-but... it\'s not {} {}'
}

cute = [
    '(✿◠‿◠)',
    '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧',
    '(▰˘◡˘▰)',
    '(づ｡◕‿‿◕｡)づ',
    'v(=∩_∩=)ﾌ',
    '(~￣▽￣)~',
    'ヾ(〃^∇^)ﾉ',
    'Ｏ(≧▽≦)Ｏ',
    'UwU',
    '~^o^~'
]

sad = [
    'ಥ_ಥ',
    '(◕︵◕)',
    'o(╥﹏╥)o',
    '(⊙﹏⊙✿)',
    '◄.►',
    '┐(‘～`；)┌',
    '(∩︵∩)',
    '●︿●',
    'ਉ_ਉ'
]

################################################################################
########################## regex ###############################################
################################################################################

timeRegex = compile('(?<=T)[0-9]{1,2}')
timePartRegex = compile('\\b(morning)|(night)\\b')
honkRegex = compile('\\b(honk)s*\\b')
hankRegex = compile('\\b(hank)\\b')
mentionRegex = compile('((?<=(<@)[!&])|(?<=<@))[0-9]+(?=>)')
reactRegex = compile('(?<=<:)[A-Za-z_0-9]+')
commRegex = compile('\\b(give)|(help)|(hmc)|(list)|(uwu)|(night)|(morning)\\b')
