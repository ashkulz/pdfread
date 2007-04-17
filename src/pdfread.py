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
import input, output




class PdfConverter:

  ##############################################################################

  """ convert all pages to PNG images """
  def convert_pages_to_png(self):
    self.index        = 0
    self.angle        = ROTATION[self.options.rotate]
    self.page_mapping = {}

    for i in range(1, self.count+1):

      # map the current logical page to a image
      self.page_mapping[i] = self.index

      p('Page %4d/%d: %s', i, self.count, 'EXTRACT ')

      image = self.IN_FORMATS[self.options.in_format](self, i)
      if not image:
        p('BLANK\n')
        continue

      p('CROP ')

      bbox  = ImageChops.invert(image).getbbox()
      if bbox is None:
        p('BLANK\n')
        continue                          # probably a blank page
      cropped = image.crop(bbox)

      p('DILATE ')

      # perform image dilation
      dilated = cropped.filter(ImageFilter.MinFilter)
      imgH, imgV     = dilated.size
      ratioV, ratioH = float(self.options.vres)/imgV, float(self.options.hres)/imgH

      if not self.options.nosplit and ratioH < 2 and ratioV < 2:
        # split up the dilated image into multiple pages as per device resolution
        self.split_page(dilated)
      else:
        # size the page to the device resolution while keeping aspect ratio constant
        ratio  = min(ratioH, ratioV)
        size   = (int(imgH*ratio), int(imgV*ratio) )
        p('RESIZE ')
        self.save_page( dilated.resize(size, Image.ANTIALIAS) )

      p(' DONE\n')

    # cleanup
    if os.path.exists('page.eps'):
      os.remove('page.eps')

    if os.path.exists('page.png'):
      os.remove('page.png')

    if os.path.exists('page.pnm'):
      os.remove('page.pnm')

  """ split up the page into multiple physical pages in landscape mode """
  def split_page(self, page):
    p('RESIZE ')

    hres, vres, overlap = self.options.hres, self.options.vres, self.options.overlap

    # determine optimal vertical resolution and resize to it
    height = int(float(hres) / page.size[0] * page.size[1])
    final  = page.resize((hres, height), Image.ANTIALIAS)

    p('SPLIT ')

    # now chop up the final image based on the device vertical resolution
    completed = 0
    while completed + overlap < height:
      page = final.crop( (0, completed, hres, min(completed+vres, height)) )

      # rotate it if necessary
      if self.angle is not None:
        page = page.transpose(self.angle)

      # save the page
      self.save_page(page)

      # move the completed pixel count
      completed = completed + vres - overlap

  """ save the given page image (if it is not blank) and downsample if necessary """
  def save_page(self, page):
    hist = page.histogram()

    # check it's not a complete black or complete white page
    if sum(hist[:32]) > 10 and sum(hist[224:]) > 10:
      p('*')

      filename = IMAGENAME_SPEC % self.index

      if self.options.colors < 2:
        page.save(filename)
      else:
        # convert it to a grayscale image of given colors
        page.save('page.png')
        if self.options.colors == 2:
          call('convert', 'page.png', '-colorspace', 'GRAY',
                   '-monochrome', filename)
        else:
          call('convert', 'page.png', '-colorspace', 'GRAY',
                   '-colors', str(self.options.colors), filename)

        if not os.path.exists(filename):
          print '\nError! Image could not be downsampled.'
          sys.exit(1)

      if self.options.optimize:
        call('optipng', filename)

      self.index = self.index + 1


  ##############################################################################

  """ main function """
  def main(self):
    self.input, self.options, parser = parse_cmdline()
    self.check_commands()
    if self.options.colors >= 2 and not COMMANDS['convert']:
      parser.error('To use color downsampling, please install ImageMagick')
      sys.exit(1)

    self.get_meta_info()

    print "\nTemporary directory: ", self.options.tempdir, '\n'

    cwd = os.getcwd()
    os.chdir(self.options.tempdir)

    self.convert_pages_to_png()

    delete = self.OUT_FORMATS[self.options.out_format](self)

    os.chdir(cwd)

    if delete:
      shutil.rmtree(self.options.tempdir, True)
    else:
      print "\nOutput directory: ", self.options.tempdir, '\n'
      if sys.platform == 'win32':
        os.startfile(self.options.tempdir)

  ##############################################################################

  OUT_FORMATS = {
    'html' : generate_html,
    'rb'   : generate_rb,
    'lrf'  : generate_lrf,
    'imp2' : generate_imp2,
    'imp1' : generate_imp1
  }

  IN_FORMATS  = {
    'pdf'  : extract_pdf,
    'djvu' : extract_djvu,
  }


##############################################################################

def opt_help(list):
  return 'one of: ' + ', '.join(list) + ' (default: %default)'

""" parse the command line """
def parse_cmdline():
  profiles    = PROFILES.keys()
  out_formats = PdfConverter.OUT_FORMATS.keys()
  in_formats  = PdfConverter.IN_FORMATS.keys()

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
                    choices=out_formats, help=opt_help(out_formats))
  parser.add_option('-i', dest='in_format',  metavar='FORMAT',
                    choices=in_formats,  help=opt_help(in_formats))
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

  if options.profile_dump:
    if len(args) == 1:
      output = file(args[0], 'w')
    else:
      output = sys.stdout

    output.write("""
[config]
profiles=%s
in_formats=%s
out_formats=%s
rotation=%s
default_profile=%s
default_format=%s
dpi=%d
""" % ( '|'.join(profiles), '|'.join(in_formats), '|'.join(out_formats),
        '|'.join(ROTATION.keys()), DEFAULT_PROFILE, DEFAULT_INPUT_FORMAT,
        DEFAULT_DPI))

    for profile in PROFILES:
      output.write('\n[%s]\n' % profile)
      for key in PROFILES[profile]:
          if PROFILES[profile][key]:
              output.write('%s=%s\n' % (key, PROFILES[profile][key]))

    output.flush()
    output.close()
    sys.exit(0)

  if not len(args) == 1:
    parser.print_help()
    sys.exit(0)

  input = os.path.abspath(args[0])
  if not os.path.isfile(input):
    parser.error('The input PDF file does not exist')

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

  return input, options, parser

##############################################################################

if __name__ == '__main__':
  PdfConverter().main()
