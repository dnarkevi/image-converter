import os
import PIL
from PIL import ImageFile
from io import BytesIO
from natsort import natsorted  # https://pypi.org/project/natsort/
import shutil
import ffmpeg  # https://pypi.org/project/ffmpeg-python/ https://github.com/BtbN/FFmpeg-Builds/releases
import exifread  # https://pypi.org/project/ExifRead/
import logging
import sys

# Allows images to be opened with misssing data.
ImageFile.LOAD_TRUNCATED_IMAGES = True
# Disabling error printing.
logging.getLogger('exifread').setLevel(logging.ERROR)

QUALITY = 85
# This is for photos 10x15 (cm) with DPI of 300.
# Exact photo size 102x152 (mm), which corresponds to 1795x1205 resolution. Source: https://fotoprint.lt/informacija/rekomenduojama-failu-raiska/
LONG_SIDE = 1795  
SHORT_SIDE = 1205
DPI = (300, 300)
# ROOT = os.path.split(__file__)[0]
BACKUP_PATH = "BACKUP"
LOW_RES_PATH = "LOWRES"
PROGRAM_DIR = os.path.split(__file__)[0]
EXE_PATH = os.path.abspath(sys.executable)
# print(PROGRAM_DIR, EXE_PATH)
# input()

input_dir_path = os.getcwd()
use_date = True
do_sort_date = True
do_backup = True
do_low_res = True

