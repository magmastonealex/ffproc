from MediaParser import Parser
from util import Log
from task import Task,TaskTypes

# Transformer is the class that has the pretty difficult task of turning what the file *is* into what the file *should be*. This is fairly easy for video, but audio has complications, i.e. what if the source has surround but no stereo? What if stereo and surround, do you want to ovewrite the stereo sound? Note that language detection isn't done right now.


"""
	Options is the dictionary that determines *how* the parser is transformed.
	Qualities describe a file target.
	video:
		- ignore: true - Just copy, we don't care about it.
		- codec: h264/hevc - the codec to use
		- allowhvec: true/false - Don't bother transcoding hevc.
		- 10bit - Use 10 bit video encoding (helps color banding, only reccomended with x265)
		- res: keep/720p/1080p/480p - the resolution to scale down to, if needed. if the video is around this, it won't be scaled to exact dimens.
		- deinterlace true/false/force - Deinterlace if ffproc thinks that it's interlaced, or force it to. 
		- quality: 20 - the crf quality setting to use
		- force: true/false - Force the video to be transcoded, even if it's already in the right codec.
		- encodepreset: veryslow/slow/fast/ultrafast - ffmpeg speed settings. Slower = equivalent quality, smaller file sizes.
	audio:
		surround:
			- keep: true/false - Keep the surround channel
		stereo:
			- keep: true/false - Keep the stereo channel that's already there
			- create: yes - Create from surround
			- ffproc_filtering - Use ffproc's filtergraph to make better stereo (less "background" noise, nightmode style filter to normalize volume for better listening with headphones or stereo speakers)
			- bitrate 128k - don't go above this bitrate
			- force_libfdk true/false - If this is false, the worker will change the libfdk_aac codec to aac if it does not have libfdk_aac installed. Will result in low-quality audio.  
		lang:
			- ignore: true/false - Ignore language tags, just take the best audio track available (this may result in weird behaviour if you have descriptive audio)
			- allowed: array - Allowed languages. Ignore all other audio tracks.
	output: (currently unused!)
		- filetype matroska/mp4 - What output file format to use
		- quickstart true/false - Run a postprocessing step to enable mp4 quickstart.
"""

"""
	


	Returns an array of transcode targets of the form:
		- { type:video, index, codec, quality, scaling, deinterlacing}
		- { type:audio, index, codec, bitrate, downconvert, customdownconvert}
	These transcode targets can then be used to create an ffmpeg command line.
"""

