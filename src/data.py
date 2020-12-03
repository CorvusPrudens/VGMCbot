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
        self.commandsHeader = "When you mention me, I'll do a command for you! {}"
        self.leaderCommands = """
        ✿ give @<username> <value> coins -- this will give <username> the <value> of coins!
        """

        self.peasantCommands = """
        ✿ help -- I'll list out all these commands for you!
        ✿ hmc -- "How Many Coins;" this'll tell you how many you've got!
        ✿ list -- List out all the VGMConnoisseurs!
        ✿ uwu -- UwU
        ✿ morning -- I'll saw good morning!
        ✿ night -- I'll say goodnight!
        """

        self.responses = {
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
        self.timePartRegex = re.compile('\\b(morning)|(night)\\b')
        self.honkRegex = re.compile('\\b(honk)s*\\b')
        self.hankRegex = re.compile('\\b(hank)\\b')
        self.mentionRegex = re.compile('((?<=(<@)[!&])|(?<=<@))[0-9]+(?=>)')
        self.reactRegex = re.compile('(?<=<:)[A-Za-z_0-9]+')
