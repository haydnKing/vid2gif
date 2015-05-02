#!/usr/bin/python3

import argparse, tempfile, subprocess, os, os.path, shutil, sys
from wand.image import Image

#parse arguments
def get_args():
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
											help="limit number of output colors")
	parser.add_argument("-O",
											"--optimisation", 
											help="gifsicle optimisation level",
											default='1')
	parser.add_argument("-L",
											"--loopreverse", 
											help="play forwards then backwards",
											action="store_true")
	parser.add_argument("--debug", 
											help="Show debug info",
											action="store_true")
	args =  parser.parse_args()

	if args.crop:
		m = re.match('(\d+)[xX](\d+)\+(\d+)\+(\d+)', args.crop)
		if not m:
			print("Invalid crop specification \'{}\'".format(args.crop))
		args.crop = tuple(m.group(x) for x in range(1,5))

	return args


def validate_args(args):
	#file exists
	if not os.path.exists(args.infile):
		raise ValueError('File {} does not exist'.format(args.infile))
	

def get_ffmpeg_args(args, tempdir, preview=False, outext='gif'):
	cmd = 'ffplay' if preview else 'ffmpeg'

	ffmpeg_args = [cmd,'-i', args.infile,]
	if args.length:
		ffmpeg_args += ['-t', args.length]
	if args.start:
		ffmpeg_args += ['-ss', args.start]
	
	if preview:
		ffmpeg_args += ['-an']
	else:
		ffmpeg_args += [os.path.join(tempdir, 'out%04d.{}'.format(outext))]

	return ffmpeg_args

def get_merge_args(args, frames):
	merge_args = ['gifsicle', '--loop',]
	if args.colors:
		merge_args += ['--colors', args.colors]
	if args.fps:
		merge_args += ['--delay', str(1.0 / float(args.fps)),]
	else:
		merge_args += ['--delay', '4',]
	merge_args += ['-O{}'.format(args.optimisation),]

	merge_args += frames
	merge_args += ['-o', args.outfile]

	return merge_args


def run_external(arglist, debug=False):
	if debug:
		print(" ".join(arglist))
	try:
		subprocess.check_output(arglist, stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		print('Error running \'{}\':\n\t{}'.format(
			arglist[0],
			e.output.decode('UTF-8')))
		sys.exit(-1)

def main():
	args = get_args()

	with tempfile.TemporaryDirectory() as tempdir:

		try:
			validate_args(args)
		except ValueError as e:
			print(e)
			sys.exit(-1)
		
		#extract
		run_external(get_ffmpeg_args(args, 
																 tempdir, 
																 preview=args.preview,
																 outext='gif'),
								 debug=args.debug)
		if args.preview:
			sys.exit(0)

		frames = [os.path.join(tempdir, x) for x in sorted(os.listdir(tempdir))]
		for frame in frames:
			with Image(filename=frame) as original:
				#scale and crop
				if args.crop:
					original.crop(args.crop[3], 
												args.crop[4], 
												width=args.crop[0],
												height=args.crop[1])
				if args.width:
					h = int((original.height * args.width) / original.width)
					original.resize(args.width, h, filter='sinc')
				with original.convert('gif') as converted:
					converted.save(filename="{}.gif".format(os.path.splitext(frame)[0]))
		frames = ["{}.gif".format(os.path.splitext(frame)[0]) for frame in frames]

		if args.loopreverse:
			frames = frames + list(reversed(frames))[1:-1]

		#merge
		run_external(get_merge_args(args, frames),
								 debug=args.debug)

if __name__ == '__main__':
	main()