defaultoptions = { "video":{"deinterlace": "yes", "allowhevc": True, "ignore":False, "codec": "h264","force":False, "encodepreset": "veryslow", "quality": "20", "res":"1080p"}, "audio":{"surround":{"keep":True},"stereo":{"keep": True,"create": True,"ffproc_filtering":True,"bitrate":"128k","force_libfdk":True}}, "format":{"filetype":"mp4"} }
TAG = "MediaTransformer"
def media_transform(parser, options):

	#keep track if we do anything other than copying
	tcodeVideo=False
	tcodeAudio=False
	# Start with the video.
	# We're going to check the parser video_stream and compare it to our target.
	cstream = parser.video_stream
	voptions = options["video"]

	codec = "copy"
	if cstream["codec"] != voptions["codec"] or voptions["force"] == True:
		if voptions["allowhevc"] == True and cstream["codec"] == "hevc":
			Log.i(TAG, "Skipping transcode for HVEC as per override.")
		else:
			tcodeVideo = True
			Log.i(TAG, "Transcoding video track")
			codec = voptions["codec"]
	else:
		Log.i(TAG, "Copying video track")

	deinterlace = False
	if (parser.is_interlaced and voptions["deinterlace"] == "yes") or voptions["deinterlace"] == "forced":
		Log.i(TAG, "Deinterlacing video track (will cause transcode!)")
		tcodeVideo=True
		codec = voptions["codec"]
		deinterlace = True

	scaleopts = False

	if voptions["res"] != "keep":
		dres = 0
		if voptions["res"] == "1080p":
			dres = 1080
		elif voptions["res"] == "720p":
			dres = 720
		elif voptions["res"] == "480p":
			dres = 480

		if(cstream["height"] < dres):
			scaleopts = False
		elif(abs(cstream["height"] - dres) < 30):
			scaleopts = False
		else:
			Log.i(TAG, "Scaling video (will cause transcode!)")
			codec = voptions["codec"]
			scaleopts = dres
        bit10 = False
        if "10bit" in voptions:
            bit10 = voptions["10bit"]
        video_build = {"type":"video", "index":cstream["index"], "codec": codec, "quality": voptions["quality"], "deinterlacing": deinterlace, "scaleopts": scaleopts, "10bit": bit10}
	if options["video"]["ignore"] == True:
		Log.w(TAG, "Ignoring incorrect video codec")
		video_build = {"type":"video", "index":cstream["index"], "codec": "copy", "quality": "10", "deinterlacing": False, "scaleopts": False}

	aoptions = options["audio"]

	audio_building=[]

	surround_exists = False
	stereo_exists = False
	#Now the hard part. Figuring out the mess of audio streams
	#Find the master track. This is the highest bitrate, highest number of channels stream, which is also in the right language.
	audio_master = {"channels": 0, 'language':'und'}
	audio_stereo = None

	ignore_language = False
	valid_laguages = ["eng"]

	if "lang" in aoptions:
		if "ignore" in aoptions["lang"] and aoptions["lang"]["ignore"] == True:
			ignore_language = True
		if "allowed" in aoptions["lang"]:
			valid_languages = aoptions["lang"]["allowed"]
	
	#this feels naieve. Take a closer look at this!
	for track in parser.audio_streams:

		if ignore_language or ( track["language"] in valid_languages or track["language"] == "und" or track["language"] == None):
			if track["channels"] > audio_master["channels"]:
				audio_master = track
			if track["channels"] < 6:
				audio_stereo = track
				stereo_exists = True
	if audio_master["channels"] > 2:
		surround_exists = True

	#Add our audio channels.
	#Use the existing surround track
	if surround_exists and aoptions["surround"]["keep"] == True:
		audio_building.append({"type":"audio","index":audio_master["index"], "codec": "copy","ffprocdown":False,"downconvert":False})
		Log.i(TAG, "Copying surround audio")

	#Use our existing stereo track.
	if stereo_exists and aoptions["stereo"]["keep"] == True:
		if "aac" == audio_stereo["codec"]:
			Log.i(TAG, "Copying stereo audio")
			audio_building.append({"type":"audio","index":audio_stereo["index"], "codec": "copy","ffprocdown":False,"downconvert":False})
		else:
			tcodeAudio = True
			Log.i(TAG, "Transcoding existing stereo audio")
			audio_building.append({"type":"audio","index":audio_stereo["index"], "codec": "aac", "bitrate": aoptions["stereo"]["bitrate"],"downconvert":False, "forcefdk":aoptions["stereo"]["force_libfdk"],"ffprocdown":False})

	#Create from surround.
	if surround_exists and (not stereo_exists or aoptions["stereo"]["keep"] == False) and aoptions["stereo"]["create"] == True:
		Log.i(TAG, "Downmixing surround to stereo")
		tcodeAudio = True
		audio_building.append({"type":"audio","index":audio_master["index"], "codec": "aac", "bitrate": aoptions["stereo"]["bitrate"],"downconvert":True, "forcefdk":aoptions["stereo"]["force_libfdk"],"ffprocdown":aoptions["stereo"]["ffproc_filtering"]})
	
	#Are we doing any transcoding?
	tcode = tcodeVideo or tcodeAudio

	remux = False
	if not tcode and parser.file_format.find(options["format"]["filetype"]) == -1:
		remux = True

	audio_building.append(video_build)
	return {"video": tcodeVideo, "audio": tcodeAudio, "remux": remux, "tcodeData":audio_building}

