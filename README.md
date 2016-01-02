FFProc
====

These two scripts allow you to transcode massive media libraries to H.264/AAC/MP4.

**BACK UP/COPY YOUR MEDIA BEFORE RUNNING THIS**. I haven't had any problem running this on my 2TB media library, but I can't guarantee this will hold true for you as well.

Requirements
----

 - You need a Redis server setup to listen on localhost.
 - You need `rq`,`redis` modules installed for python2.
 - You need `ffmpeg` installed with the libfdk_aac codec. This sounds significantly better than the builtin aac codec at all bitrates, and supports a VBR mode.

`ffproc.py`
----
This script needs to be run for every file in your library. I'd reccommend running `find /your/media/from/root -exec python2 ffproc.py {} \;` to do this. 

This script will put everything into an [RQ](http://python-rq.org/) queue. This allows you to enqueue all of your files in a persistant way, and run workers whenever it's convinient. 

The script is fairly well commented.

You *can* run FFProc without the distributed component, by uncommenting a few lines in the code, well marked in the file. In this mode, you don't need a Redis server set up at all. 

`tasks.py`
----
This file isn't run directly. Instead, once you've enqueued your media, run `rqworker mux-core audio-core video-core`. This will run the worker which will transcode all of your media, replacing it with MP4s.


