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


import os, sys, shutil, traceback

from common import *


########################################################## BASE OUTPUT


""" superclass for all output generators """
class BaseOutput(object):

  """ initalise """
  def __init__(self, n_, input_, title, author, category, output, **args):
    self.title, self.author, self.category = title, author, category
    self.n, self.input, self.output        = n_, input_, output


########################################################## HTML OUTPUT


""" support for HTML output """
class HtmlOutput(BaseOutput):

  """ generate an HTML table-of-contents """
  def toc_text(self):
    current  = 0
    toc_text = ''
    toc_map  = self.input.toc_map

    for title_, level_, page_ in self.input.toc:
      title, level, page = title_.strip(), int(level_), int(page_)

      if level > current:
        current = level
        toc_text += '<ul>'
      elif current > level:
        current = level
        toc_text += '</ul>'

      toc_text += '<li><a href="#img%d">%s</a></li>' % (toc_map[page], title)

    while current > 0:
      toc_text += '</ul>'
      current  = current - 1

    return toc_text

  """ generate an HTML file """
  def generate(self):
    output = """
<html>
 <head>
  <title>%(title)s</title>
  <meta name="author"   content="%(author)s">
  <meta name="genre"    content="%(category)s">
  <meta name="category" content="%(category)s">
 </head>
 <body>
   <h1 align="center">%(title)s</h1>
   %(toc)s""" % dict(title=self.title, author=self.author,
                     category=self.category, toc=self.toc_text())

    for i in range(self.n):
      name = IMAGENAME_SPEC % i
      if os.path.exists(name):
        output += '<p><a name="img%d"></a><img src="%s"/></p>\n' % (i, name)
    output += '</body></html>'
    write_file('ebook.html', output)

    return False


############################################################ RB OUTPUT


""" support for Rocket eBook (RB) output """
class RocketBookOutput(HtmlOutput):

  """ generate a rocket ebook """
  def generate(self):

    HtmlOutput.generate(self)

    if COMMANDS['rbmake']:
      p('\nCreating Rocket eBook ... ')
      call('rbmake', '-beio', 'ebook.rb', 'ebook.html')
      p('done.\n')

      if self.output:
        shutil.move('ebook.rb', self.output)
        return True

    return False


########################################################### IMP OUTPUT


""" support for IMP output """
class ImpOutput(HtmlOutput):

  """ generate a IMP for the specified device """
  def generate_imp(self, device):

    HtmlOutput.generate(self)

    if sys.platform != 'win32':
      p('IMP creation disabled (works only on Windows).\n')
      return False

    p('\nCreating IMP file ... ')
    try:
      from win32com.client import Dispatch
      from win32com.client import gencache

      gencache.is_readonly = False
      gencache.EnsureModule('{1103EA00-3A0C-11D3-A6F6-00104B2947FB}', 0, 1, 0)

      builder = Dispatch('SBPublisher.Builder')
      project = Dispatch('SBPublisher.Project')

      project.AuthorFirstName = self.author
      project.BookTitle       = self.title
      project.Category        = self.category

      project.BookFileName    = 'ebook'
      project.OutputDirectory = '.'
      project.BuildTarget     = device
      project.Compress        = True
      project.Encrypt         = False
      project.KeepAnchors     = True
      project.Language        = 'en'
      project.RequireISBN     = False
      project.Zoom            = 2

      project.AddSourceFile('ebook.html')
      project.Save('ebook.opf')
      builder.Build(project)

      p('done.\n')

      if self.output:
        shutil.move('ebook.imp', self.output)
        return True

    except:
      print 'failed, error details follow.\n'
      traceback.print_exc(file=sys.stdout)

    return False

""" support for IMP output for the FullVga profile """
class FullVgaImpOutput(ImpOutput):

  def generate(self):
    self.generate_imp(1)

""" support for IMP output for the HalfVga profile """
class HalfVgaImpOutput(ImpOutput):

  def generate(self):
    self.generate_imp(2)


########################################################## BBEB OUTPUT


""" support for Sony BBeB output """
class LrfOutput(BaseOutput):

  """ generate a LRF file """
  def generate(self):
    from pylrs.pylrs import Book, PageStyle, BlockStyle
    from pylrs.pylrs import ImageStream, BlockSpace, ImageBlock

    p('\nCreating BBeB file ... ')

    # create book instance
    book = Book(title=self.title, author=self.author, category=self.category)

    # create default styles
    pageStyle  = PageStyle(topmargin='0', oddsidemargin='0', evensidemargin='0')
    blockStyle = BlockStyle(blockwidth='600', blockheight='800')

    # create pages
    images = []
    for i in range(self.n):
      stream = ImageStream(IMAGENAME_SPEC % i)
      page   = book.Page(pageStyle)
      page.BlockSpace()
      image  = page.ImageBlock(refstream=stream, xsize='565', ysize='754',
                               blockheight='768', blockStyle=blockStyle)
      images.append(image)

    # generate TOC, if present
    toc_map = self.input.toc_map
    for title, level, page_ in self.input.toc:
      imagenum = toc_map[int(page_)]
      book.addTocEntry(title.strip(), images[imagenum])

    # generate the ebook
    book.renderLrs("ebook.lrs")
    book.renderLrf("ebook.lrf")

    p('done.\n')
    if self.output:
      shutil.move('ebook.lrf', self.output)
      return True

    return False


########################################################### ALL


ALL = {
  'html' : HtmlOutput,
  'rb'   : RocketBookOutput,
  'lrf'  : LrfOutput,
  'imp2' : FullVgaImpOutput,
  'imp1' : HalfVgaImpOutput
}