# Returns a Task object that has been mostly populated - infile and outfile still needed.
def ffmpeg_tasks_create(parser, options):
	streams = media_transform(parser,options)
	if streams["video"]==False and streams["audio"]==False and streams["remux"]==False:
		return None
	ffmpeg=[]
	astreamindex = 0
	for stream in streams["tcodeData"][::-1]:
		
		#Map the stream into the output. Order will be video, stereo, surround based on media_transform function, and iterating the list backwards.
		
		#Note that if we're using custom downconverting, then we can't map the regular channel - we need to build a filtergraph.
		if stream["type"] == "audio" and stream["ffprocdown"] == True:
				ffmpeg.append("-filter_complex")
				ffmpeg.append("[0:"+str(stream["index"])+"]pan=stereo| FL < FL + 0.7*FC + 0.3*BL + 0.3*SL | FR < FR + 0.7*FC + 0.3*BR + 0.3*SR, dynaudnorm[a]")
				ffmpeg.append("-map")
				ffmpeg.append("[a]")
		else:
			ffmpeg.append("-map")
			ffmpeg.append("0:"+str(stream["index"]))

		if stream["type"] == "video":
			ffmpeg.append("-c:v")
			codec_to_ffmpeg = stream["codec"]
			if codec_to_ffmpeg == "copy":
				ffmpeg.append("copy")
			elif codec_to_ffmpeg == "h264":
				#Behold, the insane list of arguments needed to tune h.264 for decent compression even 
				ffmpeg.append("libx264")
				ffmpeg.append("-crf")
				ffmpeg.append(options["video"]["quality"])
				ffmpeg.append("-level:v")
				ffmpeg.append("4.1")
				ffmpeg.append("-preset")
				ffmpeg.append(options["video"]["encodepreset"])
				ffmpeg.append("-bf")
				ffmpeg.append("16")
				ffmpeg.append("-b_strategy")
				ffmpeg.append("2")
				ffmpeg.append("-subq")
				ffmpeg.append("10")
				ffmpeg.append("-refs")
				ffmpeg.append("4")
			elif codec_to_ffmpeg == "hevc":
				ffmpeg.append("libx265")
				ffmpeg.append("-crf")
				ffmpeg.append(options["video"]["quality"])
				ffmpeg.append("-preset")
				ffmpeg.append(options["video"]["encodepreset"])
				# fix for #16. Allows Apple devices to play hevc result files.
				ffmpeg.append("-tag:v")
				ffmpeg.append("hvc1")
			else:
				Log.e(TAG, "Unknown codec selected, you're on your own!")
				ffmpeg.append(stream["codec"])
                        if stream['10bit']:
                                ffmpeg.append("-pix_fmt")
                                ffmpeg.append("yuv420p10le")
			if stream["scaleopts"] != False and stream["deinterlacing"] == True:
				#Scaling and deinterlacing
				ffmpeg.append("-vf")
				ffmpeg.append("yadif=0:-1:0,scale=-1:"+str(stream["scaleopts"]))
				ffmpeg.append("-sws_flags")
				ffmpeg.append("lanczos")
			elif stream["scaleopts"] == False and stream["deinterlacing"] == True:
				#Just deinterlacing
				ffmpeg.append("-vf")
				ffmpeg.append("yadif=0:-1:0")
			elif stream["scaleopts"] != False and stream["deinterlacing"] == False:
				#Just scaling
				ffmpeg.append("-vf")
				ffmpeg.append("scale=-1:"+str(stream["scaleopts"]))
				ffmpeg.append("-sws_flags")
				ffmpeg.append("lanczos")
			else:
				#Nothing
				pass
		elif stream["type"] == "audio":
			ffmpeg.append("-c:a:"+str(astreamindex))
			codec_to_ffmpeg = stream["codec"]

			if codec_to_ffmpeg == "copy":
				ffmpeg.append("copy")
			elif codec_to_ffmpeg == "aac":
				ffmpeg.append("libfdk_aac")
				ffmpeg.append("-b:a:"+str(astreamindex))
				ffmpeg.append(stream["bitrate"])
			else:
				Log.e(TAG, "Unknown codec selected, you're on your own!")
				ffmpeg.append(stream["codec"])
			if stream["ffprocdown"] == False and stream["downconvert"] == True:
				#Use stock downconverting, not our own pan & dynaudnorm filter.
				ffmpeg.append("-ac:a:"+str(astreamindex))
				ffmpeg.append("2")
			astreamindex=astreamindex+1

	if options["format"]["filetype"] == "mp4":
		ffmpeg.append("-movflags")
		ffmpeg.append("+faststart")

	ffmpeg.append("-map_metadata")
	ffmpeg.append("-1")

	task_type = TaskTypes.REMUX

	if streams["video"] == True:
		task_type = TaskTypes.VIDEO
	elif streams["audio"] == True:
		task_type = TaskTypes.AUDIO

	return Task(tasktype=task_type, command="ffmpeg", arguments=ffmpeg)
