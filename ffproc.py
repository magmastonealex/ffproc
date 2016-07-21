import shutil
import json
import os
import subprocess
import uuid
import sys
preset="veryslow"
ac3=0
aac=0
vid=0

aacstr=0
ac3str=0
vidstr=0

filesto=[]
fil=sys.argv[1]

#print "---"
print fil
#sys.exit(0)

out=json.loads(subprocess.Popen(["/usr/bin/ffprobe","-v", "quiet", "-print_format", "json", "-show_format", "-show_streams",fil], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0])["streams"]
print out
streams_audio=[]
#print fil
#exit()
good=0
streams_final=[]
subs_streams=[]
subs_fd = []

for stream in out:
	curstream={}
	if stream['codec_type']=='audio':
		print stream["codec_name"]
		if stream["codec_name"]=="ac3" or stream["codec_name"]=="dts" or stream["codec_name"]=="dca":
			print "special"
			curstream["type"]="audio"
			curstream["codec"]=stream["codec_name"]
			curstream["index"]=stream["index"]
			curstream["channel_layout"]=stream["channel_layout"]
			print stream
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
			if stream["channels"] == 6:
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
	elif stream["codec_type"]=="video":
		
		curstream["type"]="video"
		curstream["index"]=stream['index']
		if stream['codec_name']=="mjpeg":
			continue
		elif stream['codec_name']=="h264":
			curstream["newcodec"]= "copy"
			good=good+1
		else:
			curstream["newcodec"]="h264"
		streams_final.append(curstream)
	elif stream["codec_type"]=="subtitle":
		lang=""
		try:
			lang=stream["tags"]["LANGUAGE"]
		except:
			try:
				lang=stream["tags"]["language"]
			except:
				try:
					check = stream["tags"]["title"]
					if check.lower().find("eng") > -1:
						lang="eng"
				except:
					continue
		if lang=="eng":
			try:
				#print stream["tags"]["title"]
				if stream["tags"]["title"]=="Foriegn Dialog" or stream["tags"]["title"]=="F.D." or stream["tags"]["title"]=="FORCED":
					subs_fd.append([stream['index'],stream["codec_name"] ])
				else:
					subs_streams.append([stream['index'],stream["codec_name"] ])
			except:
				print "Adding as regular stream"
				subs_streams.append([stream['index'],stream["codec_name"] ])

if good==3:
	#print "All good."
	sys.exit(0)
#print streams_audio

# Potential for increasing if multi-streamed audio becomes prevalent. (DVDs/Blu-Ray)
aacStreams = [x for x in streams_audio if x["codec"] == "aac"]
ac3Streams = [x for x in streams_audio if x["codec"] == "ac3"]

if len(ac3Streams) == 0:
	ac3Streams = [x for x in streams_audio if x["codec"] == "dts"]
if len(ac3Streams) == 0:
	ac3Streams = [x for x in streams_audio if x["codec"] == "dca"]

aac=0
ac3=0
#print fil
if len(aacStreams)>0:
	aac=aacStreams[0]
if len(ac3Streams)>0:
	ac3=ac3Streams[0]
if len(ac3Streams)==0 or (ac3["channel_layout"]=="stereo" and aac!=0):
	#no AC3 stream. Can we do something?
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



#print streams_final
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
#			if fil.find("Brooklyn") != -1 or fil.find("Saturday") != -1 or fil.find("Gotham") != -1 or fil.find("Amazing") != -1:
#				print "Scaling!"
#				ffmpeg.append("-vf")
#				ffmpeg.append("scale=-1:720")
			ffmpeg.append("-c:v")
			ffmpeg.append("libx264")
			if fil.find("Amazing") != -1 or fil.find("Survivor") != -1 or fil.find("Colbert") != -1 or fil.find("Trevor") != -1 or fil.find("Saturday") != -1:
				print fil
				print "22"
				ffmpeg.append("-crf")
				ffmpeg.append("23")
			else:
				ffmpeg.append("-crf")
				ffmpeg.append("20")
			ffmpeg.append("-level:v")
			ffmpeg.append("4.1")
			ffmpeg.append("-preset")
			ffmpeg.append(preset)
			ffmpeg.append("-bf")
			ffmpeg.append("16")
			ffmpeg.append("-b_strategy")
			ffmpeg.append("2")
			ffmpeg.append("-subq")
			ffmpeg.append("10")
		else: 
			print "Unknown codec:"+stream["newcodec"]
			sys.exit(1)
	elif stream["type"]=="audio":
		if stream["newcodec"]=="aac":
			ffmpeg.append("-c:a:"+str(numaudio))
			ffmpeg.append("libfdk_aac")
			ffmpeg.append("-ac:a:"+str(numaudio))
			ffmpeg.append("2")
