import os
import PIL
from PIL import ImageFile
from io import BytesIO
from natsort import natsorted, index_natsorted, ns  # https://pypi.org/project/natsort/
import shutil
import ffmpeg  # https://pypi.org/project/ffmpeg-python/ https://github.com/BtbN/FFmpeg-Builds/releases
import exifread  # https://pypi.org/project/ExifRead/
import logging
import sys
import json

# Allows images to be opened with missing data.
ImageFile.LOAD_TRUNCATED_IMAGES = True
# Disabling error printing.
logging.getLogger('exifread').setLevel(logging.ERROR)

if hasattr(sys, "frozen"):
    APP_PATH = sys.executable
    LICENCE_PATH = os.path.join(sys._MEIPASS, "LICENSE")
else:
    APP_PATH = __file__
    LICENCE_DIR_PATH = os.path.split(APP_PATH)[0]
    LICENCE_PATH = os.path.join(LICENCE_DIR_PATH, "LICENSE")
APP_PATH = os.path.abspath(APP_PATH)
BASE_PATH = os.path.split(APP_PATH)[0]
CONFIG_PATH = os.path.join(BASE_PATH, "convimg_config.json")
FILE_BLACKLIST = (APP_PATH, CONFIG_PATH)

# These defaults are for photos 10x15 (cm) with DPI of 300.
# Exact photo size 102x152 (mm), which corresponds to optimal 1795x1205 resolution. Source: https://fotoprint.lt/informacija/rekomenduojama-failu-raiska/

default_config = {
    "QUALITY": 85,
    "LONG_SIDE": 1795,
    "SHORT_SIDE": 1205,
    "DPI": [300, 300],
    "BACKUP_PATH": "./BACKUP",
    "LOW_RES_PATH": "./LOWRES",
    "do_backup": True,
    "do_sort_filename": False,
    "do_sort_date": True,
    "use_date": True,
    "do_low_res": True
}

