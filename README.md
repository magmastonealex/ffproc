FFProc
====

*This project is currently undergoing a ground-up-rewrite. This new version is now in a usable state, but is still fairly experimental.*

This script allows you to transcode massive media libraries to a configurable final profile. The goal is to be easily extensible but simultaneously simple to use.

It has sane defaults which allow you to pre-transcode media for, say, a Plex or Emby server, and have them do effectively no transcoding. FWIW, I can run a Plex server off an old Atom board limited only by bandwidth because I transcode everything in advance with these scripts.


**BACK UP/COPY YOUR MEDIA BEFORE RUNNING THIS**. I haven't had any problem running this on my 2TB media library, but I can't guarantee this will hold true for you as well.

One of the reasons I wrote `ffproc` was to be able to distribute my transcoding workload over multiple machines. This does, however, require more setup. For a basic setup, without any sort of enqueing, all you need is ffmpeg installed. I'd highly reccommend installing or compiling a version with 'libfdk_aac' in it, because it results in much clearer-sounding audio compared to the stock aac encoder.

Basic Usage
====

```
usage: ffproc.py [-h] [--profile PROFILE] [--immediate] [--redis REDIS]
                 [--showcommand] [--dryrun]
                 file

Enqueue media files for transcoding, using a variety of profiles.

positional arguments:
  file               The file to transcode

optional arguments:
  -h, --help         show this help message and exit
  --profile PROFILE  Force a particular profile
  --immediate        Don't use Redis, just run the transcode immediately
  --redis REDIS      Redis IP address, if not localhost
  --showcommand      (debug) Show the FFMPEG command used
  --dryrun           (debug) Stop short of actually enqueing the file
```

This script needs to be run for every file in your library. I'd reccommend running `find /your/media/from/root -exec ./ffproc.py --immediate {} \;` to do this.

Before running it for the first time, I'd reccommend editing the `.json` files to fit your needs. Take a look at profiles.json for the format. Each option is described below.

```
Qualities describe a file target.
	video:
		- ignore: true - Just copy, we don't care about it.
		- codec: h264/hevc - the codec to use
		- allowhvec: true/false
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
	output: (currently unused!)
		- filetype matroska/mp4 - What output file format to use
		- quickstart true/false - Run a postprocessing step to enable mp4 quickstart.
```

You can use the `--profile` option to force a particular profile.

`regexes.json` is a more advanced feature allowing you to customize which files get which preset, especially useful if you do a nightly run of ffproc.

Advanced Usage (queuing)
====

Requirements
----

 - You need a Redis server setup to listen on localhost.
 - You need `rq`,`redis` modules installed for python2.
 - You need to have your media directories accessable via NFS/SMB on each worker in the same absolute paths as on the server (fix for this coming soon!)

How-to
----

 - Run ffproc over a subset of media to test it out. You may want to follow the above simpler directions until you find options that are suitable for you.
 - Run `rqinfo` to view each of the queues. You should see a number of jobs ready to run.
 - In the ffproc directory which has been cloned to the worker, run `rqworker -u redis://your.ip.master.here video audio remux`. You can remove or reorder the queues here if one of your workers, say, isn't powerful enough to transcode video.
 - The worker should start popping jobs off, transcoding, uploading the file into place, and removing the old one. Make sure the permissions are set correctly on the server-side!


Still coming up
----

- [ ] Support running ffproc from somewhere else. (Right now you must be in the ffproc directory to execute it. I'm not sure how Python handles non-system library importing, and finding the path to files like settings.json)
- [ ] Handle container/output options (Right now it's ignored, just always set to MP4 with quickstart)
- [ ] Set worker path to media directories (So that you can have workers which have mounted the media folders somewhere other than the same paths as the master)
- [ ] Worker failure should re-queue somehow
- [ ] Start work on improving the ffmpeg status update server (It's not the most reliable thing in the world)
- [ ] Write a simplistic frontend for the status update which shows current jobs, their speeds, worker status, etc. (This is a fairly large-scale task)
- [ ] Open an issue and let me know what *you* want to see here!
