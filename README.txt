Hello, and welcome to PDFRead v5. Please take a look at the platform and 
device specific notes before using this tool.

FEATURES
========

* support for PDF and DJVU documents
* works on Windows, Linux and OS X
* supports creating images for any ebook reader device
* out of the box profiles for the 1100/1150/1200 and PRS-500.
* fast and very accurate autocropping
* image dilation for more "thicker" text enabled by default
* automatically splitting into multiple pages for landscape mode
* generate image will fit the screen size exactly in potrait mode
* rotation of image for devices that don't support landscape mode
* option for reducing the number of colors to reduce image size
* output formats supported: currently html, rb, lrf, imp1, and imp2.


CHANGES IN v5
=============

* added this README
* add DJVU input support
* allow specifying custom options in the Windows GUI
* OS X support fixes (based on sammykrupa's input)
* tweaks in the EB-1150 and REB-1200 profile
* do not split page if the generated image width/height is less 
  than the device parameters. This caused too many blank pages
  to be created.

WINDOWS INSTALLATION AND USAGE
==============================

1. Download and install the PDFRead v5 installer.
2. Right-click a PDF, and choose PDFRead. Alternatively, use the start menu.
  (Start -> Programs -> PDFRead).
3. If you choose an output eBook, then that will be the generated file name.
   If you do not enter a filename, then it will be created in temp directory.
4. To customize a profile, check the "customize" box and specify parameters.
5. To uninstall, remove it from Add/Remove Programs.

LINUX INSTALLATION AND USAGE
============================

This assumes you have Ubuntu. If you don't, then install the equivalent 
packages for your distribution.

1. Open up a terminal window, and install the following packages:

   sudo apt-get install pdftk python-imaging xpdf-utils imagemagick gs-common djvulibre-bin

2. Download the PDFRead v5 source code and extract it somewhere.

3. The above directory will contain a command line program, execute it via
   
      python pdfread.py <options> pdf-file

4. Read the command line parameters description below.

OS X INSTALLATION AND USAGE
===========================

(based on sammykrupa's instructions)

1. Install Apple's developer tools from http://developer.apple.com/tools/

2. Install Python 2.5 or later from http://www.python.org/download/
   The Mac OS X installer application puts a big "MacPython 2.5" folder in your 
   applications folder. Go into that folder and double-click the 
   "Update Shell Profile.command" file.
   
3. Install fink from http://finkproject.org/

4. After fink is installed, type this into the Terminal application:

    sudo apt-get install xpdf imagemagick ghostscript ghostscript-fonts

5. Download the latest PIL source from http://www.pythonware.com/products/pil/

6. Extract the PIL source, and in the directory where you extracted run:

    sudo python setup.py install
    
7. Follow the linux instructions from point #2 onwards, as mentioned above.

8. In case you want to convert DJVU documents, please install djvulibre
   from either Fink or install it yourself.

REB1100 DEVICE NOTES
====================

* Use the reb1100 profile, which will always create images in landscape mode.
  You may have to switch the device to landscape mode.
  
* If you are on Linux or OS X, you may need to compile and install rbmake from 
  http://rbmake.sourceforge.net/

* Typical command line usage:
      pdfread -p reb1100 <pdf-file>

EBW1150 DEVICE NOTES
====================

* Use the eb1150 profile, which will always create images in landscape mode.
  You will have to hold the device sideways. Tip: you may want to enable
  "reverse paging" in settings, so that you can advance to the next page
  using the left button (which is normally the bottom one).

* If you are on Windows, please install eBook Publisher from 
      http://www.ebooktechnologies.com/support_publisher_download.htm
  
  Please uninstall and reinstall it if you already have it installed, as there
  may be problems if you have installed GEB Librarian after it.
  
* If you are on Linux or OS X, then an IMP file will not be created. You will
  have to create it by either copying the output directory to a Windows machine
  (real or virtual), and then creating an IMP with "ebook.html" in the above
  directory as the source.
  
  I recommend that you run Windows in VMWare or equivalent tools.
  
* Typical command line usage:
      pdfread -p eb1150 <pdf-file>


REB1200 DEVICE NOTES
====================

* This has not been tested, but it should work regardless. Some finetuning of 
  the device parameters may be required, as it is guesswork for now.
  
* This is very similiar to the ebw1150, so read the above notes. The profile
  to use is reb1200.
  
* Typical command line usage:
      pdfread -p reb1200 <pdf-file>

  
PRS-500 DEVICE NOTES
====================

* There are two profiles you can use: prs500 and prs500-l.
  The prs500 profile creates a typical LRF in potrait mode. The prs500-l
  profile rotates the PDF and creates it in landscape mode, which should
  result in much better legiblity at the expense of splitting up the page.

* Typical command line usage:
      pdfread -p prs500 <pdf-file>

  
COMMAND LINE OPTIONS
====================

Usage: pdfread [options] input-pdf

Options:
  -h, --help          show this help message and exit
  -p PROFILE          one of: eb1150, prs500, reb1200, reb1100, prs500-l
  -o OUTPUT           the output eBook filename
  -t TITLE            the title for the generated ebook
  -a AUTHOR           the author for the generated ebook
  -c CATEGORY         the category for the generated ebook
  -f FORMAT           one of: imp2, imp1, html, rb, lrf
  -i FORMAT           one of: pdf, djvu
  -d DIR              the temporary directory where images are generated
  --dpi=DPI           the DPI at which to perform dilation (default: 300)
  --autocontrast=N    normalize image contrast for N percent (default: 5)
  --gscrop            perform extra cropping using ghostscript
  --colors=N          downsample the output image to N grayscale colors
  --nosplit           do not split up pages
  --rotate=DIRECTION  one of: none, left, or right
  --pages=N           consider that the document has N pages
  --hres=HRES         the maximum usable horizontal resolution
  --vres=VRES         the maximum usable vertical resolution
  --overlap=OVERLAP   screen overlap between pages (in pixels)
  --help-profiles     show the various profile settings

DEFAULT PROFILE OPTIONS
=======================

Default options for the profile eb1150:
  rotate=left hres=445 format=imp2 vres=315 overlap=25 colors=16

Default options for the profile prs500:
  rotate=none hres=565 format=lrf vres=754 nosplit=1 colors=4

Default options for the profile reb1200:
  rotate=left hres=628 format=imp1 vres=464 overlap=25

Default options for the profile reb1100:
  rotate=none hres=472 format=rb vres=315 overlap=25

Default options for the profile prs500-l:
  rotate=left hres=754 format=lrf vres=565 overlap=25 colors=4

