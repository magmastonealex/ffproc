import shutil
import json
import os
import subprocess
import sys
import re
import fnmatch
import time
import math

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

# USAGE
# python2 ~/ffproc/ffproc.py /PATH/TO/MEDIA/FILE.MP4
#   OR
# find /your/media/from/root -exec python2 ~/ffproc/ffproc.py {} \;

# uncomment these two lines if you want to queue.
#from rq import Connection, Queue
#from redis import Redis
preset="slow"
#adjust this depending on your percieved quality. 0=lossless, 18=Visually Lossless, 23=default, 51=worst possible. The range is exponential, so increasing the CRF value +6 is roughly half the bitrate while -6 is roughly twice the bitrate
crf="22"
ac3=0
aac=0
vid=0

aacstr=0
ac3str=0
vidstr=0

filesto=[]
fil=sys.argv[1]

print "#################################################################"
print(fil)
print

# Run FFProbe to get all of the available streams for any given file.
out=json.loads(subprocess.Popen(["ffprobe","-v", "quiet", "-print_format", "json", "-show_format", "-show_streams",fil], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0])["streams"]
#print(out) # Print that
streams_audio=[]

#A counter to see how "good" the file is. If it's 3, then we don't need to do anything to the file.
good=0
streams_final=[]
subs_streams=[]
for stream in out:
	curstream={}
	if stream['codec_type']=='audio':
		if stream["codec_name"]=="ac3" or stream["codec_name"]=="dts" or stream["codec_name"]=="dca": # check for high quality/special codecs.
#																										This check is more complicated than it needs to be because some DVDs are really, really strange.
			curstream["type"]="audio"
			curstream["codec"]=stream["codec_name"]
			curstream["index"]=stream["index"]
			if "channel_layout" not in list(stream.keys()):
				stream["channel_layout"]="stereo"
			curstream["channel_layout"]=stream["channel_layout"]
			if stream["channels"] >= 5:
				curstream["channel_layout"]="surround"
				curstream["newcodec"]="copy"
				good=good+1
			else:
				curstream["channel_layout"]="stereo"
				curstream["newcodec"]="copy"
				good=good+1
		elif stream["codec_name"]=="aac":
			curstream["type"]="audio"
			curstream["codec"]=stream["codec_name"]
			curstream["index"]=stream["index"]
			curstream["channel_layout"]=stream["channel_layout"]
			if stream["channels"] == 6: # Surround AAC is strange, but oddly common in the warez scene.
				curstream["channel_layout"]="surround"
				curstream["newcodec"]="aac"
				curstream["channels"]="2"
			else:
				curstream["newcodec"]="copy"
				good=good+1
		else:
			curstream["type"]="audio"
			curstream["index"]=stream["index"]
			curstream["newcodec"]="aac"
			curstream["codec"]=stream["codec_name"]
			curstream["channel_layout"]=stream["channels"]
		streams_audio.append(curstream)
	elif stream["codec_type"]=="video": # Don't care unless it's already h.264.
		curstream["type"]="video"
		curstream["index"]=stream['index']
		if stream['codec_name']=="h264":
			curstream["newcodec"]= "copy"
			good=good+1
		else:
			curstream["newcodec"]="h264"
		streams_final.append(curstream)
	elif stream["codec_type"]=="subtitle":
		subs_streams.append(stream["index"])
if good==3:
	print "Conversion not needed."
	print "'", fil, "' is Chromecast compatible."
	print
	sys.exit(0)


# Potential for increasing if multi-streamed audio becomes prevalent. (DVDs/Blu-Ray)
aacStreams = [x for x in streams_audio if x["codec"] == "aac"]
ac3Streams = [x for x in streams_audio if x["codec"] == "ac3"]

if len(ac3Streams) == 0:
	ac3Streams = [x for x in streams_audio if x["codec"] == "dts"] # prefer AC3, otherwise do DTS/DCA. Most files will only have one.
if len(ac3Streams) == 0:
	ac3Streams = [x for x in streams_audio if x["codec"] == "dca"]

aac=0
ac3=0

if len(aacStreams)>0:
	aac=aacStreams[0]
if len(ac3Streams)>0:
	ac3=ac3Streams[0]
