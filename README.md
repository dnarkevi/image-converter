# Convert Images: Smart Photo Organizer & Image Resizer

Many phones and cameras use different filenames to save photos. When friends send photos from an event in different formats, it becomes a total mess. This program sorts all photos and videos by date and renames them. Many images have very high resolution and take up a lot of space. This program optimizes photos to the desired resolution to make print photos look good enough. When converting photos, you can reduce the file size by several times.

## Features

* Extract media creation date from photos and videos.
* Sort photos and videos by date.
* Rename filenames of all file types neatly in numerical format.
* Create optimal lower-resolution photos using the Lanczos algorithm.
* Customize parameters in convimg_config.json.

## Get Started

### Windows Executable

1. Download the latest version of `convimg.exe` from the [releases page](https://github.com/dnarkevi/image-converter/releases).
2. (Optional) For getting date from videos, download and install the ffmpeg.exe executable from [here](https://github.com/BtbN/FFmpeg-Builds/releases) and add it to your system's PATH environment variable.
3. Run the program directly from File Explorer or from command line: `convimg [target_directory]`
4. Type `h` and press Enter to view the help menu.

### From Source

1. Clone the repository: `git clone https://github.com/dnarkevi/image-converter`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the program: `python convimg.py [target_directory]`
4. Type `h` and press Enter to view the help menu.

## Code

Python 3.11 was used to create this program. External packages are listed as follows:

- [PIL](https://pypi.org/project/pillow/)
- [Exifread](https://pypi.org/project/ExifRead/)
- [Natsort](https://pypi.org/project/natsort/)
- [Ffmpeg-Python](https://pypi.org/project/ffmpeg-python/)
- [ffmpeg.exe](https://github.com/BtbN/FFmpeg-Builds/releases) 

