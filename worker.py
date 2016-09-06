from task import Task
import subprocess
import os
import shutil

def ffmpeg(arg):
	
	torun = Task(createfrom=arg)

#	codeccheck = subprocess.Popen(["ffmpeg", "-codecs"], stdout=subprocess.PIPE)

	out=subprocess.call(["ffmpeg","-i", torun.infile]+torun.arguments+["tmp.mp4"])
	if not out == 0:
		print "FFMPEG FAILED"
	else:
		shutil.move("tmp.mp4",torun.outfile)
		os.remove(path)

	try:
		os.remove("tmp.mp4")
	except:
		pass