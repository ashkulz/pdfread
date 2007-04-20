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
IMAGENAME_SPEC        = '%d.png'

########################################################### COMMANDS

COMMANDS = {
  'gs'      : False,
  'pdftops' : False,
  'pdftk'   : False,
  'rbmake'  : False,
  'convert' : False,
  'pdfinfo' : False,
  'djvused' : False
}

########################################################### PROFILES

PROFILES = {
  'reb1100'   : {'hres': 315, 'vres':472, 'nosplit': 0, 'overlap':25, 'rotate':'none', 'colors': 0,  'format': 'rb'  },
  'eb1150'    : {'hres': 315, 'vres':445, 'nosplit': 0, 'overlap':25, 'rotate':'left', 'colors': 16, 'format': 'imp2'},
  'reb1200'   : {'hres': 455, 'vres':595, 'nosplit': 0, 'overlap':25, 'rotate':'left', 'colors': 0,  'format': 'imp1'},
  'prs500'    : {'hres': 565, 'vres':754, 'nosplit': 1, 'overlap':0,  'rotate':'none', 'colors': 4,  'format': 'lrf' },
  'prs500-l'  : {'hres': 565, 'vres':754, 'nosplit': 0, 'overlap':25, 'rotate':'left', 'colors': 4,  'format': 'lrf' }
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

""" superclass for all image transforms """
class BaseTransform(object):

  """ ignore all keyword arguments """
  def __init__(self, **args):
    pass

""" superclass for all output generators """
class BaseOutput(object):

  """ initalise """
  def __init__(self, n_, input_, title, author, category, output, **args):
    self.title, self.author, self.category = title, author, category
    self.n, self.input, self.output        = n_, input_, output

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
    if os.file.exists(file):
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

def p(str, *args):
  sys.stdout.write(str % tuple(args))
  sys.stdout.flush()

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
    print profile + ':\n ',
    for key in PROFILES[profile]:
        if PROFILES[profile][key]:
            print '%s=%s' % (key, PROFILES[profile][key]),
    print '\n'
