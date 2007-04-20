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
class PdfInput(BaseInput):
  __plugin__ = 'pdf'

  """ initalise """
  def __init__(self, input, dpi, **args):
    self.input, self.dpi = os.path.abspath(input), dpi
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
      p('Unable to determine total number of pages in document\n')
      self.count = int(raw_input('Please enter number of pages: '))


  """ get a page from the PDF file """
  def get_page(self, n):

    p('RASTERIZE ')
    call('gs', '-q', '-dBATCH', '-dSAFER', '-dNOPAUSE', '-dDOINTERPOLATE',
         '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4', '-dUseCropBox',
         '-r%d' % self.dpi, '-dFirstPage=%d' % n, '-dLastPage=%d' % n,
         '-sDEVICE=pnggray', '-sOutputFile=page.png', self.input)

    if not os.path.exists('page.png'):
      return None

    return Image.open('page.png')


########################################################## DJVU INPUT


""" support for the DJVU format """
class DjvuInput(BaseInput):
  __plugin__ = 'djvu'

  """ initalise """
  def __init__(self, input, dpi, **args):
    self.input, self.dpi = os.path.abspath(input), dpi
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

