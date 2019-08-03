import json

class TaskTypes:
    SUBTITLE = "subs"
    VIDEO = "video"
    AUDIO = "audio"
    REMUX = "remux"
    NONE = "none"

#Tasks are capable of serializing, unserializing, and executing themselves. This allows the choice of where to execute them - on the server directly or as part of a cluster.


class Task:
    tasktype = None
    command = "echo"
    arguments = []
    forcefdk = False
    infile = ""
    outfile = ""

    def __init__(self,createfrom=None,tasktype=TaskTypes.NONE,command="echo",arguments=[],infile="",outfile="",forcefdk=False):
        if createfrom == None:
            self.tasktype = tasktype
            self.command = command
            self.arguments = arguments
            self.infile = infile
            self.outfile = outfile
            self.forcefdk = forcefdk
        else:
            obj = json.loads(createfrom)
            self.tasktype = obj["type"]
            self.command = obj["command"]
            self.arguments = obj["arguments"]
            self.infile = obj["infile"]
            self.forcefdk = obj["forcefdk"]
            self.outfile = obj["outfile"]
    def stringify(self):
        return json.dumps({"type":self.tasktype,"command":self.command,"arguments":self.arguments,"infile":self.infile,"outfile":self.outfile, "forcefdk":self.forcefdk})
    def __str__(self):
        return self.stringify()
