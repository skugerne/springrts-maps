from PIL import Image
import PIL
import numpy
from libtiff import TIFF   # used to export 16-bit grayscale tiff
import argparse

parser = argparse.ArgumentParser(description='Merge raw DTM images.')
parser.add_argument('--output-size-SMU', metavar='SMU', type=int, help='the size of the intended map in Spring Map Units (default: %(default)s)', default=28)
parser.add_argument('--example-thumbs', action='store_true', help='generate thumbnails of the images in 8-bit gray PNG')
args = parser.parse_args()

texture_dim = args.output_size_SMU * 512
texture_shape = (texture_dim,texture_dim)
heightmap_dim = args.output_size_SMU * 64 + 1
heightmap_shape = (heightmap_dim,heightmap_dim)
maxscale8 = float(256-1)
maxscale16 = float(256*256-1)

# the images to combine
# could un-hardcode these with a little parsing of the names
path1 = 'dtm1/data/dtm1_33_122_114.tif'
path2 = 'dtm1/data/dtm1_33_122_115.tif'   # towards hønnefoss
path3 = 'dtm1/data/dtm1_33_123_114.tif'   # nesodtangen
path4 = 'dtm1/data/dtm1_33_123_115.tif'
PIL.Image.MAX_IMAGE_PIXELS = None         # allow loading of very large images

print("Load images...")
img1 = Image.open(path1)
img1.load()
print("Load images...")
img2 = Image.open(path2)
img2.load()
print("Load images...")
img3 = Image.open(path3)
img3.load()
print("Load images...")
img4 = Image.open(path4)
img4.load()

# poke some missing data
# they seem to have the value -32767.0 represent NULL
print("PIXEL "+str(img2.getpixel((100,100))))

th1 = numpy.array(img1)
th2 = numpy.array(img2)
th3 = numpy.array(img3)
th4 = numpy.array(img4)
print("Smallest (raw): "+str(min((th1.min(),th2.min(),th3.min(),th4.min()))))
th1[th1 < 0] = 0
th2[th2 < 0] = 62.714691162109375   # an observed value
th3[th3 < 0] = 0
th4[th4 < 0] = 0
biggest = max((th1.max(),th2.max(),th3.max(),th4.max()))
smallest = min((th1.min(),th2.min(),th3.min(),th4.min()))
print("Biggest: "+str(biggest))
print("Smallest (fixed): "+str(smallest))
print("Shape 1: "+str(th1.shape))
print("Shape 2: "+str(th2.shape))
print("Shape 3: "+str(th3.shape))
print("Shape 4: "+str(th4.shape))
assert th1.shape == th2.shape == th3.shape == th4.shape and th4.shape[0] == th4.shape[1], "Shape issue."

rawdim = th1.shape[0]
mega_shape = (rawdim*2-10,rawdim*2-10)

# build the raw merged image
# there appears to be a 10-pixel overlap, which we simply allow one of the images to claim
mega = numpy.zeros(shape=mega_shape, dtype=numpy.float32)
lowstop = rawdim
higstop = 2*rawdim
mega[rawdim-10:higstop,0:lowstop] = th1
mega[0:lowstop,0:lowstop] = th2
mega[rawdim-10:higstop,rawdim-10:higstop] = th3
mega[0:lowstop,rawdim-10:higstop] = th4
print("Shape combined: "+str(mega.shape))

