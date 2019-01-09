from utils import config
from utils import Object
import asyncio
import time
import datetime
from utils import logger
from utils import fileIO
import os
from utils import pipeClient


class ledyBotChat:
    def __init__(self):
        self.l = logger.logs("ledyBotChat") #creates the logger 
        self.l.logger.info("Starting")
        #checks for the files to exist
        self.checkFolder()
        self.checkPipeFile()
        fileIO.checkFile("config-example{0}LedyChat{0}MsgChannel.json".format(os.sep),"config{0}LedyChat{0}MsgChannel.json".format(os.sep),"MsgChannel.json",self.l)

        self.ledyDir = '.{0}config{0}LedyChat'.format(os.sep)
        self.ledyPipeNameFile = "{0}{1}pipeNames.json".format(self.ledyDir,os.sep)
        self.msgChannelsFileName = "{0}{1}MsgChannel.json".format(self.ledyDir,os.sep)
        self.msgChannels = fileIO.fileLoad(self.msgChannelsFileName)
        self.pipeNames = fileIO.fileLoad(self.ledyPipeNameFile)
        loop = asyncio.get_event_loop()
        loop.create_task(self.ledyCommands())#creates the add commands task
        self.ledyPipeObj = pipeClient.pipeClient(self.pipeNames[0]) #loads the command pipe client
        self.ledyPipeReaderObj = pipeClient.pipeClient(self.pipeNames[1]) #loads the reader pipe client
        loop.create_task(self.ledyReader())
        self.l.logger.info("Started")

    def checkFolder(self):
        if os.path.isdir(self.ledyDir) == False:
            self.l.logger.info("LedyChat Folder Does Not Exist")
            self.l.logger.info("Creating...")
            os.makedirs(self.ledyDir)

    def checkPipeFile(self):
        if (os.path.isfile(self.ledyPipeNameFile) == False):
            self.l.logger.info("pipeNames.json File Does Not Exist")
            self.l.logger.info("Creating...")
            pipeNames = [r"\\.\pipe\LedyChat",r"\\.\pipe\LedyChatReader"]
            fileIO.fileSave(self.ledyPipeNameFile,pipeNames)


    async def ledyReader(self): #reads all messages that come in. hopefully it gets broadcasted to both pipes
        while True:
            commandOutput = await self.ledyPipeReaderObj.pipeReader()
            commandOutput = await self.messageFix(commandOutput)
            print("reader...")
            self.l.logger.info("[but] {0}".format(commandOutput))
            for key,val in self.msgChannels.items():#chat output to wherever
                botRoles= {"":0}
                if commandOutput.split(" ")[0] == "msg:trade":
                    msg = commandOutput
                    x = msg.replace("msg:trade", " ")[2:]
                    x = x.replace(" ","__<->__")#some weird string that shouldnt be used we hope
                    x = x.split("|")
                    trainer = x[0]
                    name = x[1]
                    country = x[2]
                    subReddit = x[3]
                    pokemon = x[4]
                    fc = x[5]
                    page = x[6]
                    index = x[7]
                    formatOpts = {"%ledyTrainerName%":trainer,"%ledyNickname%":name,"%ledyCountry%":country,"%ledySubReddit%":subReddit,"%ledyPokemon%":pokemon,"%ledyFC%":fc,"%ledyPage%":page,"%ledyIndex%":index}
                    await self.processMsg(message=commandOutput,username="Bot",channel=val["Channel"],server=val["Server"],service=val["Service"],roleList=botRoles,formatOpts=formatOpts,formattingSettings=val["TradeFormatting"],formatType="Other")
            await self.processMsg(message=commandOutput,username="Bot",channel=val["Channel"],server=val["Server"],service=val["Service"],roleList=botRoles,formatOpts=formatOpts)       
           


    async def messageFix(self,message): #fixes the first two characters missing from the pipe
        if message.split(":")[0] == "g": #msg fix
                message = "ms{0}".format(message)
        elif message.split(":")[0] == "mmand": #command fix
            message = "co{0}".format(message)
        return message

    async def getMessage(self,messageType): #cycles message in case it recieves a msg not a command respond
        commandOutput = ""
        while commandOutput.split(":")[0] != messageType:
            commandOutput = await self.ledyPipeObj.pipeReader()
            commandOutput = await self.messageFix(commandOutput)
        return commandOutput


    async def ledyCommands(self): #adds the commands to the commands module
        config.events.addCommandType(commandType="ledyDsStart",commandHandler=self.startLedyBot)
        config.events.addCommandType(commandType="ledyDsStop",commandHandler=self.stopLedyBot)
        config.events.addCommandType(commandType="ledyDsConnect",commandHandler=self.connectDSLedyBot)
        config.events.addCommandType(commandType="ledyDsDisconnect",commandHandler=self.disconnectDSLedyBot)
        config.events.addCommandType(commandType="ledyDsRefresh",commandHandler=self.refreshLedyBot)
        config.events.addCommandType(commandType="ledyDsTradequeue",commandHandler=self.tradequeueLedyBot)
        config.events.addCommandType(commandType="ledyDsViewqueue",commandHandler=self.viewqueueLedyBot)



    async def startLedyBot(self,message,command): #sends the start command to start the bot
        await self.ledyPipeObj.pipeWriter("startgtsbot")

    async def stopLedyBot(self,message,command): #sends the stop command to stop the bot
        await self.ledyPipeObj.pipeWriter("stopgtsbot")
        commandOutput = await self.getMessage("command")
        botRoles= {"":0}
        await self.processMsg(message=commandOutput,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       

            
    async def connectDSLedyBot(self,message,command): #starts the bot to connect to the 3ds
        await self.ledyPipeObj.pipeWriter("connect3ds")
        commandOutput = await self.getMessage("command")
        botRoles= {"":0}
        await self.processMsg(message=commandOutput,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
  

    async def disconnectDSLedyBot(self,message,command): #disconnects from the 3ds
        await self.ledyPipeObj.pipeWriter("disconnect3ds")   
        commandOutput = await self.getMessage("command")
        botRoles= {"":0}
        await self.processMsg(message=commandOutput,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
  

    async def refreshLedyBot(self,message,command): #refreshs giveaway details and bans
        splitMsg = message.Message.Contents.split(" ")
        if len(splitMsg) == 3:
            await self.ledyPipeObj.pipeWriter("refresh {0} {1}".format(splitMsg[1],splitMsg[2])) 
        elif len(splitMsg) == 2:
            await self.ledyPipeObj.pipeWriter("refresh {0} {1}".format(splitMsg[1],splitMsg[2])) 
        elif len(splitMsg) == 1:
            await self.ledyPipeObj.pipeWriter("refresh") 
        commandOutput = await self.getMessage("command")
        botRoles= {"":0}
        await self.processMsg(message=commandOutput,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
    

    async def tradequeueLedyBot(self,message,command): #enables or disables trade queue
        await self.ledyPipeObj.pipeWriter("togglequeue")
        commandOutput = await self.getMessage("command")
        botRoles= {"":0}
        await self.processMsg(message=commandOutput,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       

    async def viewqueueLedyBot(self,message,command): #views the trade queue. it can accept whatever page u wanna view of the trade queue as well
        splitMsg = splitMsg = message.Message.Contents.split(" ")
        if len(splitMsg) == 2:
            await self.ledyPipeObj.pipeWriter("viewqueue " + splitMsg[1])
        else:
            await self.ledyPipeObj.pipeWriter("viewqueue")
        commandOutput = await self.getMessage("command")
        botRoles= {"":0}
        await self.processMsg(message=commandOutput,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
        

        


    async def processMsg(self,username,message,roleList,server,channel,service,formatOpts="",formattingSettings=None,formatType=None):
        print("ya... {0}".format(message))
        formatOptions = {"%authorName%": username, "%channelFrom%": channel, "%serverFrom%": server, "%serviceFrom%": service,"%message%":"message","%roles%":roleList}
        formatOptions.update(formatOpts)
        message = Object.ObjectLayout.message(Author=username,Contents=message,Server=server,Channel=channel,Service=service,Roles=roleList)
        objDeliveryDetails = Object.ObjectLayout.DeliveryDetails(Module="Command",ModuleTo="Site",Service=service,Server=server,Channel=channel)
        if (formattingSettings==None or formatType==None):
            objSendMsg = Object.ObjectLayout.sendMsgDeliveryDetails(Message=message, DeliveryDetails=objDeliveryDetails, FormattingOptions=formatOptions,messageUnchanged="None")
        else:
            objSendMsg = Object.ObjectLayout.sendMsgDeliveryDetails(Message=message, DeliveryDetails=objDeliveryDetails, FormattingOptions=formatOptions,formattingSettings=formattingSettings,formatType=formatType,messageUnchanged="None")

        config.events.onMessageSend(sndMessage=objSendMsg)     


#refresh [mode] [filename]

#connect3ds 

#disconnect3ds

#startgtsbot 



#stopgtsbot 

'''
whats missing:
    trade commnad
        to add trades i think?

    remove command
        remove trades???

    responding to any message that may come through

'''

ledy = ledyBotChat()