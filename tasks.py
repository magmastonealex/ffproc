import subprocess
import shutil
import os
import re
import fnmatch

def ffmpeg(arg):
	path=arg["path"]
	print arg
	extension=os.path.splitext(path)[1]
	pathout=re.sub("(?i)xvid","H264",path)
	pathout=re.sub(extension,".mp4",pathout)
	out=subprocess.call(["ffmpeg","-i",path]+arg["opts"]+["tmp.mp4"])
	if not out == 0:
		print "FFMPEG FAILED"
	else:
		shutil.move("tmp.mp4",pathout)
		if fnmatch.fnmatchcase(path,pathout)==False:
			os.remove(path)