if args.example_thumbs:
	pixeltype = numpy.uint8
	thumb_mode = 'L'
	thumb_side = 1024
	thumb_size = (thumb_side,thumb_side)
	merged_thumb_size = (2*thumb_side,2*thumb_side)

	# scale the image part data for export to thumbnails
	th1 = th1 / biggest * maxscale8
	th1 = th1.astype(pixeltype)
	th2 = th2 / biggest * maxscale8
	th2 = th2.astype(pixeltype)
	th3 = th3 / biggest * maxscale8
	th3 = th3.astype(pixeltype)
	th4 = th4 / biggest * maxscale8
	th4 = th4.astype(pixeltype)

	biggest_scaled = max((th1.max(),th2.max(),th3.max(),th4.max()))
	print("Biggest, scaled: "+str(biggest_scaled))

	print("Write thumbnails...")
	th1 = Image.fromarray(th1, mode=thumb_mode)
	th1.thumbnail(thumb_size)
	th1.save("dtm1_33_122_114.thumbnail.png")
	print("Write thumbnails...")
	th2 = Image.fromarray(th2, mode=thumb_mode)
	th2.thumbnail(thumb_size)
	th2.save("dtm1_33_122_115.thumbnail.png")
	print("Write thumbnails...")
	th3 = Image.fromarray(th3, mode=thumb_mode)
	th3.thumbnail(thumb_size)
	th3.save("dtm1_33_123_114.thumbnail.png")
	print("Write thumbnails...")
	th4 = Image.fromarray(th4, mode=thumb_mode)
	th4.thumbnail(thumb_size)
	th4.save("dtm1_33_123_115.thumbnail.png")

	print("Write merged thumbnail...")
	merged = Image.new(size=merged_thumb_size, mode=thumb_mode)
	print("Size merged thumb: "+str(merged.size))
	merged.paste(th1,(0,thumb_side))
	merged.paste(th2,(0,0))
	merged.paste(th3,thumb_size)
	merged.paste(th4,(thumb_side,0))
	merged.save("merged.thumbnail.png")

# garbage collection does not clean these up
# if these are not removed (python 3.7.5) the program will proceed to get out-of-mem killed
del th1
del th2
del th3
del th4
del img1
del img2
del img3
del img4

print("Write scaled result in 8 bit int grayscale...")
print("Range (before) %s to %s." % (mega.min(),mega.max()))
mega2 = ((mega + smallest) / biggest * maxscale8).astype(numpy.uint8)
print("Range (after) %s to %s." % (mega2.min(),mega2.max()))
mega3 = Image.fromarray(mega2, mode='L')
mega3.save("merged.scaled.uint8.png")
mega3.thumbnail(texture_shape)
mega3.save("merged.scaled.uint8.%d-texture.png" % args.output_size_SMU)
mega3 = Image.fromarray(mega2, mode='L')
mega3.thumbnail(heightmap_shape)
mega3.save("merged.scaled.uint8.%d-heightmap.png" % args.output_size_SMU)

print("Write scaled result in 16 bit int grayscale...")
print("Range (before) %s to %s." % (mega.min(),mega.max()))
mega2 = (mega + smallest) / biggest * maxscale16
print("Range (after) %s to %s." % (mega2.min(),mega2.max()))
tiff = TIFF.open("merged.scaled.uint16.tiff", mode='w')
tiff.write_image(mega2.astype(numpy.uint16))
tiff.close()
mega3 = Image.fromarray(mega2, mode='F')
mega3.thumbnail(texture_shape)
tiff = TIFF.open("merged.scaled.uint16.%d-texture.tiff" % args.output_size_SMU, mode='w')
tiff.write_image(numpy.array(mega3).astype(numpy.uint16))
tiff.close()
mega3 = Image.fromarray(mega2, mode='F')
mega3.thumbnail(heightmap_shape)
tiff = TIFF.open("merged.scaled.uint16.%d-heightmap.tiff" % args.output_size_SMU, mode='w')
tiff.write_image(numpy.array(mega3).astype(numpy.uint16))
tiff.close()

print("Write unscaled merged image in 32-bit float grayscale...")
print("Range %s to %s." % (mega.min(),mega.max()))
mega2 = Image.fromarray(mega, mode='F')
mega2.save("merged.float32.tiff")
mega2.thumbnail(texture_shape)
mega2.save("merged.float32.%d-texture.tiff" % args.output_size_SMU)
mega2 = Image.fromarray(mega, mode='F')
mega2.thumbnail(heightmap_shape)
mega2.save("merged.float32.%d-heightmap.tiff" % args.output_size_SMU)

print("Reached end!")