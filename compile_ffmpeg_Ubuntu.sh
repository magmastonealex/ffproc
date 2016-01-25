#! /bin/bash

timer ()
{
    SECS=$1
    while [ 0 -ne $SECS ]; do
        echo "$SECS.."
        sleep 1
        SECS=$((SECS-1))
    done
}

echo "Updating & Upgrading your system"

timer 5
#removing old version of ffmpeg
sudo apt-get -y remove ffmpeg

#updating and upgrading system
sudo apt-get update
sudo apt-get -y upgrade

#installing needed packages
sudo apt-get -y --force-yes install autoconf automake build-essential libass-dev libfreetype6-dev libgpac-dev \
  libsdl1.2-dev libtheora-dev libtool libva-dev libvdpau-dev libvorbis-dev libxcb1-dev libxcb-shm0-dev \
  libxcb-xfixes0-dev pkg-config texi2html zlib1g-dev yasm libx264-dev unzip libmp3lame-dev

#make source dir
dir=`pwd`
mkdir $dir/ffmpeg_sources

#compile H.265/HEVC
sudo apt-get install cmake mercurial
cd $dir/ffmpeg_sources
hg clone https://bitbucket.org/multicoreware/x265
cd $dir/ffmpeg_sources/x265/build/linux
PATH="$dir/bin:$PATH" cmake -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX="$dir/ffmpeg_build" -DENABLE_SHARED:bool=off ../../source
make
make install
make distclean

#compile fdk-aac
cd $dir/ffmpeg_sources
wget -O fdk-aac.zip https://github.com/mstorsjo/fdk-aac/zipball/master
unzip fdk-aac.zip
cd mstorsjo-fdk-aac*
autoreconf -fiv
./configure --prefix="$dir/ffmpeg_build" --disable-shared
make
make install
make distclean

#compile ffmpeg
cd $dir/ffmpeg_sources
wget http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
tar xjvf ffmpeg-snapshot.tar.bz2
cd ffmpeg
PATH="$dir/bin:$PATH" PKG_CONFIG_PATH="$dir/ffmpeg_build/lib/pkgconfig" ./configure \
  --prefix="$dir/ffmpeg_build" \
  --extra-cflags="-I$dir/ffmpeg_build/include" \
  --extra-ldflags="-L$dir/ffmpeg_build/lib" \
  --bindir="$dir/bin" \
  --pkg-config-flags="--static" \
  --enable-gpl \
  --enable-libass \
  --enable-libfdk-aac \
  --enable-libfreetype \
  --enable-libmp3lame \
  --enable-libtheora \
  --enable-libvorbis \
  --enable-libx264 \
  --enable-libx265 \
  --enable-nonfree
PATH="$dir/bin:$PATH" make
make install
make distclean
hash -r

#move binary files to /usr/local/bin
cd $dir/bin
sudo cp * /usr/local/bin/

#move man pages to /usr/local/share/man
cd $dir/ffmpeg_build/share/man
sudo cp -a * /usr/local/share/man

#delete build directories
cd $dir
sudo rm -Rf bin/ ffmpeg_*

echo "FFmpeg and needed encoders have been correctly installed"

timer 5
