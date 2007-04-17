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


import os, re

from common import *


########################################################### PDF INPUT


PDFTK_COUNT   = re.compile(r'NumberOfPages: (\d+)')
PDFTK_TOC     = re.compile(r'BookmarkTitle:\s+(.*)\s+BookmarkLevel:\s+(\d+)\s+BookmarkPageNumber:\s+(\d+)')
PDFINFO_COUNT = re.compile(r'Pages:\s+(\d+)')


""" support for the PDF format """
class PdfInput(object):

  """ initalise """
  def __init__(self, input, dpi, gs_crop, **args):
    self.input, self.dpi, self.gs_crop = input, dpi, gs_crop
    self.get_meta_info()


  """ get meta information from the PDF file """
  def get_meta_info(self):
    self.count   = 0
    self.toc     = []
    self.toc_map = {}

    if COMMANDS['pdftk']:
      data = call('pdftk', self.input, 'dump_data', 'output', '-')

      match = PDFTK_COUNT.search(data)
      if match:
        self.count = int(match.group(1))

      self.toc = PDFTK_TOC.findall(data)

    elif COMMANDS['pdfinfo']:
      data  = call('pdfinfo', self.input)

      match = PDFINFO_COUNT.search(data)
      if match:
        self.count = int(match.group(1))

    # if nothing found, ask the user for the information
    if not self.count:
      p('Unable to determine total number of pages in document')
      self.count = int(raw_input('Please enter number of pages: '))


  """ get a page from the PDF file """
  def get_page(self, n):

    call('pdftops', '-f', str(n), '-l', str(n), '-eps',
         self.input, 'page.eps')

    if self.gs_crop:
      p('GSCROP ')

      # find the crop box from GhostScript
      gs_box = call('gs', '-q', '-dBATCH', '-dSAFER', '-dNOPAUSE',
                    '-sDEVICE=bbox', 'page.eps')
      box    = re.findall('(%%HiResBoundingBox: .*)', gs_box)[0]

      # replace the newly detected crop box in the EPS file
      data = read_file('page.eps')
      data = re.sub('%%HiResBoundingBox: .*', '',
                    re.sub('%%BoundingBox: .*', box, data))
      write_file('page.eps', data)

    p('RASTERIZE ')

    # rasterize to a high-res image with specified dpi
    call('gs', '-q', '-dBATCH', '-dSAFER', '-dNOPAUSE', '-r%d' % self.dpi,
         '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4', '-dEPSFitPage',
         '-dEPSCrop', '-sDEVICE=pnggray', '-sOutputFile=page.png',
         'page.eps')

    if not os.path.exists('page.png'):
      return None

    return Image.open('page.png')


########################################################## DJVU INPUT


""" support for the DJVU format """
class DjvuInput(object):

  """ initalise """
  def __init__(self, input, dpi, **args):
    self.input, self.dpi = input, dpi
    self.get_meta_info()


  """ get meta information from the PDF file """
  def get_meta_info(self):
    self.count   = 0
    self.toc     = []
    self.toc_map = {}

    if COMMANDS['djvused']:
      self.count = int(call('djvused', '-e', 'n', self.input))

    # if nothing found, ask the user for the information
    if not self.count:
      p('Unable to determine total number of pages in document')
      self.count = int(raw_input('Please enter number of pages: '))


  """ get a page from the DJVU file """
  def get_page(self, n):

    call('ddjvu', '-black', '-page', str(n), '-scale', str(self.dpi),
         self.input, 'page.pbm')

    if not os.path.exists('page.pbm'):
      return None

    return Image.open('page.pbm').convert('L')


########################################################### ALL


ALL = {
  'pdf'  : PdfInput,
  'djvu' : DjvuInput,
}