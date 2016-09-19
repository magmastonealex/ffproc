import subprocess
import json
from util import Log


"""
	The Parser has the kind-of-difficult job of figuring out what the file contains. It uses ffprobe to create a series of arrays which describe any given file. Transformers take objects of this type.
"""

TAG = "parser"

class Parser(object):
	ffprobe_dict = False
	video_stream = {}
	audio_streams = []
	sub_streams = []
	is_interlaced = False
	file_format=""
	duration = 0

	def __init__(self, filename):
		if(filename[0] != '/'):
			Log.w(TAG, "Filename is not absolute, this may cause issues dispatching jobs.")
		ffprobe = subprocess.Popen(["ffprobe","-v", "quiet", "-print_format", "json", "-show_format", "-show_streams",filename], stdout=subprocess.PIPE)
		#Get everything from stdout once ffprobe exits, and
		try:
			ffprobe_string = ffprobe.communicate()[0]
			self.ffprobe_dict=json.loads(ffprobe_string)
		except ValueError:
			Log.e(TAG, "File could not be read, are you sure it exists?")
		ffmpeg_interlace = subprocess.Popen(["ffmpeg", "-filter:v", "idet", "-frames:v", "400", "-an", "-f", "rawvideo", "-y", "/dev/null", "-i", filename],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		interlaced_details = ffmpeg_interlace.communicate()[1]
		interlaced_lines = interlaced_details.split("\n")
		num_progressive = 0
		for line in interlaced_lines:
			if line.find("idet") != -1 and line.find("Progressive") != -1:
				#find the number of progressive frames in this line.
				nframes = line.split("Progressive:")[1].split("Undetermined")[0]
				num_progressive = num_progressive + int(nframes)
		if num_progressive < 20:
			self.is_interlaced = True
		self.video_stream = self.parse_video(self.ffprobe_dict)
		self.audio_streams = self.parse_audio(self.ffprobe_dict)
		self.sub_streams = self.parse_subs(self.ffprobe_dict)
		self.file_format = self.ffprobe_dict["format"]["format_name"]
		self.duration = float(self.ffprobe_dict["format"]["duration"])

	#Parses ffprobe_dict to create the video_stream object. Let this be called by the constructor!
	def parse_video(self, ffprobe_dict):
		if ffprobe_dict == False:
			return

		foundVideo = False
		video_stream = {}
		for stream in ffprobe_dict["streams"]:
			if stream["codec_type"] == "video":
				if foundVideo:
					Log.w(TAG, "File had more than one video stream. Using the first one. This is unsupported!")
				foundVideo = True
				video_stream = {"index": stream["index"], "width": stream["width"], "height": stream["height"], "codec": stream["codec_name"] }
		return video_stream
	# Parses ffprobe_dict to create the audio_streams array. Don't call manually!
	def parse_audio(self, ffprobe_dict):
		if ffprobe_dict == False:
			return

		audio_streams = []

		for stream in ffprobe_dict["streams"]:
			if stream["codec_type"] == "audio":
				language_found = None
				try:
					language_found = stream["tags"]["language"]
				except:
					Log.v(TAG, "Could not find a language for stream " + str(stream["index"]))
				audio_streams.append({"index": stream["index"], "codec": stream["codec_name"], "channels": stream["channels"], "language": language_found})
		return audio_streams

	def parse_subs(self, ffprobe_dict):
		if ffprobe_dict == False:
			return
		sub_streams = []
		for stream in ffprobe_dict["streams"]:
			if stream["codec_type"] == "subtitle":
				language_found = None
				try:
					language_found = stream["tags"]["language"]
				except:
					Log.v(TAG, "Could not find a language for stream " + str(stream["index"]))
				# number of frames or bitrate is the best way to figure out the difference between secondary (ie foreign langauge/ forced) and primary (all text) captions.
				# There is likely a better way... still need to find it.
				br = None
				try:
					br = stream["nb_frames"]
				except:
					try:
						br = stream["tags"]["NUMBER_OF_FRAMES"]
					except:
						pass
				sub_streams.append({"index": stream["index"], "codec": stream["codec_name"], "language": language_found, "numframes": br})
		return sub_streams