# Loading configuration file.
warning = ""
if os.path.isfile(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as file:
            config = json.load(file)
        # Validate types against default_config
        for key, value in default_config.items():
            if key in config:
                if not isinstance(config[key], type(value)):
                    warning = f"WARNING: Setting '{key}' has an invalid type in the configuration file. Falling back to default values:"
                    break
            else:
                warning = f"WARNING: Setting '{key}' is missing in the configuration file. Falling back to default values:"
                break
    except json.JSONDecodeError:
        warning = "WARNING: There is a syntax error in the configuration file. Falling back to default values:"
    if warning:
        print(warning)
        print("\n".join(f"{k}: {v}" for k, v in default_config.items()))
        input("Press Enter to continue ...")
        config = default_config
    else:
        # Filter out any rogue keys the user added to the JSON
        config = {key: config[key] for key in default_config}
else:
    with open(CONFIG_PATH, "w") as file:
        json.dump(default_config, file, indent=4)
    config = default_config

globals().update(config)

if len(sys.argv) == 1:
    pass
elif len(sys.argv) == 2:
    if os.path.isdir(sys.argv[1]):
        os.chdir(sys.argv[1])
    else:
        print("WARNING: Invalid directory path provided. Falling back to default directory path.")
        input("Press Enter to continue ...")
else:
    print("WARNING: Invalid arguments provided. Falling back to default directory path.")
    input("Press Enter to continue ...")


def clear():
    """Clears terminal for Windows (Linux and Mac unsupported)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def estimate_image_size(image):
    """Tells how much space an image will take."""
    with BytesIO() as buffer:
        image.save(buffer, "JPEG", quality=QUALITY, optimize=True, progressive=True, dpi=DPI)
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
            new_width = width
            new_height = height
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
                # Excluding this program when converting filenames.
                if not (os.path.abspath(path) in FILE_BLACKLIST):
                    path_list.append(path)
    else:
        for file in os.listdir(root):
            path = os.path.join(root, file)
            if os.path.isfile(path) and (not (os.path.abspath(path) in FILE_BLACKLIST)):
                path_list.append(path)
    return tuple(path_list)


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
            return None
        if date_taken != date_taken1 != date_taken2:
            print("Warning: video creation date metadata is wrong.")
            return None
        date_taken = date_taken.replace('T', ' ')[:19]
        return date_taken
    except (ffmpeg._run.Error, FileNotFoundError):
        print("To read video metadata, you must install the ffprobe.exe executable and add it to your system's PATH environment variable.")
        return None


def get_date(path):
    """Gets the date when media was created."""
    extension = os.path.splitext(path)[1].lower()
    if (extension in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".tif"}):
        return get_picture_date(path)
    elif (extension in {".mp4", ".mov", ".m4a"}):
        return get_video_date(path)
    else:
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


def gen_numerated_filenames(paths, prefixes=None):
    """Takes an array of paths and renames filenames to ascending numbers."""
    if prefixes is None:
        prefixes = [""] * len(paths)
    new_paths = []
    extensions = []
    for path, prefix in zip(paths, prefixes):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".jpeg":
            ext = ".jpg"
        extensions.append(ext)
        dir_path = os.path.split(path)[0]
        c = 1
        new_path = os.path.join(dir_path, '%s%03d' % (prefix, c))
        while new_path in new_paths:
            c += 1
            new_path = os.path.join(dir_path, '%s%03d' % (prefix, c))
        new_paths.append(new_path)
    new_paths = [path + ext for path, ext in zip(new_paths, extensions)]
    return new_paths


def gen_sorted_by_dates(paths, dates, include_date):
    """Sorts filenames by the dates. May include the date in a filename."""
    indices = index_natsorted(dates)
    dates = [dates[i].split()[0] + " " for i in indices]
    paths = [paths[i] for i in indices]
    if include_date:
        renamed_paths = gen_numerated_filenames(paths, dates)
    else:
        renamed_paths = gen_numerated_filenames(paths)
    return renamed_paths, paths


# Event loop.
while True:
    clear()
    print()
    print("~~~~~ Welcome to Convert Images photo file manager program! ~~~~~")
    print()
    print("Commands and current settings")
    print("w - Working directory:", os.getcwd())
    print("b - Create a backup:", tell_state(do_backup))
    print("f - Rename filenames numerically:", tell_state(do_sort_filename))
    print("d - Sort photos by date and rename filenames numerically:", tell_state(do_sort_date))
    print("u - Use date in a filename:", tell_state(use_date))
    print("r - Create lower resolution copy:", tell_state(do_low_res))
    print("c - Start conversion")
    print("i - Show license")
    print("h - Help")
    print("e - Exit")
    print()
    command = input("").strip()
    if len(command) == 0:
        continue
    event = command[0].lower()
    value = command[1:].strip()
    if event == "e":
        clear()
        print("Thank you for using Convert Images program. Have a nice day!")
        input("Press Enter to continue ...")
        break

    if event == "h":
        clear()
        print("\
This program is designed to organize photos and videos, but all file types are accepted.\n\
Features:\n\
    * Extract media creation date from photos and videos.\n\
    * Sort photos and videos by date.\n\
    * Rename all file type filenames neatly in numerical format.\n\
    * Create optimal lower-resolution photos using Lanczos algorithm.\n\
    * Customize parameters in convimg_config.json.\n\
Usage:\n\
    * Type the flag (b, u, f, etc.) followed by 'Yes' or 'No' to change the parameter.\n\
    * Flags 'f - Rename filenames numerically' and 'd - Sort photos by date and rename filenames numerically' can never be 'Yes' together.\n\
    * Disable filename renaming by setting both 'f' and 'd' flags to 'No'. It is only useful for creating lower-resolution photos.\n\
    * Use date in a filename by changing 'u - Use date in a filename' to 'Yes', which requires the 'd' flag to be 'Yes'.\n\
    * Change working directory by launching from different location, by using 'w' flag in the program or by adding arguments:\n\
    convimg.exe [target_directory] OR python3 convimg.py [target_directory]\n\
")
        input("Press Enter to continue ...")

    if event == "i":
        clear()
        with open(LICENCE_PATH, 'r', encoding='utf-8') as file:
            print(file.read())
        input("Press Enter to continue ...")

    if event == "w":
        if os.path.isdir(value):
            os.chdir(value)
        else:
            print("Provided path is invalid. Make sure folder exists.")
            input("Press Enter to continue ...")

    if event == "b":
        do_backup = get_state(value, do_backup)
    
    if event == "f":
        do_sort_filename = get_state(value, do_sort_filename)
        if do_sort_date and do_sort_filename:
            do_sort_date = False
            use_date = False

    if event == "d":
        do_sort_date = get_state(value, do_sort_date)
        if do_sort_date and do_sort_filename:
            do_sort_filename = False
        if not do_sort_date:
            use_date = False

    if event == "u":
        if do_sort_date:
            use_date = get_state(value, use_date)

    if event == "r":
        do_low_res = get_state(value, do_low_res)


    if event == "c":  # Main conversion code.
        clear()
        if os.path.isdir(BACKUP_PATH):
            print(f"{BACKUP_PATH} folder already exists. Cannot convert, please remove it!")
            input("Press Enter to continue ...")
            continue
        if os.path.isdir(LOW_RES_PATH):
            print(f"{LOW_RES_PATH} folder already exists. Cannot convert, please remove it!")
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
        # Sorting like Windows sorting by name does.
        backup_paths = natsorted(backup_paths, alg=ns.IGNORECASE)
        if do_sort_date:
            dates = []
            paths_w_dates = []
            paths_wo_dates = []
            print("Finding the date in files ...")
            for path in backup_paths:
                date = get_date(path)
                if date is None:
                    paths_wo_dates.append(path)
                else:
                    dates.append(date)
                    paths_w_dates.append(path)
            print("Sorting files by date ...")
            new_paths, old_paths = gen_sorted_by_dates(paths_w_dates, dates, use_date)
            print("Generating filenames without date ...")
            new_paths = gen_numerated_filenames(paths_wo_dates) + new_paths
            new_paths = [rem_first_dir(path) for path in new_paths]
            old_paths =  paths_wo_dates + old_paths
        elif do_sort_filename:
            print("Generating filenames ...")
            new_paths = gen_numerated_filenames(backup_paths)
            new_paths = [rem_first_dir(path) for path in new_paths]
            old_paths = backup_paths
        else:
            new_paths = [rem_first_dir(path) for path in backup_paths]
            old_paths = backup_paths
            
        print("Renaming all files ...")
        for old_path, new_path in zip(old_paths, new_paths):
            print("Renaming %s -> %s ... " % (rem_first_dir(old_path), new_path), end='')
            shutil.copy(old_path, new_path)
            print("Done!")

        if do_low_res:
            print("Creating lower resolution photos in %s folder..." % LOW_RES_PATH)
            for path in new_paths:
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

