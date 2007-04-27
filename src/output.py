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


import os, sys, traceback

from common import *


########################################################## HTML OUTPUT


""" support for HTML output """
class HtmlOutput(BaseOutput):
  __plugin__ = 'html'

  """ generate an HTML table-of-contents """
  def toc_text(self, toc):
    current  = 0
    toc_text = ''
    toc_map  = self.toc_map

    for title_, level_, page_ in toc:
      title, level, page = title_.strip(), int(level_), int(page_)

      if not toc_map.has_key(page):
        continue

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
  def generate(self, toc):
    output = """
<html>
 <head>
  <title>%(title)s</title>
  <meta name="author"   content="%(author)s">
  <meta name="genre"    content="%(category)s">
  <meta name="category" content="%(category)s">
 </head>
 <body>
   <h1 align="center" style="page-break-after: always">%(title)s</h1>
   %(toc)s""" % dict(title=self.title, author=self.author,
                     category=self.category, toc=self.toc_text(toc))

    for i in range(self.n):
      name = IMAGENAME_SPEC % i
      output += '<p><a name="img%d"></a><img src="%s"/></p>\n' % (i, name)
    output += '</body></html>'
    write_file('ebook.html', output)

    return False


############################################################ RB OUTPUT


""" support for Rocket eBook (RB) output """
class RocketBookOutput(HtmlOutput):
  __plugin__ = 'rb'

  """ generate a rocket ebook """
  def generate(self, toc):

    HtmlOutput.generate(self, toc)

    if COMMANDS['rbmake']:
      p('\nCreating Rocket eBook ... ')
      call('rbmake', '-bei', '-Enone', '-o', 'ebook.rb', 'ebook.html')
      p('done.\n')

    return self.move_output('rb')


########################################################### IMP OUTPUT


""" support for IMP output """
class ImpOutput(HtmlOutput):

  """ generate a IMP for the specified device """
  def generate_imp(self, toc, device):

    HtmlOutput.generate(self, toc)

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

    except:
      print 'failed, error details follow.\n'
      traceback.print_exc(file=sys.stdout)

    return self.move_output('imp')


""" support for IMP output for the FullVga profile """
class FullVgaImpOutput(ImpOutput):
  __plugin__ = 'imp1'

  def generate(self, toc):
    return self.generate_imp(toc, 1)

""" support for IMP output for the HalfVga profile """
class HalfVgaImpOutput(ImpOutput):
  __plugin__ = 'imp2'

  def generate(self, toc):
    return self.generate_imp(toc, 2)


########################################################## BBEB OUTPUT


""" support for Sony BBeB output """
class LrfOutput(BaseOutput):
  __plugin__ = 'lrf'

  """ generate a LRF file """
  def generate(self, toc):
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
    toc_map = self.toc_map
    for title, level, page_ in toc:
      if toc_map.has_key(int(page_)):
        imagenum = toc_map[int(page_)]
        book.addTocEntry(title.strip(), images[imagenum])

    # generate the ebook
    book.renderLrf("ebook.lrf")

    p('done.\n')

    return self.move_output('lrf')
