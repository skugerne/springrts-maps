# make a texture from a heighmap

from PIL import Image
import PIL
import numpy
import time
import math
import argparse

parser = argparse.ArgumentParser(description='Merge raw DTM images.')
parser.add_argument('input', metavar='INFILE', help='file to consume, a heightmap probably best in float32 grayscale')
parser.add_argument('output', metavar='OUTFILE', nargs='?', help='file to output, will be filled with RGB pixels (default: %(default)s)', default='algotexture.png')
parser.add_argument('--columns', metavar='START,STOP', help='process only the given columns, place only those pixels in the result image (the stop column is not included) (default: all columns)')
parser.add_argument('--blockreach', metavar='PIXELS', type=int, help='reach of analysis block (default: %(default)s)', default=2)
args = parser.parse_args()

PIL.Image.MAX_IMAGE_PIXELS = None

blockreach = args.blockreach
blocksize = float((blockreach * 2 + 1) ** 2)
threshold = 3.0
mud_threshold = -1 * threshold / 8

print("Load the image.")
himg = Image.open(args.input)
himg.load()
hdat = numpy.array(himg)
print("Size of input heightmap (HxW, RxC): %s" % str(hdat.shape))
print("Largest value: %s" % str(hdat.max()))
print("Smallest value: %s" % str(hdat.min()))

if args.columns:
	a,b = args.columns.split(',')
	a,b = int(a),int(b)
	if a < 0 or a >= b or b > hdat.shape[1]:
		raise Exception("The column limit is no good.")
	args.columns = (a,b)
else:
	args.columns = (0,hdat.shape[1])

print("Pad the array.")
hig = hdat.shape[0]
wid = hdat.shape[1]
cut_wid = args.columns[1]-args.columns[0]
print("There will be %d pixels to color." % (wid*hig))
hdat_ext = numpy.zeros(shape=(wid+blockreach*2,hig+blockreach*2), dtype=numpy.float32)
hdat_ext[blockreach:wid+blockreach,blockreach:hig+blockreach] = hdat

print("Fill in corner padding.")
hdat_ext[0:blockreach,                    0:blockreach                   ] = hdat[0,0]
hdat_ext[0:blockreach,                    hig+blockreach:hig+2*blockreach] = hdat[0,hig-1]
hdat_ext[wid+blockreach:wid+2*blockreach, 0:blockreach                   ] = hdat[wid-1,0]
hdat_ext[wid+blockreach:wid+2*blockreach, hig+blockreach:hig+2*blockreach] = hdat[wid-1,hig-1]

print("Fill in top and bottom padding.")
hdat_ext[0:blockreach,blockreach:wid+blockreach] = hdat[0,:]
hdat_ext[hig+blockreach:hig+2*blockreach,blockreach:wid+blockreach] = hdat[-1,:]
print("Fill in left and right padding.")
hdat = numpy.fliplr(numpy.rot90(hdat))
hdat_ext = numpy.fliplr(numpy.rot90(hdat_ext))
hdat_ext[0:blockreach,blockreach:hig+blockreach] = hdat[0,:]
hdat_ext[wid+blockreach:wid+2*blockreach,blockreach:hig+blockreach] = hdat[-1,:]
hdat = numpy.fliplr(numpy.rot90(hdat))
hdat_ext = numpy.fliplr(numpy.rot90(hdat_ext))

# some confirmation
print("Corner: %s" % str(hdat_ext[:2*blockreach,:2*blockreach]))
print("Corner: %s" % str(hdat_ext[:2*blockreach,-2*blockreach:]))
print("Corner: %s" % str(hdat_ext[-2*blockreach:,:2*blockreach]))
print("Corner: %s" % str(hdat_ext[-2*blockreach:,-2*blockreach:]))

start_time = time.time()
perc = None
gray = (128,128,128)
brown = (64,64,32)
green = (64,128,32)
gray_green_np = numpy.array((gray,green), dtype=numpy.float32)
green_brown_np = numpy.array((green,brown), dtype=numpy.float32)
colors = dict()
merged = Image.new(size=(hig,cut_wid), mode='RGB', color=green)
for x in range(*args.columns):
	newperc = int(100 * x / cut_wid)
	if newperc != perc:
		perc = newperc
		print("Done with %d%%." % perc)
	for y in range(hig):
		x2 = x + blockreach
		y2 = y + blockreach
		s = hdat_ext[x2-1:x2+2,y2-1:y2+2]
		diff = s.max() - s.min()
		if diff > threshold * 2:
			clr = gray
		else:
			v = hdat_ext[x2,y2]
			s = hdat_ext[x2-blockreach:x2+blockreach+1,y2-blockreach:y2+blockreach+1]
			diff = v - (s.sum() / blocksize)  # positive means center is higher
			if diff > threshold:
				clr = gray
			elif diff > 0:
				p = diff / threshold          # positive / positive
				clr = tuple(numpy.array((p,1-p), dtype=numpy.float32).dot(gray_green_np).astype(numpy.uint8))
			elif diff < mud_threshold:        # notably negative center compared to nieghbors
				clr = brown
			elif diff < 0:
				p = diff / mud_threshold      # negative / negative
				clr = tuple(numpy.array((1-p,p), dtype=numpy.float32).dot(green_brown_np).astype(numpy.uint8))
			else:
				continue
		merged.putpixel((y,x-args.columns[0]),clr)

et = time.time() - start_time
pps = cut_wid * hig / et
spmp = 1000 * 1000 / pps
print("Elapsed seconds: %s" % int(round(et)))
print("Pixels per second: %s" % int(round(pps)))
print("Seconds per million pixels: %s" % int(round(spmp)))
print("Write texture.")
merged.save(args.output)
