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


import os, re, glob, Image
from common import *

########################################################### PDF INPUT


PDFTK_COUNT   = re.compile(r'NumberOfPages: (\d+)')
PDFTK_TOC     = re.compile(r'BookmarkTitle:\s+(.*)\s+BookmarkLevel:\s+(\d+)\s+BookmarkPageNumber:\s+(\d+)')
PDFINFO_COUNT = re.compile(r'Pages:\s+(\d+)')
PDF_DEVICE    = { 'gray' : 'pnggray', 'rgb' : 'png16m' }

""" support for the PDF format """
class PdfInput(BaseInput):
  __plugin__ = 'pdf'

  """ initalise """
  def __init__(self, input, dpi, colorspace, no_toc, **args):
    self.input, self.dpi = input, dpi
    self.get_meta_info(no_toc)
    self.device = '-sDEVICE=%s' % PDF_DEVICE[colorspace]

  """ get meta information from the PDF file """
  def get_meta_info(self, no_toc=False):
    self.count   = 0
    self.toc     = []
    self.toc_map = {}

    if COMMANDS['pdftk']:
      data = call('pdftk', self.input, 'dump_data', 'output', '-')

      match = PDFTK_COUNT.search(data)
      if match:
        self.count = int(match.group(1))

      if not no_toc:
        self.toc = PDFTK_TOC.findall(data)

    elif COMMANDS['pdfinfo']:
      data  = call('pdfinfo', self.input)

      match = PDFINFO_COUNT.search(data)
      if match:
        self.count = int(match.group(1))

    # if nothing found, ask the user for the information
    if not self.count:
      p('Unable to determine total number of pages in document\n')
      self.count = int(raw_input('Please enter number of pages: '))


  """ get a page from the PDF file """
  def get_page(self, n):

    p('RASTERIZE ')
    call('gs', '-q', '-dBATCH', '-dSAFER', '-dNOPAUSE', '-dDOINTERPOLATE',
         '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4', '-dUseCropBox',
         '-r%d' % self.dpi, '-dFirstPage=%d' % n, '-dLastPage=%d' % n,
         self.device, '-sOutputFile=page.png', self.input)

    if not os.path.exists('page.png'):
      return None

    return Image.open('page.png')


########################################################## DJVU INPUT

DJVU_MODE = { 'gray' : 'black', 'rgb' : 'color' }

""" support for the DJVU format """
class DjvuInput(BaseInput):
  __plugin__ = 'djvu'

  """ initalise """
  def __init__(self, input, dpi, colorspace, **args):
    self.input, self.dpi = input, dpi
    self.get_meta_info()
    self.mode   = '-mode=%s' % DJVU_MODE[colorspace]
    self.immode = COLORSPACE[colorspace]

  """ get meta information from the document """
  def get_meta_info(self):
    self.count   = 0
    self.toc     = []
    self.toc_map = {}

    if COMMANDS['djvused']:
      self.count = int(call('djvused', '-e', 'n', self.input))

    # if nothing found, ask the user for the information
    if not self.count:
      p('Unable to determine total number of pages in document\n')
      self.count = int(raw_input('Please enter number of pages: '))


  """ get a page from the document """
  def get_page(self, n):

    call('ddjvu', self.mode, '-page', str(n), '-scale', str(self.dpi),
         self.input, 'page.pnm')

    if not os.path.exists('page.pnm'):
      return None

    return Image.open('page.pnm').convert(self.immode)

########################################################## TIFF INPUT


""" support for the TIFF format """
class TiffInput(BaseInput):
  __plugin__ = 'tiff'

  """ initalise """
  def __init__(self, input, dpi, colorspace, tempdir, **args):
    self.input, self.dpi = input, dpi
    self.get_meta_info(tempdir)
    self.immode = COLORSPACE[colorspace]

  """ get meta information from the document """
  def get_meta_info(self, tempdir):
    self.toc     = []
    self.toc_map = {}

    p('\nExtracting TIFF pages ... ')
    call('tiffcp', '-c', 'lzw', self.input,
          os.path.join(tempdir, 'page.tif'))

    call('tiffsplit', os.path.join(tempdir, 'page.tif'),
          os.path.join(tempdir, 'page_'))
    p('done.\n')

    self.files = glob.glob(os.path.join(tempdir, 'page_*.tif'))
    self.files.sort()
    self.count = len(self.files)


  """ get a page from the document """
  def get_page(self, n):
    if n < 1 or n > self.count:
      return None

    return Image.open(self.files[n-1]).convert(self.immode)


########################################################## LIST INPUT


""" support for a list of images """
class ImageListInput(BaseInput):
  __plugin__ = 'imglist'

  """ initalise """
  def __init__(self, input, colorspace, **args):
    self.input = input
    self.immode = COLORSPACE[colorspace]
    self.load_images()

  """ load the images from the list """
  def load_images(self):
    self.toc     = []
    self.toc_map = {}
    self.files   = []

    p('\nLoading images ... ')
    list = file(self.input, 'r')
    for name in list.readlines():
      if not name.strip():
        continue
      filename = os.path.abspath(name.strip())
      if filename and os.path.exists(filename):
        try:
          image = Image.open(filename).convert(self.immode)
          self.files.append(image)
        except:
          pass
    self.count = len(self.files)

    p('%d loaded.\n' % self.count)

  """ get a page from the document """
  def get_page(self, n):
    if n < 1 or n > self.count:
      return None

    return self.files[n-1]
