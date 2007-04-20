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

import os, sys, subprocess, Image

########################################################### CONSTANTS

DEFAULT_PROFILE       = 'reb1100'
DEFAULT_INPUT_FORMAT  = 'pdf'
DEFAULT_DPI           = 300
DEFAULT_EDGE_ENHANCE  = 5
IMAGENAME_SPEC        = '%d.png'

########################################################### COMMANDS

COMMANDS = {
  'gs'      : False,
  'pdftk'   : False,
  'rbmake'  : False,
  'convert' : False,
  'pdfinfo' : False,
  'djvused' : False
}

########################################################### PROFILES

PROFILES = {
  'reb1100'   : {'hres': 315, 'vres':472, 'mode': 'landscape', 'overlap':25, 'rotate':'none', 'colors': 2,  'format': 'rb'  },
  'eb1150'    : {'hres': 315, 'vres':445, 'mode': 'landscape', 'overlap':25, 'rotate':'left', 'colors': 16, 'format': 'imp2'},
  'reb1200'   : {'hres': 455, 'vres':595, 'mode': 'landscape', 'overlap':25, 'rotate':'left', 'colors': 16, 'format': 'imp1'},
  'prs500-l'  : {'hres': 565, 'vres':754, 'mode': 'landscape', 'overlap':25, 'rotate':'left', 'colors': 4,  'format': 'lrf' },
  'reb1200-p' : {'hres': 455, 'vres':595, 'mode': 'potrait',   'overlap':0,  'rotate':'none', 'colors': 16, 'format': 'imp1'},
  'prs500'    : {'hres': 565, 'vres':754, 'mode': 'potrait',   'overlap':0,  'rotate':'none', 'colors': 4,  'format': 'lrf' }
}

ROTATION = {
  'none'  : None,
  'left'  : Image.ROTATE_90,
  'right' : Image.ROTATE_270
}

###################################################### BASE CLASSES

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
  def __init__(self, output, optimize, colors,
                      title, author, category, **args):
    self.n       = 0
    self.toc_map = {}

    self.colors, self.optimize, self.output = colors, optimize, output
    self.title, self.author, self.category  = title, author, category

  def add_page(self, page, images):
    p('SAVE ')
    self.toc_map[page] = self.n
    for image in images:
      hist = image.histogram()
      if sum(hist[:32]) < 10 or sum(hist[224:]) < 10:
        continue

      filename = IMAGENAME_SPEC % self.n
      if self.colors < 2:
        image.save(filename)
      else:
        self.downsample(image, filename)

      if self.optimize:
        call('optipng', filename)

      if os.path.exists(filename):
        self.n += 1

  def downsample(self, image, filename):
    image.save('colors.png')
    if self.colors == 2:
      call('convert', 'colors.png', '-colorspace', 'GRAY',
           '-monochrome', filename)
    else:
      call('convert', 'colors.png', '-colorspace', 'GRAY',
           '-colors', str(self.colors), filename)

    rm('colors.png')


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
