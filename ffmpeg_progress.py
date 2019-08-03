"""
Receives progress from ffmpeg, and adds to Redis for the provided job ID.

Redis format:
    tcode:jobid:progress:out_time
    tcode:jobid:progress:fps
    tcode:jobid:progress:speed
"""

import socket
import threading
from ffdb import DB

class FFMpegReceiver(object):
    def __init__(self, port, tdb):
        self.port = port
        self.tdb = tdb
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            print "accepting"
            client.settimeout(60)
            threading.Thread(target = self.listenToFFmpeg,args = (client,address)).start()

    def listenToFFmpeg(self, client, address):
        bstring = " "
        found = False
        while found == False:
            bstring = bstring + client.recv(1)
            found = bstring.find("progress=continue") != -1
        jid = bstring.split("\n")[0].split("/")[1].split(" ")[0]

        while True:
            found = False
            bstring = ""
            while found == False:
                bstring = bstring + client.recv(1)
                found = bstring.find("progress=continue") != -1
            #print bstring
            data=bstring.split("\n")
            dataDict={}
            for d in data:
                d.rstrip()
                if d.find("=") != -1:
                    kv = d.split("=")
                    dataDict[kv[0].strip()]=kv[1].strip()
            #print dataDict
            self.tdb.put("tcode:"+jid+":progress:out_time",dataDict["out_time_ms"])
            self.tdb.put("tcode:"+jid+":progress:fps",dataDict["fps"])
            self.tdb.put("tcode:"+jid+":progress:speed",dataDict["speed"])
        client.close()
