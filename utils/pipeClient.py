import asyncio
import sys
import time
#import win32pipe, win32file, pywintypes
import threading
import struct
import codecs

class pipeClient():
    def __init__(self,pipeName):
        self.pipeName=pipeName
        self.pipe = None
        try:
            self.pipe = open(pipeName, 'r+b', 0) 
        except:
            print("Pipe Not Found") #please make this prompt nicer
            loop = asyncio.get_event_loop()
            loop.create_task(self.pipeReload())
        self.pipeState = "clear"      

    async def pipeReload(self):
        connection = False
        if self.pipeState != "Reloading":
            self.pipeState = "Reloading"
            print("[Pipe] " + self.pipeName +  " Attempting to reload pipe")
            while not connection:
                await asyncio.sleep(4)
                reload = pipeReloader(self.pipeName) 
                reload.start()
                while reload.status == None:
                    await asyncio.sleep(0.01)
                resp = reload.status
                while reload.is_alive():
                    await asyncio.sleep(0.01)
                if resp == "PipeReady":
                    self.pipe=reload.pipe
                    connection = True
                reload.join()
            print("[Pipe] " + self.pipeName +  " Reload Successful") 
            self.pipeState = "clear"


    async def pipeReader(self): #for whatever reason this reads but however it doesnt get the first two characters
        while self.pipeState != "clear":
            await asyncio.sleep(0.01)
        self.pipeState = "inUse"
        print("Starting read")
        pipeReadComplete=False #stays false until the read is complete in case the pipe broke mid read or something
        while not pipeReadComplete: #retrys the read until its completed successful
            if self.pipe != None: #prevents pipe opening the file None
                reader = pipeReader(self.pipe) 
                reader.start()
                while reader.reader == None:
                    await asyncio.sleep(0.01)
                resp = reader.reader
                while reader.is_alive():
                    await asyncio.sleep(0.01)
                reader.join()
            else:
                resp = "PipeFailedTryAgain"
            if resp == "PipeFailedTryAgain":
                print("[Pipe Reader] Ouch Something Closed The Pipe. Please Reload..")
                await self.pipeReload()
            else:
                pipeReadComplete=True
            await asyncio.sleep(10)
        self.pipeState = "clear"
        return resp

    async def pipeWriter(self,data):
        print("blah")
        pipeFailCount = 0
        while self.pipeState != "clear":
            await asyncio.sleep(0.01)
            pipeFailCount +=1
            if (pipeFailCount==20000):
                print("waiting")
                pipeFailCount=0
        self.pipeState = "inUse"
        print("Active Threads: {0}".format(threading.active_count()))
        pipeWriteComplete=False
        while not pipeWriteComplete: #here to restart the write in the event it failed
            try: #here to catch the error of the read 
                # self.thread = threading.Thread(name='pipeWriter',target=self.write, args=[self.pipe, data])
                # self.thread.start()
                writer = pipeWriter(self.pipe) 
                writer.start()
                while writer.is_alive():
                    await asyncio.sleep(0.01)

                while writer.status == None:
                    await asyncio.sleep(0.01)
                resp = writer.status
                while writer.is_alive():
                    await asyncio.sleep(0.01)
                writer.join()    

                if resp == "Failed":
                    print("[Pipe Writer] Ouch Something Closed The Pipe. Please Reload..")
                    await self.pipeReload()
                elif resp == "Successful":
                    pipeWriteComplete = True

                print("YAYYY")
            except:
                print("[Pipe Writer] Ouch Something Closed The Pipe. Please Reload..")
                await self.pipeReload()
                await asyncio.sleep(5)
                pass
        self.pipeState = "clear"
    
    def write(self,pipe,data):
        print("writing")
        pipe.write(data.encode('utf-16-le').strip(codecs.BOM_UTF16)) #this can probably be removed as byte order doesnt seem to be a thing when using -le or -be
        pipe.seek(0)
        print("written")

    def start(self):
        self.loop.run_forever()

class pipeWriter(threading.Thread):
    def __init__(self,pipe):
        self.status = None
        self.pipe = pipe
        threading.Thread.__init__(self)

    def run(self): 
        try:
            print("writing")
            pipe.write(data.encode('utf-16-le').strip(codecs.BOM_UTF16)) #this can probably be removed as byte order doesnt seem to be a thing when using -le or -be
            pipe.seek(0)
            print("written")
            self.status="Successful"
        except:
            self.status="Failed"

class pipeReloader(threading.Thread):
    def __init__(self,pipeName):
        self.status = None
        self.pipe = None
        self.pipeName = pipeName
        threading.Thread.__init__(self)

    def run(self):  
        while self.status == None:
            try:
                self.pipe = open(self.pipeName, 'r+b', 0) 
                self.status = "PipeReady"
            except: #FileNotFoundError or OSError
                self.status = "PipeFailed"
                print("Pipe " + self.pipeName + "  Not Found") #please make this prompt nicer


class pipeReader(threading.Thread):
    def __init__(self,pipe):
        self.reader = None
        self.pipe = pipe
        threading.Thread.__init__(self)

    def run(self):  
        while self.reader == None:
            try: 
                n = struct.unpack('I', self.pipe.read(4))[0]    # Read str length
                resp = self.pipe.read(n)                           # Read str
                self.pipe.seek(0)        
                resp = resp.decode('utf-16')
                self.reader = resp
            except:
                time.sleep(15)
                self.reader="PipeFailedTryAgain"
                #print("[Pipe Reader] Ouch Something Closed The Pipe. Please Reload..")