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


## The edge enhancing technique is taken from Philip R. Thompson's "xim"
## program, which in turn took it from section 6 of "Digital Halftones by
## Dot Diffusion", D. E. Knuth, ACM Transaction on Graphics Vol. 6, No. 4,
## October 1987, which in turn got it from two 1976 papers by J. F. Jarvis
## et. al.
class EdgeEnhanceFilter(ImageFilter.Kernel):
  def __init__(self, n):
    if n < 1 or n > 9:
      raise ValueError("enhancement parameter incorrect")

    self.name = 'Edge-enhancement'
    phi    = n / 10.0
    omphi  = 1.0 - phi
    x      = -phi/9.0

    self.filterargs = (3,3), omphi, 0.5, [x,    x,    x,
                                          x,  1+x,    x,
                                          x,    x,    x]


########################################################### PROCESSING

""" perform image cropping via whitespace detection at the borders """
def crop(image):
  p('CROP ')
  bbox = ImageChops.invert(image).getbbox()
  if bbox is None:
    return None

  return image.crop(bbox)

""" perform image dilation """
def dilate(image):
  p('DILATE ')
  return image.filter(ImageFilter.MinFilter)

""" perform edge enhancement """
def edge_enhance(image, n):
  p('ENHANCE ')
  return image.filter( EdgeEnhanceFilter(n) )

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
