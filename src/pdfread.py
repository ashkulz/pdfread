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

DEFAULT_PROFILE      = 'reb1100'
DEFAULT_INPUT_FORMAT = 'pdf'
DEFAULT_DPI          = 300
DEFAULT_AUTOCONTRAST = 5

##############################################################################

import os, sys, re, subprocess, Image, ImageFilter, ImageChops, ImageOps, optparse, shutil, traceback

PROFILES = {
  'reb1100'   : {'hres': 472, 'vres':315, 'nosplit': 0, 'overlap':25, 'rotate':'none', 'colors': 0,  'format': 'rb'  },
  'eb1150'    : {'hres': 445, 'vres':315, 'nosplit': 0, 'overlap':25, 'rotate':'left', 'colors': 16, 'format': 'imp2'},
  'reb1200'   : {'hres': 595, 'vres':455, 'nosplit': 0, 'overlap':25, 'rotate':'left', 'colors': 0,  'format': 'imp1'},
  'prs500'    : {'hres': 565, 'vres':754, 'nosplit': 1, 'overlap':0,  'rotate':'none', 'colors': 4,  'format': 'lrf' },
  'prs500-l'  : {'hres': 754, 'vres':565, 'nosplit': 0, 'overlap':25, 'rotate':'left', 'colors': 4,  'format': 'lrf' }
}

ROTATION = {
  'none'  : None,
  'left'  : Image.ROTATE_90,
  'right' : Image.ROTATE_270
}

COMMANDS = {
  'gs'      : False,
  'pdftops' : False,
  'pdftk'   : False,
  'rbmake'  : False,
  'convert' : False,
  'pdfinfo' : False,
  'djvused' : False
}

IMAGENAME_SPEC = '%d.png'

