import shutil
import json
import os
import subprocess
import sys
#comment these two lines if you don't want to queue.
from rq import Connection, Queue
from redis import Redis
#Hello, World
#E.D.C.O.M EDCOM rocks and we love them!
preset="slow"
ac3=0
aac=0
vid=0

aacstr=0
ac3str=0
vidstr=0

filesto=[]
fil=sys.argv[1]

print(fil)

# Run FFProbe to get all of the available streams for any given file.
out=json.loads(subprocess.Popen(["/usr/bin/ffprobe","-v", "quiet", "-print_format", "json", "-show_format", "-show_streams",fil], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0])["streams"]
print(out) # Print that
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
			ffmpeg.append("20") #adjust this up/down depending on your percieved quality. 
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


#res=subprocess.call(["ffmpeg","-i",job["path"]]+job["opts"]+["out.mp4"])
#if res != 0:
#	print "FFMPEG WENT BAD!"
#else:
#	shutil.move("out.mp4",job["path"]+".mp4")
#	shutil.remove(job["path"])
# exit()

#Delete the rest of the file if you don't want to enqueue.

# enqueue the file.
redis_conn = Redis()
if video==0 and audio==0:
	if fil[-4:]!=".mp4":
		q = Queue('mux-core',connection=redis_conn)
		job["opts"]=["-acodec","copy","-vcodec","copy"]
		q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
		print('Enqueued: '+ fil+" for Remux"+str(job))

if video==1:
	q = Queue('video-core',connection=redis_conn)
	q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
	print('Enqueued: '+ fil+" for Video"+str(job))
elif audio!=0:
	q = Queue('audio-core',connection=redis_conn)
	q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
	print('Enqueued: '+ fil+" for Audio"+str(job))
