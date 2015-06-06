import subprocess
import shutil
import os

def ffmpeg(arg):
	path=arg["path"]
	print arg
	pathout=arg["path"]+".mp4"
	out=subprocess.call(["ffmpeg","-i",path]+arg["opts"]+["tmp.mp4"])
	if not out == 0:
		print "FFMPEG FAILED"
	else:
		shutil.move("tmp.mp4",pathout)
		os.remove(path)
