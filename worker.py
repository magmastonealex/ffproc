from task import Task
import subprocess
import os
import shutil
import sys

def ffmpeg(arg):
	
	torun = Task(createfrom=arg)

	codeccheck = subprocess.Popen(["ffmpeg", "-codecs"], stdout=subprocess.PIPE)
	allcodecs = codeccheck.communicate()[0]
	if allcodecs.find("libfdk_aac") == -1:
		print "Install libfdk_aac for better audio quality!"
		if torun.forcefdk == True:
			print "Server has disabled workers without libfdk_aac!"
			sys.exit()
		else:
			if "libfdk_aac" in torun.arguments:
				libfdk_pos = torun.arguments.index("libfdk_aac")
				torun.arguments[libfdk_pos] = "aac"
				torun.arguments.append("-strict")
				torun.arguments.append("-2")

	out=subprocess.call(["ffmpeg","-i", torun.infile]+torun.arguments+["tmp.mp4"])
	if not out == 0:
		print "FFMPEG FAILED"
	else:
		shutil.move("tmp.mp4",torun.outfile)
		os.remove(torun.infile)

	try:
		os.remove("tmp.mp4")
	except:
		pass
