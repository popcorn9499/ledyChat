from utils.Events import Events
from utils.EventHook import EventHook
from utils import config
from sites import discord
from sites import youtube
from sites import irc
from utils import logger
#from utils import deleteMsg
from modules import chatbot
#from modules import chatLog
from modules import command
from modules import ledyBotChat

async def messageTest(Message):
    print(Message.Contents)




#talk to ezpz about start command


#events.onMessage += messageTest
# config.events.onMessage += messageTest

# print(config.events.__dict__)

# print(config.x)

chatbot = chatbot.chatbot()

#chatLog = chatLog.chatLog()



#this is the starting point for all the bot tasks
discordP = discord.Discord()
discordP.start(config.c.discordToken)




# x = input()


# if x == "1":
#     print(events.onMessage(Message="Message"))