class PdfConverter:

  ##############################################################################

  """ check for existence of command line tools """
  def check_commands(self):
    for command in COMMANDS.keys():
      try:
        exec_cmd(command)
        COMMANDS[command] = True
      except:
        pass

  """ get meta information from the input PDF """
  def get_meta_info(self):
    self.count = self.options.count
    self.toc   = []

    pdf  = (self.options.input_format == 'pdf')
    djvu = (self.options.input_format == 'djvu')

    if pdf and COMMANDS['pdftk']:
      data  = exec_cmd('pdftk', self.input, 'dump_data', 'output', '-')

      # get page count
      match = re.findall('NumberOfPages: (\d+)', data)
      if not self.count and match:
        self.count = int(match[0])

      # get TOC information
      self.toc = re.findall(r'BookmarkTitle:\s+(.*)\s+BookmarkLevel:\s+(\d+)\s+BookmarkPageNumber:\s+(\d+)', data)

    elif pdf and COMMANDS['pdfinfo']:
      data  = exec_cmd('pdfinfo', self.input)

      # get page count
      match = re.findall('Pages:\s+(\d+)', data)
      if not self.count and match:
        self.count = int(match[0])

    if djvu and COMMANDS['djvused']:
      data = exec_cmd('djvused', '-e', 'n', self.input).strip()
      if not self.count:
        self.count = int(data)

    if not self.count:
      print "Unable to determine total number of pages in document"
      self.count = int(raw_input("Please enter total page count: "))

  """ convert all pages to PNG images """
  def convert_pages_to_png(self):
    self.index        = 0
    self.angle        = ROTATION[self.options.rotate]
    self.page_mapping = {}

    for i in range(1, self.count+1):

      # map the current logical page to a image
      self.page_mapping[i] = self.index

      p('Page %4d/%d: %s', i, self.count, 'EXTRACT ')

      raw_image = self.INPUT_FORMATS[self.options.input_format](self, i)
      if not raw_image:
        p('BLANK\n')
        continue

      p('CROP ')

      image = ImageOps.autocontrast(raw_image, cutoff=self.options.cutoff)
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

      p('DONE\n')

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
      filename = IMAGENAME_SPEC % self.index

      if self.options.colors < 2:
        page.save(filename)
      else:
        # convert it to a grayscale image of given colors
        page.save('page.png')
        exec_cmd('convert', 'page.png', '-colorspace', 'GRAY',
                 '-colors', str(self.options.colors), filename)
        if not os.path.exists(filename):
          print '\nError! Image could not be downsampled.'
          sys.exit(1)

      self.index = self.index + 1




  ##############################################################################

  """ extract a PDF page and return the image location """
  def extract_pdf(self, number):

    # convert the current PDF page into a EPS file
    exec_cmd('pdftops', '-f', str(number), '-l', str(number), '-eps', self.input, 'page.eps')

    if self.options.gs_crop:
      p('GSCROP ')

      # find the crop box from GhostScript
      gs_box = exec_cmd('gs', '-q', '-dBATCH', '-dSAFER', '-dNOPAUSE', '-sDEVICE=bbox', 'page.eps')
      box    = re.findall('(%%HiResBoundingBox: .*)', gs_box)[0]

      # replace the newly detected crop box in the EPS file
      data = read_file('page.eps')
      data = re.sub('%%HiResBoundingBox: .*', '', re.sub('%%BoundingBox: .*', box, data))
      write_file('page.eps', data)

    p('RASTERIZE ')

    # rasterize to a high-res image with specified dpi
    exec_cmd('gs', '-q', '-dBATCH', '-dSAFER', '-dNOPAUSE', '-r%d' % self.options.dpi,
             '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4', '-dEPSFitPage', '-dEPSCrop',
             '-sDEVICE=pnggray', '-sOutputFile=page.png', 'page.eps')

    if not os.path.exists('page.png'):
      return None

    return Image.open('page.png')

  ##############################################################################

  """ extract a DJVU page and return the image location """
  def extract_djvu(self, number):
    p('RASTERIZE ')

    # only black & white mode supported for now
    exec_cmd('ddjvu', '-black', '-page', str(number), '-scale', str(self.options.dpi), self.input, 'page.pbm')

    if not os.path.exists('page.pbm'):
      return None

    return Image.open('page.pbm').convert('L')

  ##############################################################################

  """ generate an HTML table-of-contents """
  def generate_html_toc(self):
    current  = 0
    toc_text = ""
    for title, lvl, pg in self.toc:
      level, page = int(lvl), int(pg)
      if level > current:
        current = level
        toc_text = toc_text + (' ' * level) + '<ul>\n'
      elif current > level:
        current = level
        toc_text = toc_text + (' ' * current) + '</ul>\n'

      toc_text = toc_text + (' ' * level) + '<li><a href="#img%d">%s</a></li>\n' % (self.page_mapping[page], title.strip())

    while current > 0:
      toc_text = toc_text + (' ' * current) + '</ul>\n'
      current = current - 1

    return toc_text

  """ generate an HTML file """
  def generate_html(self):
    output = """
<html>
 <head>
  <title>%(title)s</title>
  <meta name="author"   content="%(author)s">
  <meta name="genre"    content="%(category)s">
  <meta name="category" content="%(category)s">
 </head>
 <body>
   %(toc)s""" % dict(title=self.options.title, author=self.options.author,
                     category=self.options.category, toc=self.generate_html_toc())

    for i in range(self.index):
      if os.path.exists(IMAGENAME_SPEC % i):
          output += '<p id="img%(i)d"><img src="%(src)s"/></p>\n' % dict(i=i, src=IMAGENAME_SPEC % (i))
    output += '</body></html>'
    write_file('ebook.html', output)

    return False

  ##############################################################################

  """ generate a Rocket eBook """
  def generate_rb(self):
    self.generate_html()

    if not COMMANDS['rbmake']:
      return

    p('\nCreating Rocket eBook ... ')
    exec_cmd('rbmake', '-beio', 'ebook.rb', 'ebook.html')
    p('done.\n')

    if self.options.output:
      shutil.move('ebook.rb', self.options.output)
      return True

    return False

  ##############################################################################

  """ generate a Sony BBeB """
  def generate_lrf(self):
    from pylrs.pylrs import Book, PageStyle, BlockStyle, ImageStream, BlockSpace, ImageBlock

    p('\nCreating BBeB file ... ')

    # create book instance
    book = Book(title=self.options.title, author=self.options.author,
                category=self.options.category)

    # create default styles
    pageStyle  = PageStyle(topmargin='0', oddsidemargin='0', evensidemargin='0')
    blockStyle = BlockStyle(blockwidth='600', blockheight='800')

    # create pages
    images = []
    for i in range(self.index):
      stream = ImageStream(IMAGENAME_SPEC % i)
      page   = book.Page(pageStyle)
      page.BlockSpace()
      image  = page.ImageBlock(refstream=stream, xsize='565', ysize='754',
                               blockheight='768', blockStyle=blockStyle)
      images.append(image)

    # generate TOC, if present
    for title, lvl, pg in self.toc:
      pgnum = self.page_mapping[int(pg)]
      book.addTocEntry(title.strip(), images[pgnum])

    # generate the ebook
    book.renderLrs("ebook.lrs")  # for debugging
    book.renderLrf("ebook.lrf")

    p('done.\n')
    if self.options.output:
      shutil.move('ebook.lrf', self.options.output)
      return True

    return False

  ##############################################################################

  def generate_imp(self, device):
    self.generate_html()

    if sys.platform == 'win32':
      p('\nCreating IMP file ... ')
      try:
        from win32com.client import Dispatch
        from win32com.client import gencache

        gencache.is_readonly = False
        gencache.EnsureModule('{1103EA00-3A0C-11D3-A6F6-00104B2947FB}', 0, 1, 0)

        builder = Dispatch('SBPublisher.Builder')
        project = Dispatch('SBPublisher.Project')
        project.NewUniqueID()

        project.AuthorFirstName = self.options.author
        project.BookTitle       = self.options.title
        project.Category        = self.options.category

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

        if self.options.output:
          shutil.move('ebook.imp', self.options.output)
          return True

      except:
        print 'failed, error details follow.\n'
        traceback.print_exc(file=sys.stdout)
    else:
      p('\nIMP creation disabled (works only on Windows).\n')

    return False

  def generate_imp1(self):
    return self.generate_imp(1)

  def generate_imp2(self):
    return self.generate_imp(2)

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

    delete = self.FORMATS[self.options.format](self)

    os.chdir(cwd)

    if delete:
      shutil.rmtree(self.options.tempdir, True)
    else:
      print "\nOutput directory: ", self.options.tempdir, '\n'
      if sys.platform == 'win32':
        os.startfile(self.options.tempdir)

  ##############################################################################

  FORMATS = {
    'html' : generate_html,
    'rb'   : generate_rb,
    'lrf'  : generate_lrf,
    'imp2' : generate_imp2,
    'imp1' : generate_imp1
  }

  INPUT_FORMATS  = {
    'pdf'  : extract_pdf,
    'djvu' : extract_djvu,
  }


