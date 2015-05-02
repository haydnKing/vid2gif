#!/usr/bin/python3

import argparse, tempfile, subprocess, os, os.path, shutil, sys

#parse arguments
parser = argparse.ArgumentParser(description="Convert a video into a gif")
parser.add_argument("infile", 
										type=str, 
										help="Input file") 
parser.add_argument("outfile", 
										type=str, 
										help="Output file") 
parser.add_argument("-p",
										"--preview",
										help="Show a preview",
										action="store_true")
parser.add_argument("-s",
										"--start", 
										help="Start time in HH:MM:SS")
parser.add_argument("-l",
										"--length", 
										help="Length of clip to extract")
parser.add_argument("-w", 
										"--width", 
										type=int,
										help="Output width, default unchanged")
parser.add_argument("-x",
										"--crop", 
										type=str, 
										metavar="WIDTHxHEIGHT+XOFFSET+YOFFSET", 
										help="crop to widthxheight+x+y") 
parser.add_argument("-f", 
										"--fps",
										type=float,
										help="Output frames per second, default 25")
parser.add_argument("-c",
										"--colors",
										type=int,
										help="limit number of output colors")
parser.add_argument("-O",
										"--optimisation", 
										type=int,
										help="gifsicle optimisation level",
										default='1')
parser.add_argument("-L",
										"--loopreverse", 
										help="play forwards then backwards",
										action="store_true")


def validate_args(args):
	#file exists
	if not os.path.exists(args.infile):
		raise ValueError('File {} does not exist'.format(args.infile))
	

def get_ffmpeg_args(args, tempdir, preview=False):
	cmd = 'ffplay' if preview else 'ffmpeg'

	ffmpeg_args = [cmd,'-i', args.infile,]
	if args.width:
		ffmpeg_args += ['-vf', 'scale={}:-1'.format(args.width)]
	if args.length:
		ffmpeg_args += ['-t', args.length]
	if args.start:
		ffmpeg_args += ['-ss', args.start]
	
	if preview:
		ffmpeg_args += ['-loop', '0']
	else:
		ffmpeg_args += [os.path.join(tempdir, 'out%04d.gif')]

	return ffmpeg_args

def run_external(arglist, debug=True):
	#with open(os.devnull, "w") as devnull:
	if debug:
		print(" ".join(arglist))
	try:
		subprocess.check_output(arglist, stderr=subprocess.STDOUT)#, stdout=devnull, stderr=devnull)
	except subprocess.CalledProcessError as e:
		print('Error running \'{}\':\n\t{}'.format(
			arglist[0],
			e.output.decode('UTF-8')))
		sys.exit(-1)

def main():
	args = parser.parse_args()

	with tempfile.TemporaryDirectory() as tempdir:

		try:
			validate_args(args)
		except ValueError as e:
			print(e)
			sys.exit(-1)
		
		#extract
		run_external(get_ffmpeg_args(args, tempdir, preview=args.preview))
		if args.preview:
			sys.exit(0)

		frames = [os.path.join(tempdir, x) for x in sorted(os.listdir(tempdir))]

		#crop
		if args.crop:
			subprocess.check_call(['mogrify', '-crop', args.crop, '+repage'] + frames)

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

if __name__ == '__main__':
	main()
