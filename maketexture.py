# make a texture from a heighmap

from PIL import Image
import PIL
import numpy
import time
import math

heightmap = "merged.scaled.float32.tiff"
output_name = "algotexture.png"
blockreach = 2
blocksize = float((blockreach * 2 + 1) ** 2)
threshold = 1.5 #(256*256) / 650 * 10
mud_threshold = -1 * threshold / 4

# open image and obtain raw data
himg = Image.open(heightmap)
himg.load()
hdat = numpy.array(himg)
print("Size of input heighmap: %s" % str(hdat.shape))
print("Largest value: %s" % str(hdat.max()))
print("Smallest value: %s" % str(hdat.min()))

# create a larger area so that we can elliminate corner cases
wid = hdat.shape[0]
hig = hdat.shape[1]
print("There will be %d pixels to color." % (wid*hig))
hdat_ext = numpy.zeros(shape=(wid+blockreach*2,hig+blockreach*2), dtype=numpy.float32)
hdat_ext[blockreach:wid+blockreach,blockreach:hig+blockreach] = hdat

# corners
hdat_ext[0:blockreach,                    0:blockreach                   ] = hdat[0,0]
hdat_ext[0:blockreach,                    hig+blockreach:hig+2*blockreach] = hdat[0,hig-1]
hdat_ext[wid+blockreach:wid+2*blockreach, 0:blockreach                   ] = hdat[wid-1,0]
hdat_ext[wid+blockreach:wid+2*blockreach, hig+blockreach:hig+2*blockreach] = hdat[wid-1,hig-1]

# sides
hdat_ext[0:blockreach,blockreach:wid+blockreach] = hdat[0,:]
hdat_ext[hig+blockreach:hig+2*blockreach,blockreach:wid+blockreach] = hdat[-1,:]
#hdat_ext[blockreach:hig+blockreach,0:blockreach] = hdat[:,0]
#hdat_ext[blockreach:hig+blockreach,wid+blockreach:wid+2*blockreach] = hdat[:,-1]

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
green_np = numpy.array(green, dtype=numpy.float32)
brown_np = numpy.array(brown, dtype=numpy.float32)
colors = dict()
merged = Image.new(size=(wid,hig), mode='RGB', color=green)
for x in range(wid):
	newperc = int(100 * x / wid)
	if newperc != perc:
		perc = newperc
		print("Done with %d%%." % perc)
	for y in range(hig):
		x2 = x + blockreach
		y2 = y + blockreach
		v = hdat_ext[x2,y2]
		s = hdat_ext[x2-blockreach:x2+blockreach+1,y2-blockreach:y2+blockreach+1]
		diff = v - (s.sum() / blocksize)  # positive means center is higher
		if (diff > threshold) or (diff < 0 and (s.max() - s.min() > threshold * 2)):
			clr = gray
		elif diff < mud_threshold:        # notably negative center compared to nieghbors
			clr = brown
		elif diff < 0:
			p = diff / mud_threshold      # result will be positive
			clr = tuple((green_np * p + brown_np * (1-p)).astype(numpy.uint8))
		else:
			continue
		merged.putpixel((y,x),clr)

et = time.time() - start_time
pps = wid * hig / et
spmp = 1000 * 1000 / pps
print("Elapsed seconds: %s" % int(round(et)))
print("Pixels per second: %s" % int(round(pps)))
print("Seconds per million pixels: %s" % int(round(spmp)))
print("Write texture.")
merged.save(output_name)
