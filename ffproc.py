"""
	This is the script to invoke across all of your media.


	N.B: Regexes are parsed in decending order. IE, the first match wins. So your regexes should be from least to most specific.
	It will invoke a parser on the media, then parse the config files using regex if applicable to select a transcode profile, which is then passed to a transformer to turn it into Tasks, if applicable.

	The Tasks are then enqueued into Redis.

	There is a separate Python module that handles running these tasks out of the queue.


	Long-term cool things to do: The receiver for FFmpeg progress URL is implemented, but we need to write a web interface or something for it to mean anything. 

"""

import argparse

import json
import transformer
import sys
import os
import json
import re
from util import Log

from parser import Parser
from task import Task, TaskTypes

TAG = "ffproc"

useredis = True

try:
	from rq import Connection, Queue
	from redis import Redis
except:
	useredis = False
	Log.e(TAG, "rq and redis libraries not found. Disabling redis support...")



parser = argparse.ArgumentParser(description='Enqueue media files for transcoding, using a variety of profiles.')
parser.add_argument('--profile', help='Force a particular profile')
parser.add_argument('--immediate', action='store_true',help="Don't use Redis, just run the transcode immediately")
parser.add_argument('--redis', default="127.0.0.1",nargs=1,type=str,help="Redis IP address, if not localhost")
parser.add_argument('--showcommand', action='store_true',help='(debug) Show the FFMPEG command used')
parser.add_argument('--dryrun', action='store_true',help='(debug) Stop short of actually enqueing the file')

parser.add_argument('file', metavar='file', type=str,
                    help='The file to transcode')
arguments = parser.parse_args()

if arguments.immediate == True:
	useredis = False

allprofiles = json.loads(open("profiles.json").read())


startfilename = arguments.file
endfilename = ".".join(arguments.file.split(".")[:-1])+".mp4"

fileparsed = Parser(startfilename)



profile = arguments.profile
basefilename = os.path.basename(arguments.file)



if profile == None:
	regexes = json.loads(open("regexes.json").read())
	for regex in regexes:
		if re.match(regex["regex"], basefilename) != None:
			profile = regex["profile"]
			Log.v(TAG, "Got profile " + profile + " for " + basefilename)

if profile == None:
	#No regex matched either!
	profile = "default"


if profile not in allprofiles:
	Log.e(TAG, "Profile " + profile+" does not exist!")
	sys.exit()

discoveredprofile = allprofiles[profile]
#TODO: use argparse here


thistask = transformer.ffmpeg_tasks_create(fileparsed,discoveredprofile)
if thistask != None:
	thistask.infile = startfilename
	thistask.outfile = endfilename
	thistask.forcefdk = discoveredprofile["audio"]["stereo"]["force_libfdk"]
	Log.i(TAG, "Enqueing " + os.path.basename(startfilename) + " for " + thistask.tasktype)
	if arguments.showcommand == True:
		Log.v(TAG, "ffmpeg command: " + " ".join(thistask.arguments))
	if arguments.dryrun == False and useredis == True:
		redaddr = arguments.redis
		if isinstance(redaddr, list):
			redaddr = arguments.redis[0]
		q = Queue(thistask.tasktype, connection=Redis(redaddr))
		q.enqueue_call("worker.ffmpeg", args=(str(thistask),),timeout=360000)
	else:
		if arguments.dryrun == True:
			Log.e(TAG, "Did not enqueue as per command line options")
		else:
			Log.e(TAG, "Running ffmpeg locally.")
			import worker
			worker.ffmpeg(str(thistask))
else:
	Log.i(TAG, "No action needed for " + os.path.basename(startfilename))