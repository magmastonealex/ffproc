from parser import Parser
from util import Log

#Pass in a Parser object.
# This function will take that and turn it into an array of stream objects which can then be turned into an ffmpeg command.

"""
	Options is the dictionary that determines *how* the parser is transformed.
	It contains a series of qualities, with their settings, and one master object which maps files to qualities using regexes.
	Qualities describe a file target.
	First params are defaults.

	default:
		video:
			- codec: h264/hevc - the codec to use
			- res: keep/720p/1080p/480p - the resolution to scale down to, if needed. if the video is around this, it won't be scaled to exact dimens.
			- deinterlace yes/no/force - Deinterlace if ffproc thinks that it's interlaced, or force it to. 
			- quality: 20 - the quality setting to use
			- force: yes/no
		audio:
			surround:
				- keep: yes/no - Keep the surround channel 
				- codec: ac3/dts/aac - Codec to use for surround format.
				- bitrate 640k - don't go above this bitrate
			stereo:
				- keep: yes/no - Keep the stereo channel
				- create: yes - Create from surround
				- ffproc_filtering - Use ffproc's filtergraph to make better stereo (less background noise, nightmode style filter to normalize volume.)
				- codec aac/mp3
				- bitrate 128k - don't go above this bitrate
				- force_libfdk yes/no allow or disallow  
		subtitles:
			- keep yes/no - yes will require the external utilities to be installed for some files.
			- inline yes/no - (personal preference) inline subtitles after flattening.
			- codec srt - When extracting, use this format
		output:
			- filetype mkv/mp4 - What output file format to use
			- quickstart yes/no - Run a postprocessing step to enable mp4 quickstart.
"""

"""
	Returns an object containing pre,transcode,post subobjects.
	pre:
		- subtitles:  [idx,codec,lang] to extract. Lang may have .forced appended to it for FD subs.
	transcode:
		- { video, index, codec, quality, scaleopts, deinterlacing}
		- { audio, index, codec, bitrate, downconvert, customdownconvert}

	Pre is run first, serverside to extract subtitles and do other preprocessing work
	transcode is used to build an ffmpeg command line
"""

def transform(parser, options):


	# Start with the video.
	# We're going to check the parser video_stream and compare it to our target.
	cstream = parser.video_stream
	voptions = options["video"]

	codec = "copy"
	if cstream["codec"] != voptions["codec"] or voptions["force"] == True:
		codec = voptions["codec"]

	deinterlace = False
	if (parser.is_interlaced and voptions["deinterlace"] == "yes") or voptions["deinterlace"] == "forced":
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
			scaleopts = dres

	video_build = {"index":cstream["index"], "codec": codec, "quality": voptions["quality"], "deinterlacing": deinterlace, "scaling": scaleopts}

	#Now the hard part. Figuring out the mess of audio streams
	#Find the master track. This is the highest bitrate, highest number of channels stream, which is also in the right language.
	