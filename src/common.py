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

import os, sys, shutil, subprocess, Image, ImageFilter

########################################################### CONSTANTS

DEFAULT_PROFILE       = 'reb1100'
DEFAULT_INPUT_FORMAT  = 'pdf'
DEFAULT_DPI           = 300
DEFAULT_EDGE_ENHANCE  = 5
DEFAULT_CROP_PERCENT  = 2.0
DEFAULT_COLORSPACE    = 'gray'
DEFAULT_OVERLAP_H     = 20
DEFAULT_OVERLAP_V     = 20
IMAGENAME_SPEC        = '%d.png'

########################################################### COMMANDS

COMMANDS = {
  'gs'        : False,
  'pdftk'     : False,
  'rbmake'    : False,
  'pngnq'     : False,
  'pdfinfo'   : False,
  'djvused'   : False,
  'tiffcp'    : False,
  'tiffsplit' : False
}

########################################################### PROFILES

PROFILES = {
  'reb1100'   : {'hres': 315, 'vres':472, 'mode': 'landscape', 'rotate':'none',  'colors': 0,  'format': 'rb'  },
  'eb1150'    : {'hres': 315, 'vres':445, 'mode': 'landscape', 'rotate':'left',  'colors': 16, 'format': 'imp2'},
  'reb1200'   : {'hres': 455, 'vres':595, 'mode': 'landscape', 'rotate':'left',  'colors': 16, 'format': 'imp1'},
  'reb1200-p' : {'hres': 455, 'vres':595, 'mode': 'portrait',  'rotate':'none',  'colors': 16, 'format': 'imp1'},
  'prs500-l'  : {'hres': 565, 'vres':754, 'mode': 'landscape', 'rotate':'right', 'colors': 4,  'format': 'lrf' },
  'prs500'    : {'hres': 565, 'vres':754, 'mode': 'portrait',  'rotate':'none',  'colors': 4,  'format': 'lrf' }
}

ROTATION = {
  'none'  : None,
  'left'  : Image.ROTATE_90,
  'right' : Image.ROTATE_270
}

COLORSPACE = { 
  'gray'  : 'L',
  'rgb'   : 'RGB'
}

###################################################### BASE CLASSES

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


""" superclass for all input formats """
class BaseInput(object):

  """ ignore all keyword arguments """
  def __init__(self, **args):
    pass

""" superclass for all image rendering modes """
class BaseMode(object):

  """ initialise """
  def __init__(self, hres, vres, **args):
    self.hres, self.vres = hres, vres

""" superclass for all output generators """
class BaseOutput(object):

  """ initalise """
  def __init__(self, output, optimize, colors, no_enhance,
               edge_level, title, author, category, **args):
    self.n       = 0
    self.toc_map = {}
    self.edge    = None

    self.colors, self.optimize, self.output = colors, optimize, output
    self.title, self.author, self.category  = title, author, category
    if not no_enhance and edge_level in range(1,10):
      self.edge = edge_level

  def add_page(self, page, images):
    p('SAVE ')
    self.toc_map[page] = self.n
    for image in images:
      if self.edge:
        image = image.filter( EdgeEnhanceFilter(self.edge) )

      hist = image.histogram()
      if sum(hist[:32]) < 10 or sum(hist[224:]) < 10:
        continue

      filename = IMAGENAME_SPEC % self.n
      if self.colors <= 2:
        image.save(filename)
      else:
        self.downsample(image, filename)

      if self.optimize:
        call('optipng', filename)

      if os.path.exists(filename):
        self.n += 1

  def downsample(self, image, filename):
    image.save('page.png')
    call('pngnq', '-fs', '1', '-n', str(self.colors), 'page.png')
    if os.path.exists('page-nq8.png'):
      os.rename('page-nq8.png', filename)

  def move_output(self, ext):
    fname = self.output

    if not fname or not os.path.exists('ebook.%s' % ext):
      return False

    if not fname.endswith(ext):
      fname += '.%s' % ext

    shutil.move('ebook.%s' % ext, fname)
    return True

########################################################### METHODS

def read_file(name):
  f = open(name, 'rb')
  data = f.read()
  f.close()
  return data

def write_file(name, data):
  f = open(name, 'wb')
  f.write(data)
  f.close()

def rm(*files):
  for file in files:
    if os.path.exists(file):
      os.remove(file)

def call(*args):
  process = subprocess.Popen(list(args),
                             stdin  = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.STDOUT)
  process.stdin.close()
  data = process.stdout.read()
  process.wait()
  return data

P_STREAM = sys.stdout
def p(str, *args):
  P_STREAM.write(str % tuple(args))
  P_STREAM.flush()

def check_commands():
  for command in COMMANDS.keys():
    try:
      call(command)
      COMMANDS[command] = True
    except:
      pass

def get_plugins(base_type):
  mapping = {}
  for type in base_type.__subclasses__():
    if hasattr(type, '__plugin__'):
      mapping[type.__plugin__] = type
      mapping.update( get_plugins(type) )
  return mapping

def profile_help():
  for profile in PROFILES:
    print '[%s]' % profile
    for key in PROFILES[profile]:
        if PROFILES[profile][key]:
            print '  %-8s = %s' % (key, PROFILES[profile][key])
    print '\n'