#			ffmpeg.append("-vbr")
#			ffmpeg.append("5")
			ffmpeg.append("-metadata:s:a:"+str(numaudio))
			ffmpeg.append("lang=eng")
			ffmpeg.append("-b:a:"+str(numaudio))
			ffmpeg.append("128k")
			audio=1
			numaudio=numaudio+1
		elif stream["newcodec"]=="ac3":
			ffmpeg.append("-c:a:"+str(numaudio))
			ffmpeg.append("ac3")
			ffmpeg.append("-ac:a:"+str(numaudio))
			ffmpeg.append("6")
			ffmpeg.append("-b:a:"+str(numaudio))
			ffmpeg.append("640k")
			ffmpeg.append("-metadata:s:a:"+str(numaudio))
			ffmpeg.append("lang=eng")
			audio=1
			numaudio=numaudio+1
		elif stream["newcodec"]=="copy":
			ffmpeg.append("-c:a:"+str(numaudio))
			ffmpeg.append("copy")
			ffmpeg.append("-metadata:s:a:"+str(numaudio))
			ffmpeg.append("lang=eng")
			numaudio=numaudio+1
		else:
			print "Unknown codec:"+stream["newcodec"]
#if len(subs_streams) > 0:
#	ffmpeg.append("-scodec")
#	ffmpeg.append("mov_text")
#	for stream in subs_streams:
#		ffmpeg.append("-map")
#		ffmpeg.append("0:"+str(stream))

ffmpeg.append("-movflags")
ffmpeg.append("faststart")
ffmpeg.append("-map_metadata")
ffmpeg.append("-1")

ffmpeg.append("-refs")
ffmpeg.append("4")

print subs_streams
print subs_fd
print ffmpeg

def filenameFromType(type):
	print type
	if type == "srt":
		return "/bin/subs/extractsrt.sh"
	elif type == "pgssub":
		return "/bin/subs/tosrt.sh"
	elif type == "ass" or type == "ssa":
		return "/bin/subs/ssa-to-srt.sh"
	elif type == "vobsub" or type == "dvdsub":
		return "/bin/subs/tosrt_vobsub.sh"

if len(subs_fd)>0:
	#we know the FD sub track, and the proper full subs:
	subprocess.call([filenameFromType(subs_fd[0][1]),fil,str(subs_fd[0][0]),"eng.forced",str(uuid.uuid4())])
	subprocess.call([filenameFromType(subs_streams[0][1]),fil,str(subs_streams[0][0]),"eng",str(uuid.uuid4())])
else:
	if len(subs_streams) > 0:
		subprocess.call([filenameFromType(subs_streams[0][1]),fil,str(subs_streams[0][0]),"eng",str(uuid.uuid4())])

#sys.exit()

job={}
job["path"]=fil
job["opts"]=ffmpeg

sb=subprocess.Popen(["/usr/bin/frames",fil], stdout=subprocess.PIPE)
job["frames"]=int(sb.communicate()[0])

from rq import Connection, Queue
from redis import Redis

redis_conn = Redis()

head,tail=os.path.split(fil)
redis_conn.set("transtat:"+tail, 0)

if fil[-4:]==".mpg":
	print "Deinterlacing!"
	ffmpeg.append("-vf")
	if fil.find("Colbert") != -1 or fil.find("Saturday") != -1 or fil.find("Gotham") != -1 or fil.find("Amazing") != -1 or fil.find("Trevor") != -1 or fil.find("Survivor") != -1 or fil.find("Agents") != -1 or fil.find("Bang") != -1 or fil.find("Mercer") != -1:
		ffmpeg.append("yadif=0:-1:0,scale=-1:720")
		ffmpeg.append("-sws_flags")
		ffmpeg.append("lanczos")
		ffmpeg.append("-refs")
		ffmpeg.append("9")
	else:
		ffmpeg.append("yadif=0:-1:0")
		ffmpeg.append("-refs")
		ffmpeg.append("4")
print " ".join(ffmpeg)

#exit()
#sb=subprocess.Popen(["/usr/bin/frames",fil], stdout=subprocess.PIPE)
#print int(sb.communicate()[0])
if video==0 and audio==0:
	if fil[-4:]!=".mp4":
		q = Queue('mux-core',connection=redis_conn)
		job["opts"]=["-acodec","copy","-vcodec","copy"]
		q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
		print 'Enqueued: '+ fil+" for Remux"+str(job)		

if video==1:
	q = Queue('video-core',connection=redis_conn)
	q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
	print 'Enqueued: '+ fil+" for Video"+str(job)
elif audio!=0:
	q = Queue('audio-core',connection=redis_conn)
	q.enqueue_call('tasks.ffmpeg',args=(job,),timeout=360000)
	print 'Enqueued: '+ fil+" for Audio"+str(job)