##############################################################################

""" parse the command line """
def parse_cmdline():
  profiles      = PROFILES.keys()
  formats       = PdfConverter.FORMATS.keys()
  input_formats = PdfConverter.INPUT_FORMATS.keys()

  parser = optparse.OptionParser(usage='%prog [options] input-pdf')
  parser.add_option('-p', dest='profile', choices=profiles, default=DEFAULT_PROFILE,
                    help='one of: ' + ', '.join(profiles))
  parser.add_option('-o', dest='output', help='the output eBook filename')
  parser.add_option('-t', dest='title',    default='Unknown', help='the title for the generated ebook')
  parser.add_option('-a', dest='author',   default='Unknown', help='the author for the generated ebook')
  parser.add_option('-c', dest='category', default='General', help='the category for the generated ebook')
  parser.add_option('-f', dest='format', choices=formats,
                    help='one of: ' + ', '.join(formats))
  parser.add_option('-i', dest='input_format', choices=input_formats, default=DEFAULT_INPUT_FORMAT,
                    metavar='FORMAT', help='one of: ' + ', '.join(input_formats))
  parser.add_option('-d', dest='tempdir', metavar='DIR',
                    help='the temporary directory where images are generated')
  parser.add_option('--dpi', dest='dpi', type='int', default=DEFAULT_DPI,
                    help='the DPI at which to perform dilation (default: %d)' % DEFAULT_DPI)
  parser.add_option('--autocontrast', dest='cutoff', type='int', default=DEFAULT_AUTOCONTRAST,
                    metavar='N', help='normalize image contrast for N percent (default: %d)' % DEFAULT_AUTOCONTRAST)
  parser.add_option('--gscrop', dest='gs_crop', action='store_true', default=False,
                    help='perform extra cropping using ghostscript')
  parser.add_option('--colors', dest='colors', metavar='N', type='int', default=None,
                    help='downsample the output image to N grayscale colors')
  parser.add_option('--nosplit', dest='nosplit', action='store_const', default=None,
                    const=1, help='do not split up pages')
  parser.add_option('--rotate', dest='rotate', choices=ROTATION.keys(), metavar='DIRECTION',
                    help='one of: none, left, or right')
  parser.add_option('--pages', dest='count', type='int', default=None,
                    metavar='N', help='consider that the document has N pages')
  parser.add_option('--hres', dest='hres', type='int',
                    help='the maximum usable horizontal resolution')
  parser.add_option('--vres', dest='vres', type='int',
                    help='the maximum usable vertical resolution')
  parser.add_option('--overlap', dest='overlap', type='int',
                    help='screen overlap between pages (in pixels)')
  parser.add_option('--help-profiles', dest='profile_help', action='store_true', default=None,
                    help='show the various profile settings')
  parser.add_option('--dump-profiles', dest='profile_dump', action='store_true', default=None,
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
formats=%s
default_profile=%s
default_format=%s
dpi=%d
rotation=%s
autocontrast=%d
output_formats=%s
""" % ( '|'.join(profiles), '|'.join(input_formats), DEFAULT_PROFILE, DEFAULT_INPUT_FORMAT,
       DEFAULT_DPI, '|'.join(ROTATION.keys()), DEFAULT_AUTOCONTRAST, '|'.join(formats)))

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

  if not options.vres:
    options.vres    = PROFILES[options.profile]['vres']

  if not options.hres:
    options.hres    = PROFILES[options.profile]['hres']

  if not options.overlap:
    options.overlap = PROFILES[options.profile]['overlap']

  if not options.rotate:
    options.rotate  = PROFILES[options.profile]['rotate']

  if not options.colors:
    options.colors  = PROFILES[options.profile]['colors']

  if not options.format:
    options.format  = PROFILES[options.profile]['format']

  if options.nosplit is None:
    options.nosplit = PROFILES[options.profile]['nosplit']

  if not options.tempdir:
    import tempfile
    options.tempdir  = tempfile.mkdtemp(prefix='pdfread-')

  if options.output:
    options.output = os.path.abspath(options.output)

  return input, options, parser

##############################################################################

def read_file(name):
  f = open(name, 'rb')
  data = f.read()
  f.close()
  return data

def write_file(name, data):
  f = open(name, 'wb')
  f.write(data)
  f.close()

def exec_cmd(*args):
  process = subprocess.Popen(list(args), stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  process.stdin.close()
  data = process.stdout.read()
  process.wait()
  return data

def p(str, *args):
  sys.stdout.write(str % tuple(args))
  sys.stdout.flush()

##############################################################################

if __name__ == '__main__':
  PdfConverter().main()