def clear():
    """Clears terminal for Windows (Linux and Mac unsupported)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def estimate_image_size(image):
    """Tells how much space will take an image."""
    with BytesIO() as buffer:
        image.save(buffer, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        return buffer.tell()


def resize_and_convert_photo(input_path, output_path):
    """Changes picture size, format and resolution and saves it."""
    with PIL.Image.open(input_path,) as img:
        img = img.convert('RGB')
        # Preserve image orientation
        try:
            for orientation in PIL.ExifTags.TAGS.keys():
                if PIL.ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img.getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
        # Cases where image doesn't have EXIF data or the orientation key is not found
        except (AttributeError, KeyError, IndexError) as e:
            print("%s " % e, end="")
        # Find which side will fit provided dimensions.
        width, height = img.size
        if width > height:
            target_width, target_height = LONG_SIDE, SHORT_SIDE
        else:
            target_width, target_height = SHORT_SIDE, LONG_SIDE

        if width < target_width or height < target_height:
            pass
        else:
            if width / target_width > height / target_height:
                scale = height / target_height
            else:
                scale = width / target_width
            new_width = int(width / scale)
            new_height = int(height / scale)
            # Resize the image with the best interpolation algorithm
            img = img.resize((new_width, new_height), PIL.Image.LANCZOS)
        # Save the image to the output path with high quality compression
        estimated_size = estimate_image_size(img)
        # Check if the original file is smaller than the estimated size
        original_size = os.path.getsize(input_path)
        if original_size < estimated_size:
            return False, ("", "")
        
        # img = img.filter(PIL.ImageFilter.GaussianBlur(0.5))
        img.save(output_path, "JPEG", quality=QUALITY, optimize=True, progressive=True, dpi=DPI)
        return True, ("%dx%d" % (width, height), "%dx%d" % (new_width, new_height))

def gen_file_paths(root, nested=True):
    """Generates tuple of paths of all files in the provided directory."""
    path_list = []
    if nested:
        for dir_path, dirs, files in os.walk(root):
            for file in files:
                path = os.path.join(dir_path, file)
                if os.path.abspath(path) != EXE_PATH:
                    path_list.append(path)
    else:
        for file in os.listdir(root):
            path = os.path.join(root, file)
            if os.path.isfile(path) and os.path.abspath(path) != EXE_PATH:
                path_list.append(path)
    return tuple(path_list)


#def load_config(dir_path)
#    path = os.path.join(dir_path, "config.txt")
#    if not os.path.exists(path):
#        raise FileNotFoundError("Config file does not exist")
#    with open(path, 'r') as file:
#        for line in file:
#            line = line.strip()
#            if line and ('=' in line):
#                key, value = line.split('=', 1)
#                # Dynamically set a global variable
#                globals()[key.strip()] = value.strip()
#
#
#def save_config(dir_path, key, value)
#    path = os.path.join(dir_path, "config.txt")
#    if not os.path.exists(path):
#        raise FileNotFoundError("Config file does not exist")
#    lines = []
#    with open(path, 'r') as file:
#        for line in file:
#            line = line.strip()
#            if line and ('=' in line):
#                seek_key, seek_value = line.split('=', 1)
#                if seek_key == key:
#                    seek_value = value

def tell_state(state):
    """Tells bool state in human language."""
    if state:
        return "Yes"
    else:
        return "No"


def get_state(value, init):
    """Returns bool from human language."""
    if value.lower().startswith("y"):
        return True
    elif value.lower().startswith("n"):
        return False
    else:
        clear()
        print("Provided value is invalid. You should write y or n.")
        input("Press Enter to continue ...")
        return init
        


def del_files(paths):
    """Deletes all files in the provided path list."""
    for path in paths:
        os.remove(path)


def rem_first_dir(path):
    """Removes first directory in provided path."""
    split_path = path.split(os.path.sep)[1:]
    if len(split_path) == 1:
        return split_path[0]
    elif len(split_path) == 0:
        print([split_path], [path])
        return split_path
    else:
        return os.path.join(*split_path)


def get_picture_date(path):
    """Gets the date when picture was taken."""
    with open(path, 'rb') as image_file:
        tags = exifread.process_file(image_file, details=False)
        # Check if the DateTimeOriginal tag is present
    if 'EXIF DateTimeOriginal' in tags:
        date_taken = str(tags['EXIF DateTimeOriginal'])
        date, time = date_taken.split()
        date = date.replace(':', '-')
        date_taken = " ".join((date, time))
        return date_taken
    else:
        return None


def get_video_date(path):
    """Gets the date when video was taken."""
    try:
        metadata = ffmpeg.probe(path)
        try:
            date_taken = metadata["format"]["tags"]["creation_time"]
            date_taken1 = metadata["streams"][0]["tags"]["creation_time"]
            date_taken2 = metadata["streams"][0]["tags"]["creation_time"]
        except Exception as e:
            print(e)
            return None
        if date_taken != date_taken1 != date_taken2:
            print("Warning: video creation date matadata is wrong.")
            return None
        date_taken = date_taken.replace('T', ' ')[:19]
        return date_taken
    except (ffmpeg._run.Error, FileNotFoundError):
        print("To read video metadata, you must install the ffprobe.exe executable and add it to your system's PATH environment variable.")
        return None


def join_paths(*path_input):
    """
    Combines strings and lists of path components into a new list of
    full paths, preserving the original order of all inputs.
    
    """
    string_index = []
    list_index = []
    list_length = 0
    for i, paths in enumerate(path_input):
        if isinstance(paths, (str, int)):
            string_index.append(i)
        elif isinstance(paths, (tuple, list)):
            list_index.append(i)
            list_length = len(paths)
        else:
            raise TypeError("Provided input type is incorrect.")
    for i in range(len(list_index)):
        if len(path_input[list_index[i]]) != list_length:
            raise ValueError("Provided lists must be same length.")
    path_output = []
    if list_length == 0:
        list_length = 1
    for i in range(list_length):
        new_path = ""
        for j in range(len(path_input)):
            if j in string_index:
                new_path = os.path.join(new_path, str(path_input[j]))
            elif j in list_index:
                new_path = os.path.join(new_path, path_input[j][i])
        path_output.append(os.path.normpath(new_path))
    return path_output

# Event loop.
while True:
    clear()
    print()
    print("~~~~~ Welcome to Convert Images photo file manager program! ~~~~~")
    print()
    print("Commands and current settings")
    print("w - Working directory:", input_dir_path)
    print("b - Create a backup:", tell_state(do_backup))
    print("s - Sort photos by date:", tell_state(do_sort_date))
    print("d - Date in a filename:", tell_state(use_date))
    print("r - Create lower resolution copy:", tell_state(do_low_res))
    print("c - Start converstion")
    print("h - Help")
    print("e - Exit")
    print()
    command = input("").strip()
    event = command[0].lower()
    value = command[1:].strip()
    if event == "e":
        clear()
        print("Thank you for using Convert Images program. Have a nice day!")
        input("Press Enter to continue ...")
        break

    if event == "h":
        clear()
        print(f"This program organizes photos by date, renames them, and saves them.\n\
You can create a backup of your original images before any modifications.\n\
Additionally, you can create a lower-resolution copy for optimal 10x15 cm prints,\n\
with a DPI of {DPI} and a resolution of {LONG_SIDE}x{SHORT_SIDE}.\n\
This program can also be used to number any files sequentially.\n\
This program can be added to your system's PATH environment variable.")
        input("Press Enter to continue ...")

    if event == "w":
        if os.path.isdir(value):
            input_dir_path = value
            os.chdir(input_dir_path)
        else:
            print("Provided path is invalid. Make sure folder exists.")
            input("Press Enter to continue ...")

    if event == "b":
        do_backup = get_state(value, do_backup)

    if event == "s":
        do_sort_date = get_state(value, do_sort_date)

    if event == "d":
        use_date = get_state(value, use_date)

    if event == "r":
        do_low_res = get_state(value, do_low_res)


    if event == "c":  # Main conversion code.
        clear()
        if os.path.isdir(BACKUP_PATH):
            print(f"{BACKUP_PATH} folder already exist. Cannot convert, please remove it!")
            input("Press Enter to continue ...")
            continue
        if os.path.isdir(LOW_RES_PATH):
            print(f"{LOW_RES_PATH} folder already exist. Cannot convert, please remove it!")
            input("Press Enter to continue ...")
            continue
        init_paths = gen_file_paths(".")
        if not init_paths:
            print("No files were detected in the provided directory.")
            input("Press Enter to continue ...")
            continue
        shutil.copytree(".", BACKUP_PATH)
        del_files(init_paths)
        backup_paths = join_paths(BACKUP_PATH, init_paths)

        # Findind all date creation of media.
        w_dates = {}
        wo_dates = []
        print("Finding the date in files ...")
        for path in backup_paths:  
            extension = os.path.splitext(path)[1].lower()
            if (extension in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".tif"}) and do_sort_date:
                date = get_picture_date(path)
            elif (extension in {".mp4", ".mov", ".m4a"}) and do_sort_date:
                date = get_video_date(path)
            else:
                date = None
            if date is None:
                wo_dates.append(path)
            else:
                c = 1
                date_new = date
                while date_new in w_dates:
                    date_new = date + str(c)
                    c += 1
                w_dates[date_new] = path

        # Sorting out all paths by the creation date.
        all_dates = set()
        sorted_paths = []
        sorted_filenames = []
        i = 1
        if do_sort_date:
            print("Sorting files by date ...")
            for key in natsorted(w_dates.keys()):
                date, time = key.split()
                # Checking if same the date already exist.
                if not (date in all_dates):
                    all_dates.add(date)
                    i = 1
                path = w_dates[key]
                ext = os.path.splitext(path)[1]
                filename = '%s %03d%s' % (date, i, ext)
                sorted_filenames.append(filename)
                sorted_paths.append(path)
               # print("From: %s To: %s" % (path, filename))
                i += 1
        if do_sort_date and wo_dates:
            print("Sorting other files ...")
        elif not do_sort_date:
            print("Sorting all files ...")
        i = 1
        for path in wo_dates:
            ext = os.path.splitext(path)[1]
            filename = '%03d%s' % (i, ext)
            sorted_filenames.append(filename)
            sorted_paths.append(path)
            i += 1
        # Renaming filenames, when not using date.
        if (not use_date) and do_sort_date:
            print("Generating filenames without dates ...")
            sorted_filenames = []
            i = 1
            for path in sorted_paths:
                ext = os.path.splitext(path)[1]
                filename = '%03d%s' % (i, ext)
                sorted_filenames.append(filename)
                i += 1
        # Creating new paths.
        sorted_new_paths = []
        for path, filename in zip(sorted_paths, sorted_filenames):
            new_path = rem_first_dir(path)
            new_path = os.path.split(new_path)[0]
            new_path = os.path.join(new_path, filename)
            sorted_new_paths.append(new_path)
        # Copying files back with renamed filenames.
        print("Renaming all files ...")
        for path, new_path in zip(sorted_paths, sorted_new_paths):
            print("Renaming %s -> %s ... " % (rem_first_dir(path), new_path), end='')
            shutil.copy(path, new_path)
            print("Done!")
        # This for loop block is not joined to ensure cleaner terminal output.
        if do_low_res:
            print("Creating lower resolution photos in %s folder..." % LOW_RES_PATH)
            for path in sorted_new_paths:
                low_res_path = os.path.join(LOW_RES_PATH, path)
                folder_path = os.path.split(low_res_path)[0]
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                extension = os.path.splitext(path)[1].lower()
                if extension in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".tif"}:
                    print("Converting %s ... " % path, end='')
                    try:
                        result, dims = resize_and_convert_photo(path, low_res_path)
                        if result:
                            print("Done! ", end='')
                            print("Resolution %s -> %s " % dims)
                        else:
                            print("Original image size is smaller. Copying ... ", end='')
                            shutil.copy(path, low_res_path)
                            print("Done!")
                    except PIL.UnidentifiedImageError:
                        print("Some errors encountered. Copying ... ", end='')
                        shutil.copy(path, low_res_path)
                        print("Done!")
                else:
                    print("Copying %s ... " % path, end='')
                    shutil.copy(path, low_res_path)
                    print("Done!")
        if not do_backup:
            shutil.rmtree(BACKUP_PATH)
        input("Press Enter to continue ...")