if len(ac3Streams)==0 or (ac3["channel_layout"]=="stereo" and aac!=0):
	#no AC3 stream. See if we can convert that strange surround AAC to AC3.
	try:
		if aac["channel_layout"] == "surround":
			newstr={}
			newstr["newcodec"]="ac3"
			newstr["channels"]="6"
			newstr["index"]=aac["index"]
			newstr["type"]="audio"
			newstr["codec"]="NewStream"
			ac3=newstr
	except:
		pass

if aac==0 and ac3==0:
	newstr={}
	newstr["newcodec"]="aac"
	newstr["channels"]="2"
	newstr["index"]=streams_audio[0]["index"]
	newstr["type"]="audio"
	newstr["codec"]="NewStream"
	aac=newstr

if aac==0:
	#no AAC stream. There must be an AC3 stream.
	newstr={}
	newstr["newcodec"]="aac"
	newstr["channels"]="2"
	newstr["index"]=ac3["index"]
	newstr["type"]="audio"
	newstr["codec"]="NewStream"
	aac=newstr



if aac != 0:
	streams_final.append(aac)
if ac3 !=0:
	streams_final.append(ac3)



#build an ffmpeg command.

numaudio=0
video=1
audio=0
ffmpeg=[]
for stream in streams_final:
	ffmpeg.append("-map")
	ffmpeg.append("0:"+str(stream["index"]))
	if stream["type"]=="video":
		if stream["newcodec"]=="copy":
			ffmpeg.append("-c:v")
			ffmpeg.append("copy")
			video=0
		elif stream["newcodec"]=="h264":
			ffmpeg.append("-c:v")
			ffmpeg.append("libx264")
			ffmpeg.append("-crf")
			ffmpeg.append(crf)
			ffmpeg.append("-level:v")
			ffmpeg.append("4.1")
			ffmpeg.append("-preset")
			ffmpeg.append(preset)
			ffmpeg.append("-bf") # these slow down encoding, but reduce file size pretty significantly.
			ffmpeg.append("16")
			ffmpeg.append("-b_strategy")
			ffmpeg.append("2")
			ffmpeg.append("-subq")
			ffmpeg.append("10")
		else: 
			print("Unknown codec:"+stream["newcodec"])
			sys.exit(1)
	elif stream["type"]=="audio":
		if stream["newcodec"]=="aac":
			ffmpeg.append("-c:a:"+str(numaudio))
			ffmpeg.append("libfdk_aac")
			ffmpeg.append("-ac:a:"+str(numaudio))
			ffmpeg.append("2")
			ffmpeg.append("-vbr")
			ffmpeg.append("5")
			#ffmpeg.append("-b:a:"+str(numaudio))
			#ffmpeg.append("320k")
			audio=1
			numaudio=numaudio+1
		elif stream["newcodec"]=="ac3":
			ffmpeg.append("-c:a:"+str(numaudio))
			ffmpeg.append("ac3")
			ffmpeg.append("-ac:a:"+str(numaudio))
			ffmpeg.append("6")
			ffmpeg.append("-b:a:"+str(numaudio))
			ffmpeg.append("640k")
			audio=1
			numaudio=numaudio+1
		elif stream["newcodec"]=="copy":
			ffmpeg.append("-c:a:"+str(numaudio))
			ffmpeg.append("copy")
			numaudio=numaudio+1
		else:
			print("Unknown codec:"+stream["newcodec"])
ffmpeg.append("-movflags")
ffmpeg.append("faststart")
ffmpeg.append("-hide_banner")

job={}
job["path"]=fil
job["opts"]=ffmpeg

head,tail=os.path.split(fil)

if fil[-4:]==".mpg" or fil[-4:]==".vob": # These are usually OTA  recordings or DVD rips, which are in 1080i. There isn't a good way to test this. 
	print("Deinterlacing!")
	ffmpeg.append("-vf")
	ffmpeg.append("yadif=0:-1:0")

if len(subs_streams) > 0:
	ffmpeg.append("-scodec")
	ffmpeg.append("mov_text")
	for stream in subs_streams:
		ffmpeg.append("-map")
		ffmpeg.append("0:"+str(stream))

#uncomment these next few lines if you want to just run ffmpeg.

# make temp file in home directory with a unique name
output=os.path.expanduser('~')+"/"+"ffmpeg.tmp."+time.strftime("%H.%M.")+os.path.splitext(tail)[0]+".mp4"

