"""
	This is the script to invoke across all of your media.

	It will invoke a parser on the media, then parse the config file using regex if applicable to select a transcode profile, which is then passed to a transformer to turn it into Tasks, if applicable.

	The Tasks are then enqueued into Redis.

	There is a separate Python module that handles running these tasks out of the queue.


	Long-term cool things to do: The receiver for FFmpeg progress URL is implemented, but we need to write a web interface or something for it to mean anything. 

"""

import argparse
from rq import Connection, Queue
from redis import Redis
import json
import transformer
import sys
import os

from parser import Parser
from task import Task, TaskTypes

redis_conn = Redis("10.154.60.11")

#TODO: use argparse here
startfilename = sys.argv[1]
endfilename = ".".join(sys.argv[1].split(".")[:-1])+".mp4"

fileparsed = Parser(startfilename)

thistask = transformer.ffmpeg_tasks_create(fileparsed,transformer.defaultoptions)
if thistask != None:
	thistask.infile = startfilename
	thistask.outfile = endfilename
	print "Enqueing " + os.path.basename(startfilename) + " for " + thistask.tasktype
	q = Queue(thistask.tasktype,connection=redis_conn)
	q.enqueue_call("worker.ffmpeg", args=(str(thistask),),timeout=360000)
else:
	print "No action needed for " + os.path.basename(startfilename)