#!/usr/bin/env python

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

##############################################################################

import os, sys, glob, optparse


from common  import *
from process import *
from input   import *
from output  import *

OUT_FORMATS = get_plugins(BaseOutput)
IN_FORMATS  = get_plugins(BaseInput)
MODES       = get_plugins(BaseMode)

def convert(pages, input, mode_tranform, output, crop_percent,
            unpaper_args=None, no_crop=False, no_dilate=False):

  for page in pages:
    p('Page %4d/%d: %s', page, input.count, 'EXTRACT ')

    image = input.get_page(page)
    if not image:
      p('BLANK\n')
      continue

    if unpaper_args:
      image = unpaper(image, unpaper_args)
      if not image:
        p('BLANK\n')
        continue

    if not no_crop:
      image = crop(image, crop_percent)
      if not image:
        p('BLANK\n')
        continue

    if not no_dilate:
      image = dilate(image)

    output.add_page(page, mode_tranform(image))
    p('DONE\n')

  # remove all temporary files
  for file in glob.glob('page*.*'):
    os.remove(file)

def main():
  input, output, mode, options, parser = parse_cmdline()

  first = options.first_page or 1
  last  = options.last_page  or input.count

  pages = range(first, last+1)

  print '\nTemporary directory: ', options.tempdir, '\n'

  cwd = os.getcwd()
  os.chdir(options.tempdir)

  convert(pages, input, mode, output, options.crop_percent,
          options.unpaper_args, options.no_crop, options.no_dilate)

  delete = output.generate(input.toc)
  os.chdir(cwd)

  if delete:
    shutil.rmtree(options.tempdir, True)
  else:
    print "\nOutput directory: ", options.tempdir, '\n'
    if sys.platform == 'win32':
      os.startfile(options.tempdir)

##############################################################################

def opt_help(list):
  return 'one of: ' + ', '.join(list)

""" parse the command line """
def parse_cmdline():
  profiles = PROFILES.keys()

  parser = optparse.OptionParser(usage='%prog [options] input-document')

  parser.set_defaults(profile=DEFAULT_PROFILE, in_format=DEFAULT_INPUT_FORMAT,
                      dpi=DEFAULT_DPI, colorspace=DEFAULT_COLORSPACE, 
                      edge_level=DEFAULT_EDGE_ENHANCE,
                      crop_percent=DEFAULT_CROP_PERCENT,
                      overlap_h=DEFAULT_OVERLAP_H, overlap_v=DEFAULT_OVERLAP_V,
                      title='Unknown', author='Unknown', category='General')

  parser.add_option('-p', dest='profile', choices=profiles, help=opt_help(profiles))
  parser.add_option('-o', dest='output',   help='the output filename')
  parser.add_option('-t', dest='title',    help='generated ebook title (default: "%default")')
  parser.add_option('-a', dest='author',   help='generated ebook author (default: "%default")')
  parser.add_option('-c', dest='category', help='generated ebook category (default: "%default")')
  parser.add_option('-f', dest='out_format', metavar='FORMAT',
                    choices=OUT_FORMATS.keys(), help=opt_help(OUT_FORMATS.keys()))
  parser.add_option('-i', dest='in_format',  metavar='FORMAT',
                    choices=IN_FORMATS.keys(),  help=opt_help(IN_FORMATS.keys()))
  parser.add_option('-m', dest='mode', choices=MODES.keys(), help=opt_help(MODES.keys()))
  parser.add_option('-u', metavar='ARGS', dest='unpaper_args',
                    help='command line arguments for unpaper')
  parser.add_option('-d', dest='tempdir', metavar='DIR',
                    help='the temporary directory where images are generated')
  parser.add_option('--first-page', metavar='PAGE', type='int', help='first page to convert')
  parser.add_option('--last-page', metavar='PAGE', type='int',  help='last page to convert')
  parser.add_option('--optimize', action='store_true', help='optimize generated PNG images')
  parser.add_option('--crop-percent', type='float', metavar='N%', help='whitespace cropping percentage (default: %default%)')
  parser.add_option('--edge-level', type='int', metavar='L', help='edge enhancement level from 1-9 (default: %default)')
  parser.add_option('--dpi', type='int',
                    help='the DPI at which to perform dilation (default: %default)')
  parser.add_option('--colors', metavar='N', type='int',
                    help='downsample the output image to N grayscale colors')
  parser.add_option('--colorspace', metavar='TYPE', choices=COLORSPACE.keys(),
                    help='the colorspace to use (default: %default)')
  parser.add_option('--mono', dest='colors', action='store_const', const=2,
                    help='downsample the output image to monochrome')
  parser.add_option('--rotate', choices=ROTATION.keys(), metavar='DIRECTION',
                    help=opt_help(ROTATION.keys()))
  parser.add_option('--count', type='int', metavar='N', help='consider that the document has N pages')
  parser.add_option('--hres', dest='hres', type='int',       help='the maximum usable horizontal resolution')
  parser.add_option('--vres', dest='vres', type='int',       help='the maximum usable vertical resolution')
  parser.add_option('--overlap-h', type='int', metavar='PIXELS', help='horizontal overlap between pages (default: %default)')
  parser.add_option('--overlap-v', type='int', metavar='PIXELS', help='vertical overlap between pages (default: %default)')
  parser.add_option('--no-crop',    action='store_true',   help='disable the cropping stage')
  parser.add_option('--no-dilate',  action='store_true',   help='disable the dilation stage')
  parser.add_option('--no-enhance', action='store_true',   help='disable the edge enhancement stage')
  parser.add_option('--no-toc',     action='store_true',   help='disable the generation of Table of Contents')
  parser.add_option('--list-profiles', dest='profile_help', action='store_true',
                    help='show the various profiles and their settings')

  (options, args) = parser.parse_args()

  if options.profile_help:
    profile_help()
    sys.exit(0)

  if not len(args) == 1:
    parser.print_help()
    sys.exit(0)

  if options.vres is None:
    options.vres       = PROFILES[options.profile]['vres']

  if options.hres is None:
    options.hres       = PROFILES[options.profile]['hres']

  if options.rotate is None:
    options.rotate     = PROFILES[options.profile]['rotate']

  if options.colors is None:
    options.colors     = PROFILES[options.profile]['colors']

  if options.out_format is None:
    options.out_format = PROFILES[options.profile]['format']

  if options.mode is None:
    options.mode       = PROFILES[options.profile]['mode']

  if not options.tempdir:
    import tempfile
    options.tempdir    = tempfile.mkdtemp(prefix='pdfread-')

  if options.output:
    options.output     = os.path.abspath(options.output)

  if not os.path.exists(args[0]) or not os.access(args[0], os.R_OK):
    parser.error('input document does not exist or cannot be opened')

  check_commands()

  opt = options.__dict__
  input  = IN_FORMATS[options.in_format](os.path.abspath(args[0]), **opt)
  output = OUT_FORMATS[options.out_format](**opt)
  mode   = MODES[options.mode](**opt)

  return input, output, mode, options, parser

##############################################################################

if __name__ == '__main__':
  main()
