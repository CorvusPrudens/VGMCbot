import re

################################################################################
########################## text data ###########################################
################################################################################

class Data:
    def __init__(self):
        self.botID = '782113493797044224'
        self.cachePath = 'bank.csv'
        self.prevChoice = 0
        self.leader = 'Leader'
        self.bank = {}
        self.timeBound = {
            'morning': [5, 12],
            'night': [17, 5]
        }

        self.timeUrl = 'https://worldtimeapi.org/api/timezone/America/New_York'

        self.imgur = 'https://i.imgur.com/'
        self.end = '.jpg'
        self.honks = [
            '9LXSJdC',
            'BzYrnYp',
            'kq3B5UK',
            'z44rteZ',
            'Ewh9N3k'
        ]

        self.hankUrl1 = "https://static.wikia.nocookie.net/kingofthehill/images/c/c4/"
        self.hankUrl2 = "Hank_Hill.png/revision/latest/top-crop/width/360/height/"
        self.hankUrl3 = "450?cb=20140504043948"
        self.commandsHeader = "if you prefix something with a dot, I'll do a command for you! {}"
        self.leaderCommands = """
Leader commands:
✿ .give @<username> <value> coins -- this will give <username> the <value> of coins!
✿ .addimg <image url> -- this will add the given image to the current mgm raffle!
✿ .mgmvote -- this will kick off mgm voting!
✿ .mgmwin -- this will end mgm voting and announce the winning images!
"""

        self.peasantCommands = """
✿ .help <option> -- I'll list out all these commands for you! (options: {})
✿ .hmc -- "How Many Coins;" this'll tell you how many you've got!
✿ .list -- List out all the VGMConnoisseurs!
✿ .uwu -- UwU
✿ .morning -- I'll saw good morning!
✿ .night -- I'll say goodnight!
"""

        self.responses = {
            'give': "Ok! {} now has {:,.2f} VGMCoins {}",
            'giveErr': """I'm sorry {}, I didn't quite catch that.
The \"give\" syntax is \"give @<username> <number> coins\" {}""",
            'permission': "sorry {}, you don't have permission to give coins {}",
            'hmc': 'hey {}, looks like you have {:,.2f} VGMCoins {}',
            'list': 'get ready {}\n',
            'listItem': '✿ {}\n  -- {:,.2f} VGMCoins\n',
            'uwu': 'UwU {}',
            'time': '✧ good {} gamer {} ✧',
            'nottime': 'b-but... it\'s not {} {}',
            'addimg': 'Ok! I\'ve added that to the list {}',
            'addimgErr': 'I\'m sorry, I didn\'t catch that {}\nMake sure the image is given as a link!',
            'addimgPerm': "sorry {}, you don't have permission to add images {}",
            'mgmvotePerm': "sorry {}, you don't have permission to start the vote {}",
            'mgmvoteErr': "there's no images!! {}",
            'mgmwinPerm': "sorry {}, you don't have permission to end the vote {}",
        }

        self.cute = [
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

        self.sad = [
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

        self.timeRegex = re.compile('(?<=T)[0-9]{1,2}')
        self.timePartRegex = re.compile('(?<=\\.)((morning)|(night))\\b')
        self.honkRegex = re.compile('\\b(honk)s*\\b')
        self.hankRegex = re.compile('\\b(hank)\\b')
        self.mentionRegex = re.compile('((?<=(<@)[!&])|(?<=<@))[0-9]+(?=>)')
        self.reactRegex = re.compile('(?<=<:)[A-Za-z_0-9]+')

        self.mgm = []

        self.prefix = '.'
