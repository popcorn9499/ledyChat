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
        try:
            self.pipe = open(pipeName, 'r+b', 0) 
        except FileNotFoundError:
            print("Pipe Not Found") #please make this prompt nicer

        self.pipeState = "clear"      

    async def pipeReader(self): #for whatever reason this reads but however it doesnt get the first two characters
        while self.pipeState != "clear":
            await asyncio.sleep(0.01)
        self.pipeState = "inUse"
        print("Starting read")
        pipeReadComplete=False #stays false until the read is complete in case the pipe broke mid read or something
        while !pipeReadComplete: #retrys the read until its completed successful
            reader = pipeReader(self.pipe) 
            reader.start()
            while reader.reader == None:
                await asyncio.sleep(0.01)
            resp = reader.reader
            while reader.is_alive():
                await asyncio.sleep(0.01)
            reader.join()
            if resp == "PipeFailedTryAgain":
                print("[Pipe Reader] Ouch Something Closed The Pipe. Please Reload..")
            else:
                pipeReadComplete=True
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
        try:
            self.thread = threading.Thread(name='pipeWriter',target=self.write, args=[self.pipe, data])
            self.thread.start()
            while self.thread.is_alive():
                await asyncio.sleep(0.01)
            print("YAYYY")
        except:
            print("error...")
            pass
        self.pipeState = "clear"
    
    def write(self,pipe,data):
        print("writing")
        pipe.write(data.encode('utf-16-le').strip(codecs.BOM_UTF16)) #this can probably be removed as byte order doesnt seem to be a thing when using -le or -be
        pipe.seek(0)
        print("written")

    def start(self):
        self.loop.run_forever()

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
                print("[Pipe Reader] Ouch Something Closed The Pipe. Please Reload..")