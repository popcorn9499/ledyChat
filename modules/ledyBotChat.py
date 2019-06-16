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
        self.fcListFileName ="{0}{1}fcList.json".format(self.ledyDir,os.sep)
        #checks for the files to exist
        self.checkFolder()
        self.checkPipeFile()
        fileIO.checkFile("config-example{0}LedyChat{0}MsgChannel.json".format(os.sep),"config{0}LedyChat{0}MsgChannel.json".format(os.sep),"MsgChannel.json",self.l)

        fileIO.checkFile("config-example{0}LedyChat{0}general.json".format(os.sep),"config{0}LedyChat{0}general.json".format(os.sep),"general.json",self.l)
        
        try:
            self.fcList = fileIO.fileLoad(self.fcListFileName)
        except:
            self.fcList = [] 

        self.tradequeueEnable = fileIO.fileLoad(self.generalFileName)["Tradequeue Enable"]
        self.msgChannels = fileIO.fileLoad(self.msgChannelsFileName)
        

        self.onGoingCommandList = []
        loop = asyncio.get_event_loop()
        loop.create_task(self.ledyCommands())#creates the add commands task

        if not 'port' in fileIO.fileLoad(self.generalFileName):
            temp = fileIO.fileLoad(self.generalFileName)
            temp.update({"port": "10000"}) #default port
            fileIO.fileSave(self.generalFileName,temp) #save the new config

        self.tcpPort = fileIO.fileLoad(self.generalFileName)["port"]
        self.tcpObj = tcpStream.tcpServer(self.tcpPort)
        loop.create_task(self.tcpObj.readerCallBackAdder(self.reader))
        loop.create_task(self.tcpObj.onConnectCallBackAdder(self.sendFCs))
        self.responseList = []
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

    async def sendFCs(self):
        await self.checkFCs()
        for fc in self.fcList:
           await self.tcpObj.write("addFcTrade " + fc["fc"])

    async def checkFCs(self): #checks for duplicate fcs
        for fcCheck in self.fcList:
            for fc in self.fcList:
                if fc["fc"] == fcCheck["fc"]:
                    self.fcList.remove(fc)
        fileIO.fileSave(self.fcListFileName,self.fcList)

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
                pass
                #await self.processMsg(message=commandOutput,username="Bot",channel=val["Channel"],server=val["Server"],service=val["Service"],roleList=botRoles)       


    async def reader(self,message):
        self.l.logger.info("reading message: " + message)
        await self.handleResponseList(message)
        await self.ledyReader(message)

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
        config.events.addCommandType(commandType="ledySearchBanFCList",commandHandler=self.searchBanFCsLedyBot)
        config.events.addCommandType(commandType="ledyAddFC",commandHandler=self.addFC)
        config.events.addCommandType(commandType="ledyViewFC",commandHandler=self.viewFC)

    async def addFC(self,message,command):
        fc = ""
        botRoles= {"":0}
        try: #if the command isnt long enough complain to the user
            fc = message.Message.Contents.split(" ")[1]
        except IndexError:
            result = command["HelpDetails"]
            await self.processMsg(message=result,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)
            return
        fc = fc.replace("-","")
        fc = fc.replace(" ", "")
        if not fc.isdigit() or len(fc) != 12: #checks if the fc is digits and the correct length
            result = command["HelpDetails"]
            await self.processMsg(message=result,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)
            return

        for fcL in self.fcList: #cycles the fcs to see if the fc exists already
            if fcL["fc"] == fc:
                self.fcList.remove(fcL)

        self.fcList.append({"username": message.Message.User,"fc": fc})
        fileIO.fileSave(self.fcListFileName,self.fcList)
        print("Adding the fc")
        try:
            await self.tcpObj.write("addFcTrade " + fc)
        except:
            result = command["botDown"]
            await self.processMsg(message=result,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)

        await self.processMsg(message="Your FC was added!!",username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles) #returns the data to the user

    async def viewFC(self,message,command):
        user = message.Message.User
        botRoles= {"":0}
        for fc in self.fcList:
            if fc["username"] == user:
                response = "Your fc: " + fc["fc"]
                await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       
  

    async def searchBanFCsLedyBot(self,message,command): #sends the start command to start the bot
        await self.tcpObj.write("listBanFCList")
        await self.getResponse("command:listBanFCList",self.searchBanFCsBotCallback,message,command)
        
        
    async def searchBanFCsBotCallback(self,response,message,command):
        botRoles= {"":0}
        fcData = [] #stores all the fc data in between and during this command
        onGoing = None
        finalResponse = False #keeps track of whether ledybot has more fcs to talk about
        for x in self.onGoingCommandList: #cycles to see if this command has been started before and not finished
            #this will only occur is the fc list is fairly large
            if x["message"] == message:
                fcData = x["fcData"]
                onGoing = x
                break
        
        
        details = response.split(" ")
        
        if details[1] == ":Done": #determines if this is a final response from the ledybot connection or not
            finalResponse = True
            details.pop(1)

        fcResponse = details[1].split("&")

        fcData = fcData + fcResponse

        if onGoing != None:#keeps the ongoing message list clear
            self.onGoingCommandList.remove(onGoing)

        if not finalResponse: #if not final response create a onGoingCommand in the queue
            info = {"message":message, "fcData": fcData}
            self.onGoingCommandList.append(info)
            return    

        try: #if the command isnt long enough complain to the user
            checkFor = message.Message.Contents.split(" ")[1]
        except IndexError:
            result = command["HelpDetails"]
            await self.processMsg(message=result,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)
            return

        banned = False #inocent until proven guilty
        for banFC in fcData: #cycles list for banned fcs
            if banFC == checkFor:
                banned = True
        if banned:
            result = command["userBanned"]
        else:
            result = command["userNotBanned"]

        await self.processMsg(message=result,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles) #returns the data to the user



    async def startLedyBot(self,message,command): #sends the start command to start the bot
        await self.tcpObj.write("startgtsbot")
        await self.getResponse("command:startgtsbot",self.startLedyBotCallback,message)
        
        
    async def startLedyBotCallback(self,response,message):
        botRoles= {"":0}
        await self.processMsg(message=response,username="Bot",channel=message.Message.Channel,server=message.Message.Server,service=message.Message.Service,roleList=botRoles)       


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