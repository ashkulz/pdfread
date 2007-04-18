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

import os, sys, Image, ImageFilter, ImageChops, ImageOps, optparse


from common import *
from process import *
from input import *
from output import *

class PdfConverter:

  """ convert all pages to PNG images """
  def convert_pages_to_png(self, input, pipeline, output):
    for n in range(1, input.count+1):

      # map the current logical page to a image
      input.toc_map[n] = output.n

      p('Page %4d/%d: %s', n, input.count, 'EXTRACT ')

      image = input.get_page(n)
      if not image:
        p('BLANK\n')
        continue

      result = [image]
      for step in pipeline:
        result = step(result)
        if not result:
          break
        
      if not result:
        continue

      p('SAVE ')
      output(result)
      p('DONE\n')

    # cleanup
    for file in ['page.eps', 'page.png', 'page.pnm']:
      if os.path.exists(file):
        os.remove(file)

  ##############################################################################

  """ main function """
  def main(self):
    self.input, self.options, parser = parse_cmdline()
    if self.options.colors >= 2 and not COMMANDS['convert']:
      parser.error('To use color downsampling, please install ImageMagick')
      sys.exit(1)

    print "\nTemporary directory: ", self.options.tempdir, '\n'

    cwd = os.getcwd()
    os.chdir(self.options.tempdir)
    
    plugins = get_plugins(BaseTransform)
    stages = ['crop', 'dilate', 'split-landscape']
    pipeline = []
    for stage in stages:
      pipeline.append( plugins[stage](**self.options.__dict__) )
    
    save = SavePng(**self.options.__dict__)
    self.convert_pages_to_png(self.input, pipeline, save)

    output = get_plugins(BaseOutput)[self.options.out_format]
    
    delete = output(save.n, self.input, **self.options.__dict__).generate()

    os.chdir(cwd)

    if delete:
      shutil.rmtree(self.options.tempdir, True)
    else:
      print "\nOutput directory: ", self.options.tempdir, '\n'
      if sys.platform == 'win32':
        os.startfile(self.options.tempdir)


##############################################################################

def opt_help(list):
  return 'one of: ' + ', '.join(list) + ' (default: %default)'

""" parse the command line """
def parse_cmdline():
  profiles    = PROFILES.keys()
  out_formats = get_plugins(BaseOutput)
  in_formats  = get_plugins(BaseInput)

  parser = optparse.OptionParser(usage='%prog [options] input-pdf')

  parser.set_defaults(profile=DEFAULT_PROFILE, dpi=DEFAULT_DPI,
                      in_format=DEFAULT_INPUT_FORMAT, gs_crop=False,
                      title='Unknown', author='Unknown', category='General',
                      colors=None, nosplit=None, count=None,
                      profile_help=None, profile_dump=None)

  parser.add_option('-p', dest='profile', choices=profiles, help=opt_help(profiles))
  parser.add_option('-o', dest='output',   help='the output filename')
  parser.add_option('-t', dest='title',    help='generated ebook title (default: %default)')
  parser.add_option('-a', dest='author',   help='generated ebook author (default: %default)')
  parser.add_option('-c', dest='category', help='generated ebook category (default: %default)')
  parser.add_option('-f', dest='out_format', metavar='FORMAT',
                    choices=out_formats.keys(), help=opt_help(out_formats.keys()))
  parser.add_option('-i', dest='in_format',  metavar='FORMAT',
                    choices=in_formats.keys(),  help=opt_help(in_formats.keys()))
  parser.add_option('-d', dest='tempdir', metavar='DIR',
                    help='the temporary directory where images are generated')
  parser.add_option('--optimize', action='store_true', help='optimize generated PNG images (very slow!)')
  parser.add_option('--dpi', dest='dpi', type='int',
                    help='the DPI at which to perform dilation (default: %default)')
  parser.add_option('--gscrop', dest='gs_crop', action='store_true',
                    help='perform extra cropping using ghostscript (only for PDF)')
  parser.add_option('--colors', dest='colors', metavar='N', type='int',
                    help='downsample the output image to N grayscale colors')
  parser.add_option('--mono', dest='colors', action='store_const', const=2,
                    help='downsample the output image to monochrome')
  parser.add_option('--nosplit', dest='nosplit', action='store_const', const=1,
                    help='do not split up pages')
  parser.add_option('--rotate', dest='rotate', choices=ROTATION.keys(), metavar='DIRECTION',
                    help=opt_help(ROTATION.keys()))
  parser.add_option('--count', dest='count', type='int',
                    metavar='N', help='consider that the document has N pages')
  parser.add_option('--hres', dest='hres', type='int',       help='the maximum usable horizontal resolution')
  parser.add_option('--vres', dest='vres', type='int',       help='the maximum usable vertical resolution')
  parser.add_option('--overlap', dest='overlap', type='int', help='screen overlap between pages (in pixels)')
  parser.add_option('--help-profiles', dest='profile_help', action='store_true',
                    help='show the various profile settings')
  parser.add_option('--dump-profiles', dest='profile_dump', action='store_true',
                    help=optparse.SUPPRESS_HELP)

  (options, args) = parser.parse_args()

  if options.profile_help:
    for profile in PROFILES:
      print 'Default options for the profile %s:\n ' % profile,
      for key in PROFILES[profile]:
          if PROFILES[profile][key]:
              print '%s=%s' % (key, PROFILES[profile][key]),
      print '\n'
    sys.exit(0)

  if not len(args) == 1:
    parser.print_help()
    sys.exit(0)

  if options.vres is None:
    options.vres       = PROFILES[options.profile]['vres']

  if options.hres is None:
    options.hres       = PROFILES[options.profile]['hres']

  if options.overlap is None:
    options.overlap    = PROFILES[options.profile]['overlap']

  if options.rotate is None:
    options.rotate     = PROFILES[options.profile]['rotate']

  if options.colors is None:
    options.colors     = PROFILES[options.profile]['colors']

  if options.out_format is None:
    options.out_format  = PROFILES[options.profile]['format']

  if options.nosplit is None:
    options.nosplit    = PROFILES[options.profile]['nosplit']

  if not options.tempdir:
    import tempfile
    options.tempdir    = tempfile.mkdtemp(prefix='pdfread-')

  if options.output:
    options.output     = os.path.abspath(options.output)

  check_commands()
  inp = in_formats[options.in_format](os.path.abspath(args[0]), **options.__dict__)

  return inp, options, parser

##############################################################################

if __name__ == '__main__':
  PdfConverter().main()
