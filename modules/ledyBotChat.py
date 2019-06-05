from utils import config
from utils import Object
import asyncio
import time
import datetime
from utils import logger
from utils import fileIO
import os
from utils import tcpStream


class ledyBotChat:
    def __init__(self):
        self.l = logger.logs("ledyBotChat") #creates the logger 
        self.l.logger.info("Starting")
        self.ledyDir = '.{0}config{0}LedyChat'.format(os.sep)
        self.ledyPipeNameFile = "{0}{1}pipeNames.json".format(self.ledyDir,os.sep)
        self.msgChannelsFileName = "{0}{1}MsgChannel.json".format(self.ledyDir,os.sep)
        self.generalFileName="{0}{1}general.json".format(self.ledyDir,os.sep)
        #checks for the files to exist
        self.checkFolder()
        self.checkPipeFile()
        fileIO.checkFile("config-example{0}LedyChat{0}MsgChannel.json".format(os.sep),"config{0}LedyChat{0}MsgChannel.json".format(os.sep),"MsgChannel.json",self.l)

        fileIO.checkFile("config-example{0}LedyChat{0}general.json".format(os.sep),"config{0}LedyChat{0}general.json".format(os.sep),"general.json",self.l)
        
        self.tradequeueEnable = fileIO.fileLoad(self.generalFileName)["Tradequeue Enable"]
        self.msgChannels = fileIO.fileLoad(self.msgChannelsFileName)
        #self.pipeNames = fileIO.fileLoad(self.ledyPipeNameFile)
        loop = asyncio.get_event_loop()
        loop.create_task(self.ledyCommands())#creates the add commands task
        # self.ledyPipeObj = pipeClient.pipeClient(self.pipeNames[0]) #loads the command pipe client
        # self.ledyPipeReaderObj = pipeClient.pipeClient(self.pipeNames[1]) #loads the reader pipe client

        self.tcpObj = tcpStream.tcpServer("10000")
        loop.create_task(self.tcpObj.readerCallBackAdder(self.reader))

        #loop.create_task(self.ledyReader())

        self.responseList = []

        #loop.create_task(self.tradequeueOnOff(self.tradequeueEnable))
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


    async def tradequeueOnOff(self,tradequeueEnable): #enable of disable tradequeue when the bot loads 
        enabled = False #potentially redo how this sucker works maybe modify the visual studio code to make this actually work properly
        # while (enabled != True):
        #     await self.tcpObj.write("togglequeue")
        #     if (tradequeueEnable == True):
        #         enabled=commandOutput=="command:togglequeue Trade Queue Enabled."
        #     else:
        #         enabled=commandOutput=="command:togglequeue Trade Queue Disabled."
        #     await asyncio.sleep(2)


    async def ledyReader(self,commandOutput): #reads all messages that come in. hopefully it gets broadcasted to both pipes
        print("reader...")
        self.l.logger.info("[but] {0}".format(commandOutput))
        for key,val in self.msgChannels.items():#chat output to wherever
            botRoles= {"":0}
            if commandOutput.split(" ")[0] == "msg:trade":
                msg = commandOutput
                x = msg.replace("msg:trade", " ")[2:]
                #x = x.replace(" ","__<->__")#some weird string that shouldnt be used we hope
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
            else:
                await self.processMsg(message=commandOutput,username="Bot",channel=val["Channel"],server=val["Server"],service=val["Service"],roleList=botRoles)       


    async def reader(self,message):
        self.l.logger.info("reading message: " + message)
        await self.handleResponseList(message)

    async def handleResponseList(self,message): #sends callbacks for responses from the tcp stream
        messageType = message.split(" ")[0]
        for response in self.responseList:
            if response["messageType"] == messageType:
                await response["callback"](message,*response["args"])
                self.responseList.remove(response)

    async def getMessageaa(self,messageType): #cycles message in case it recieves a msg not a command respond
        commandOutput = ""
        while commandOutput.split(" ")[0] != messageType:
            commandOutput = await self.ledyPipeObj.pipeReader()
        return commandOutput

    async def getResponse(self,messageType,callback, *args):
        self.responseList.append({"callback": callback, "messageType": messageType, "args": list(args)})
        


    async def ledyCommands(self): #adds the commands to the commands module
        config.events.addCommandType(commandType="ledyDsStart",commandHandler=self.startLedyBot)
        config.events.addCommandType(commandType="ledyDsStop",commandHandler=self.stopLedyBot)
        config.events.addCommandType(commandType="ledyDsConnect",commandHandler=self.connectDSLedyBot)
        config.events.addCommandType(commandType="ledyDsDisconnect",commandHandler=self.disconnectDSLedyBot)
        config.events.addCommandType(commandType="ledyDsRefresh",commandHandler=self.refreshLedyBot)
        config.events.addCommandType(commandType="ledyDsTradequeue",commandHandler=self.tradequeueLedyBot)
        config.events.addCommandType(commandType="ledyDsViewqueue",commandHandler=self.viewqueueLedyBot)



    async def startLedyBot(self,message,command): #sends the start command to start the bot
        await self.tcpObj.write("startgtsbot")
        await self.getResponse("command:startgtsbot",self.startLedyBotCallback,message)
        
        
    async def startLedyBotCallback(self,response,message):
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
        await self.tradequeueOnOff(self.tradequeueEnable)


    async def stopLedyBot(self,message,command): #sends the stop command to stop the bot
        await self.tcpObj.write("stopgtsbot")
        await self.getResponse("command:startgtsbot",self.stopLedyBotCallback,message)

    async def stopLedyBotCallback(self,response,message):   
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       

            
    async def connectDSLedyBot(self,message,command): #starts the bot to connect to the 3ds
        await self.tcpObj.write("connect3ds")
        await self.getResponse("command:connect3ds",self.connectDSLedyBotCallback,message)

    async def connectDSLedyBotCallback(self,response,message):   
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
  

    async def disconnectDSLedyBot(self,message,command): #disconnects from the 3ds
        await self.tcpObj.write("disconnect3ds")   
        await self.getResponse("command:disconnect3ds",self.disconnectDSLedyBotCallback,message)

    async def disconnectDSLedyBotCallback(self,response,message):   
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
  

    async def refreshLedyBot(self,message,command): #refreshs giveaway details and bans
        splitMsg = message.Message.Contents.split(" ")
        if len(splitMsg) == 3:
            await self.tcpObj.write("refresh {0} {1}".format(splitMsg[1],splitMsg[2])) 
        elif len(splitMsg) == 2:
            await self.tcpObj.write("refresh {0} {1}".format(splitMsg[1],splitMsg[2])) 
        elif len(splitMsg) == 1:
            await self.tcpObj.write("refresh") 
        await self.getResponse("command:refresh",self.refreshLedyBotCallback,message)

    async def refreshLedyBotCallback(self,response,message):   
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
    

    async def tradequeueLedyBot(self,message,command): #enables or disables trade queue
        await self.tcpObj.write("togglequeue")
        await self.getResponse("command:togglequeue",self.tradequeueLedyBotCallback,message)


    async def tradequeueLedyBotCallback(self,response,message):   
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       

    async def viewqueueLedyBot(self,message,command): #views the trade queue. it can accept whatever page u wanna view of the trade queue as well
        splitMsg = splitMsg = message.Message.Contents.split(" ")
        if len(splitMsg) == 2:
            await self.tcpObj.write("viewqueue " + splitMsg[1])
        else:
            await self.tcpObj.write("viewqueue")
        await self.getResponse("command:viewqueue",self.viewqueueLedyBotCallback,message)
        
    async def viewqueueLedyBotCallback(self,response,message):       
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
        

        


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