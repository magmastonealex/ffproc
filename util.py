class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class loglevels:
    VERBOSE = 5
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    level_colors = { VERBOSE : bcolors.OKGREEN, INFO : bcolors.OKBLUE, WARNING : bcolors.WARNING, ERROR : bcolors.FAIL, CRITICAL : bcolors.FAIL}

class Log:
    @staticmethod
    def v(tag,message):
        level = loglevels.VERBOSE
        Log.log(tag,message,level)
    @staticmethod
    def i(tag,message):
        level = loglevels.INFO
        Log.log(tag,message,level)
    @staticmethod
    def w(tag,message):
        level = loglevels.WARNING
        Log.log(tag,message,level)
    @staticmethod
    def e(tag,message):
        level = loglevels.ERROR
        Log.log(tag,message,level)
    @staticmethod
    def c(tag,message):
        level = loglevels.CRITICAL
        Log.log(tag,message,level)

    @staticmethod
    def log(fromModule, message, level):
        minLevel = 0
        if level > minLevel:
            print(loglevels.level_colors[level] + "["+fromModule+"] "+ message + bcolors.ENDC)