print "Starting ffmpeg with this command:"
print "ffmpeg -i", fil, " ".join(ffmpeg), output
print

# the time conversion starts
elapsed_time = time.time()

# start the ffmpeg conversion
try:
	res=subprocess.call(["ffmpeg","-i",job["path"]]+job["opts"]+[output])
except KeyboardInterrupt:
	# Ctrl-C was pressed
	sys.exit()

# the time conversion stops
elapsed_time = time.time() - elapsed_time

if res != 0:
	print "FFMPEG FAILURE!"
else:
	# replace xvid with x264 and the extention with mp4
	extension = os.path.splitext(job["path"])[1]
	pathout = re.sub("(?i)xvid","x264",job["path"])		
	pathout = re.sub(extension,".mp4",pathout)
	print "Moving '", output,"'", "to","'", pathout,"'"
	print

	# wait 3 seconds incase it needs to be canceled with Ctrl-C
	try:
		time.sleep(3)
	except KeyboardInterrupt:
		print " Canceling move" # Ctrl-C was pressed
		print
		sys.exit()
	
	# write files sizes to log
	log=os.path.expanduser('~')+"/"+"ffproc.log"
	f1=open(log, 'a+')
	print >> f1, ""
	print >> f1, "Before", sizeof_fmt(os.path.getsize(fil)), "|", os.path.basename(fil)

	# find how much HD space was saved or lost
	diff = os.path.getsize(fil)
	
	# move the temp file to the original location
	shutil.move(output,pathout)

	print >> f1, "After ", sizeof_fmt(os.path.getsize(pathout)), "|", os.path.basename(pathout)
		
	# print HD space to log
	diff = diff - os.path.getsize(pathout)
	if diff >= 0:
		print >> f1, sizeof_fmt(diff), "Saved and",
	else:
		absdiff=abs(diff)
		print >> f1, sizeof_fmt(absdiff), "Lost and",

	# find the total saved
	totalLog=os.path.expanduser('~')+"/"+".totalSavedFFPROC.log"
	if os.path.isfile(totalLog):
		# get the total saved so far
		f2=open(totalLog, 'r')
		total=int(f2.read())
		f2.close()
		# add this file's difference to the total
		f2=open(totalLog, 'w+')
		total=str(diff + total)
		f2.write(total)
		f2.close()
		# print that to the log
		if int(total) >= 0:
			print >> f1, sizeof_fmt(int(total)),"Saved All Together"
		else:
			print >> f1, sizeof_fmt(int(total)),"Lost All Together"
	else:
		# make this file's difference the total
		f2=open(totalLog, 'w+')
		f2.write(str(diff))
		f2.close()
		if diff > 0:
			print >> f1, sizeof_fmt(diff),"Saved All Together"
		else:
			print >> f1, sizeof_fmt(diff),"Lost All Together"

	# find how much time elapsed
	if elapsed_time >= 3600:
		hours, minutes = divmod(elapsed_time, 3600)
		minutes, seconds = divmod(minutes, 60)
		elapsed_time =  math.trunc(hours), "h ", math.trunc(minutes), "m ", math.trunc(round(seconds)), "s"
	else:
		minutes, seconds = divmod(elapsed_time, 60)
		elapsed_time = math.trunc(minutes), "m ", math.trunc(round(seconds)), "s"

	# print time elapsed to log
	print >> f1, ''.join(str(x) for x in elapsed_time), "elapsed"

	f1.close()
	
	# delete old file if new name and old name are different
	if fnmatch.fnmatchcase(job["path"],pathout)==False:
		print "Deleting '",job["path"],"'"
		print
		os.remove(job["path"])
exit()

#Delete the rest of the file if you don't want to enqueue.

# enqueue the file.
#redis_conn = Redis()
#if video==0 and audio==0:
#	if fil[-4:]!=".mp4":
#		q = Queue('mux-core',connection=redis_conn)
#		job["opts"]=["-acodec","copy","-vcodec","copy"]
#		q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
#		print('Enqueued: '+ fil+" for Remux"+str(job))
#
#if video==1:
#	q = Queue('video-core',connection=redis_conn)
#	q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
#	print('Enqueued: '+ fil+" for Video"+str(job))
#elif audio!=0:
#	q = Queue('audio-core',connection=redis_conn)
#	q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
#	print('Enqueued: '+ fil+" for Audio"+str(job))
