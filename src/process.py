## Copyright (c) 2007 Ashish Kulkarni
##
## Permission is hereby granted, free of charge, to any person obtaining a
## copy of this software and associated documentation files (the "Software"),
## to deal in the Software without restriction, including without limitation
## the rights to use, copy, modify, merge, publish, distribute, sublicense,
## and/or sell copies of the Software, and to permit persons to whom the
## Software is furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
## FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
## DEALINGS IN THE SOFTWARE.


import os, sys, math, Image, ImageFilter, ImageChops, ImageOps

from common import *


########################################################### PROCESSING

MAX_CROP_SIZE = 100
MAX_CROP_STEP = 10

""" internal function for cropping a single axis """
def crop_axis(input, img, start, end, percent,
              func_crop, func_size, func_pos):

  # compute optimal step and size for given axis percentage
  size = min(MAX_CROP_SIZE,  max(1, int((end-start)*percent/100)))
  step = min(MAX_CROP_STEP,  max(1, int(size/10)))

  content    = []
  begin      = start
  blank_area = False
  for i in range(start, end, step):
    test = img.crop( func_crop(i, i+size) )
    if test.getbbox() is None:
      if not blank_area:
        # we've hit a blank area, so save content area
        content.append( (begin, i) )
        blank_area = True
    else:
      if blank_area:
        # we've moved out of a blank area, mark beginning
        begin = i
        blank_area = False

  # handle the last leftover area
  if not blank_area and end > begin:
    content.append( (begin, end) )

  # create image with shrunken axis
  newI   = sum([last-first for first, last in content])
  output = Image.new('L', func_size(newI), None)

  # append the content parts
  i = 0
  for first, last in content:
    output.paste( input.crop(func_crop(first, last)), func_pos(i) )
    i += (last - first)

  # return output
  return output


""" perform image cropping via whitespace detection """
def crop(input, percent=DEFAULT_CROP_PERCENT):
  p('CROP ')
  w, h = input.size
  img  = ImageChops.invert(input)
  box  = img.getbbox()
  if box is None:
    return None

  l, t, r, b = box

  # crop horizontal blank areas
  temp = crop_axis(input, img, t, b, percent,
                   lambda s, e: (0, s, w, e),
                   lambda s   : (w, s),
                   lambda s   : (0, s))

  w, h = temp.size
  img  = ImageChops.invert(temp)

  # crop vertical blank areas
  return crop_axis(temp, img, l, r, percent,
                   lambda s, e: (s, 0, e, h),
                   lambda s   : (s, h),
                   lambda s   : (s, 0))

""" perform image dilation """
def dilate(image):
  p('DILATE ')
  return image.filter(ImageFilter.MinFilter)

""" perform unpaper cleanup """
def unpaper(image, args):
  p('UNPAPER ')
  rm('page_i.pgm', 'page_o.pgm')
  image.save('page_i.pgm')
  cmd = ['unpaper', '--overwrite'] + args.split() + ['page_i.pgm', 'page_o.pgm']
  call(*cmd)
  if not os.path.exists('page_o.pgm'):
    return None

  return Image.open('page_o.pgm')

##############################################################################


""" potrait mode """
class PotraitMode(BaseMode):
  __plugin__ = 'potrait'

  """ execute """
  def __call__(self, image):
    # find the ratios
    imgH, imgV     = image.size
    ratioH, ratioV = float(self.hres)/imgH, float(self.vres)/imgV

    # select the lower ratio
    ratio  = min(ratioH, ratioV)
    size   = ( int(imgH*ratio), int(imgV*ratio) )

    return [ image.resize(size, Image.ANTIALIAS) ]


##############################################################################


""" landscape mode """
class LandscapeMode(BaseMode):
  __plugin__ = 'landscape'

  """ initialise """
  def __init__(self, hres, vres, overlap, rotate, **args):
    self.hres, self.vres, self.overlap = hres, vres, overlap
    self.rotate = ROTATION[rotate]

  """ execute """
  def __call__(self, image):
    p('SPLIT ')
    output = []

    # find the ratios
    imgH, imgV     = image.size
    ratioH, ratioV = float(self.vres)/imgH, float(self.hres)/imgV

    if ratioH >= 2 or ratioV >= 2:
      # too many pages will be generated, so fit to device size
      ratio  = min(ratioH, ratioV)
      size   = ( int(imgH*ratio), int(imgV*ratio) )

      return [ image.resize(size, Image.ANTIALIAS) ]

    # determine the height which will maintain aspect ratio
    height = int(float(self.vres) / image.size[0] * image.size[1])
    final  = image.resize((self.vres, height), Image.ANTIALIAS)

    # split it up into multiple landscape pages
    completed = 0
    while completed + self.overlap < height:
      page = final.crop( (0, completed, self.vres,
                          min(completed+self.hres, height)) )

      if self.rotate is not None:
        page = page.transpose(self.rotate)

      output.append( page )
      completed = completed + self.hres - self.overlap

    return output
