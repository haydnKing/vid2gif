#!/usr/bin/python3

import argparse, tempfile, subprocess, os, os.path, shutil

#parse arguments
parser = argparse.ArgumentParser(description="Convert a video into a gif")
parser.add_argument("infile", type=str, help="Input file") 
parser.add_argument("outfile", type=str, help="Output file") 
parser.add_argument("--start",'-s', help="Start time in HH:MM:SS")
parser.add_argument("--length",'-l', help="Length of clip to extract")
parser.add_argument("--width", "-w", help="Output width, default unchanged")
parser.add_argument("--crop", type=str, metavar="WIDTHxHEIGHT+XOFFSET+YOFFSET", help="crop to widthxheight+x+y") 
parser.add_argument("--fps", "-f", help="Output frames per second, default 25")
parser.add_argument("--colors", help="limit number of output colors")
parser.add_argument("--optimisation", "-O", help="gifsicle optimisation level",
		default='1')
parser.add_argument("--loopreverse", "-L", help="play forwards then backwards",
		action="store_true")

args = parser.parse_args()

with tempfile.TemporaryDirectory() as tempdir:
	print("Using temporary directory \"{}\"".format(tempdir))
	
	#extract
	ffmpeg_args = ['ffmpeg',]
	if args.length:
		ffmpeg_args += ['-t', args.length]
	if args.start:
		ffmpeg_args += ['-ss', args.start]
	ffmpeg_args += ['-i', args.infile, os.path.join(tempdir, 'out%04d.gif')]

	ret = subprocess.check_call(ffmpeg_args)

	frames = [os.path.join(tempdir, x) for x in sorted(os.listdir(tempdir))]

	#crop
	if args.crop:
		subprocess.check_call(['mogrify', '-crop', args.crop, '+repage'] + frames)

	#resize
	if args.width:
		subprocess.check_call(['mogrify', '-resize', args.width,] + frames)
	
	if args.loopreverse:
		frames = frames + list(reversed(frames))[1:-1]

	#merge
	conv_args = ['gifsicle', '--loop',]
	if args.colors:
		conv_args += ['--colors', args.colors]
	if args.fps:
		conv_args += ['--delay', str(1.0 / float(args.fps)),]
	else:
		conv_args += ['--delay', '4',]
	conv_args += ['-O{}'.format(args.optimisation),]

	conv_args += frames
	conv_args += ['-o', args.outfile]
	ret = subprocess.check_call(conv_args)


