# Convert Images: Smart Photo Organizer & Image Resizer

Many phones and cameras use different filenames to save photos. This program sorts all photos by date and renames them. Many images have very high resolution and take up a lot of space. This program was optimised for 10x15 cm prints with a DPI of 300, which is enough for a print photo to look good. When converting photos, you can reduce the file size by a factor of multiple.

## Features

– __Auto Sort__: Photos and videos are organized by date.
- __Bulk Rename__: Files are renamed by their date, ensuring consistent naming.
- __Optimized Resize__: Creates lower resolution copies suitable for sharing online and for high-quality 10x15 cm prints (300 DPI).
- __Secure Workflow__: Includes automatic backup of original files before processing.
- __Cross-platform__: Built for Windows with a simple executable, but the Python source code runs on any OS.
- __Flexible Interface__: Uses a simple command line interface.


## Get Started

### Windows Executable

1. Download the `convimg.exe` from the [build].
2. (Optional) For getting date from videos, install the ffmpeg.exe executable and add it to your system's PATH environment variable from [here](https://github.com/BtbN/FFmpeg-Builds/releases).
3. Run the program.

### From Source

1.  Clone the repository: `git clone https://github.com/dnarkevi/image-converter`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run the program: `python convimg.py`

## Code

Python 3.11 was used to create this program. External packages are listed as follows:

- [PIL](https://pypi.org/project/pillow/)
- [Exifread](https://pypi.org/project/ExifRead/)
- [Natsort](https://pypi.org/project/natsort/)
- [Ffmpeg-Python](https://pypi.org/project/ffmpeg-python/)
- [Fmpeg](https://github.com/BtbN/FFmpeg-Builds/releases)

