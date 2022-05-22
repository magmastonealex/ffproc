from task import Task
import subprocess
import os
import shutil
import sys

def ffmpeg(arg):
	
	torun = Task(createfrom=arg)

	# Get the output file extension:
	destExtension = torun.outfile.split(".")[-1]
	print(torun.outfile.split("."))
	tmpfile = "tmp." + destExtension

	codeccheck = subprocess.Popen(["ffmpeg", "-codecs"], stdout=subprocess.PIPE)
	allcodecs = codeccheck.communicate()[0].decode('utf-8')
	if allcodecs.find("libfdk_aac") == -1:
		print("Install libfdk_aac for better audio quality!")
		if torun.forcefdk == True:
			print("Server has disabled workers without libfdk_aac!")
			sys.exit()
		else:
			if "libfdk_aac" in torun.arguments:
				libfdk_pos = torun.arguments.index("libfdk_aac")
				torun.arguments[libfdk_pos] = "aac"
				torun.arguments.append("-strict")
				torun.arguments.append("-2")

	out=subprocess.call(["ffmpeg","-i", torun.infile]+torun.arguments+[tmpfile])
	if not out == 0:
		print("FFMPEG FAILED")
	else:
		shutil.move(tmpfile,torun.outfile)
		# To-do: de-hackify this.
		try:
			subprocess.call(["/usr/share/ffproc/completed", torun.outfile])
		except:
			pass
		os.remove(torun.infile)

	try:
		os.remove(tmpfile)
	except:
		pass
