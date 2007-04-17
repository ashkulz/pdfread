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


##############################################################################

""" perform image cropping via whitespace detection at the borders """
class Crop(object):

  """ initialise """
  def __init__(self, e_crop, **args):
    self.enabled = e_crop

  """ execute """
  def __call__(self, images):
    if not self.enabled:
      return images

    output = []
    for image in images:
      bbox    = ImageChops.invert(image).getbbox()

      if bbox is None:
        output.append(None)
      else:
        output.append(image.crop(bbox))

    return output


##############################################################################

""" perform image dilation """
class Dilate(object):

  """ initialise """
  def __init__(self, e_dilate, **args):
    self.enabled = e_dilate

  """ execute """
  def __call__(self, images):
    if not self.enabled:
      return images

    output = []
    for image in images:
      output.append( image.filter(ImageFilter.MinFilter) )

    return output


##############################################################################

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
    kernel = [-phi/9.0] * 9
    kernel[4] = kernel[4] + 1.0

    self.filterargs = (3,3), omphi, 0.5, kernel


""" perform edge enhancement """
class EdgeEnhance(object):

  """ initialise """
  def __init__(self, e_edge, edge_n, **args):
    self.enabled, self.n = e_edge, edge_n

  """ execute """
  def __call__(self, images):
    if not self.enabled:
      return images

    output = []
    for image in images:
      output.append( image.filter( EdgeEnhanceFilter(self.n) ) )

    return output


##############################################################################


""" fit the image to the device size """
class FitDeviceSize(object):

  """ initialise """
  def __init__(self, hres, vres, **args):
    self.hres, self.vres = hres, vres

  """ execute """
  def __call__(self, images):
    output = []
    for image in images:
      # find the ratios
      imgH, imgV     = image.size
      ratioH, ratioV = float(self.hres)/imgH, float(self.vres)/imgV

      # select the lower ratio
      ratio  = min(ratioH, ratioV)
      size   = (math.ceil(imgH*ratio), math.ceil(imgV*ratio) )

      output.append( image.resize(size, Image.ANTIALIAS) )

    return output


##############################################################################


""" split the image """
class SplitLandscape(object):

  """ initialise """
  def __init__(self, hres, vres, **args):
    self.hres, self.vres = hres, vres

  """ execute """
  def __call__(self, images):
    output = []
    for image in images:
      # find the ratios
      imgH, imgV     = image.size
      ratioH, ratioV = float(self.hres)/imgH, float(self.vres)/imgV

      # select the lower ratio
      ratio  = min(ratioH, ratioV)
      size   = (math.ceil(imgH*ratio), math.ceil(imgV*ratio) )

      output.append( image.resize(size, Image.ANTIALIAS) )

    return output


