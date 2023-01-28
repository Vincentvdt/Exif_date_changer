# Name : Timekeeper
# Description : Keep your photos easily accessible and say goodbye to cluttered folders. "


import os
import re
import shutil
from collections import Counter
from datetime import datetime
import pyinputplus as pyip
import filedate
from exif import Image

count = Counter()
overwrite = pyip.inputYesNo(prompt="Do you want to activate the overwrite option : [Y/n]")

if overwrite == "yes":
    overwrite = True
elif overwrite == "no":
    overwrite = False

rename = pyip.inputYesNo(prompt="Dou you want to rename the file if a date is found in the exif data (only for .jpg "
                                "and .jpeg) [Y/n]")

if rename == "yes":
    rename = True
elif rename == "no":
    rename = False

SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
name_date_format = "%Y-%m-%d_%H-%M-%S"

source_folder = os.getcwd()
destination_folder = os.path.join(source_folder, "Pictures")
regex_pattern = [
    r"(\d{4}[-._]\d{2}[-._]\d{2}[-._]\d{2}[-._]\d{2}[-._]\d{2})",
    r"(\d{4}[-._]\d{2}[-._]\d{2}[-._]\d{6})",
    r"(\d{8}[-._]\d{2}[-._]\d{2}[-._]\d{2})",
    r"(\d{8}[-._]\d{6})",
    r"(\d{4}[-._]\d{2}[-._]\d{2})",
    r"(\d{14})"
    r"(\d{8})",
]


def generate_date_time_formats():
    separators = ['-', '.', '_', '']
    date_formats = ["%Y{}%m{}%d".format(sep, sep) for sep in separators]
    date_formats.append("%Y%m%d")
    time_formats = ["%H{}%M{}%S".format(sep, sep) for sep in separators]
    time_formats.append("%H%M%S")
    date_time_formats = [date_format + separator + time_format for date_format in date_formats for separator in
                         separators for time_format in time_formats]
    date_time_formats += date_formats
    return date_time_formats


def print_final_count(counter, _destination_folder):
    success_count, error_count = counter.values()
    print('\n')
    if success_count:
        print("\033[1;32m" + f'SUCCESS: {success_count} image{"s" if success_count != 1 else ""} have been processed '
                             f'and saved successfully to the folder '
                             f'\\{os.path.relpath(_destination_folder)}.' + "\033[0m")
    if error_count:
        print_error_message(
            f'ERROR: {error_count} image{"s" if error_count != 1 else ""} already existed and were not overwritten. '
            f'To overwrite the existing files, please enable the overwrite option in the user interface.')


def print_error_message(msg):
    print(f"\033[1;31m{str(msg)}\033[0m")


def copy_image_to_folder(source, destination_name, no_date_found=False):
    try:
        destination = os.path.join(destination_folder, destination_name)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        if os.path.exists(destination) and not overwrite:
            raise FileExistsError(f"'{os.path.basename(destination)}' "
                                  f"already exists at '{os.path.relpath(destination)}'.\n "
                                  f"To overwrite the file, please enable the 'overwrite' option in the user interface.")
        shutil.copy2(source, destination)
        print(f"The file '{os.path.basename(source)}' has been copied to the directory '{os.path.dirname(destination)}'"
              f"{' BUT no date was found in the image name.' if no_date_found else '.'}")

        return True
    except FileExistsError as e:
        print_error_message(e)
        return False
    except Exception as e:
        if "PermissionError" in str(e):
            print_error_message(f"An error occurred with '{source}': {e}.\nPlease check if you have the permission "
                                f"to access the destination folder.")
        elif "No such file or directory" in str(e):
            print_error_message(f"An error occurred with '{source}': {e}.\nPlease check if the source file path is "
                                f"correct.")
        else:
            print_error_message(f"An error occurred with '{source}': {e}")
        return False


def process_exif_image(img):
    if rename:
        name = f'{img["date"].strftime(name_date_format)}_{img["name"]}{img["ext"]}'
    else:
        name = img["file"]
    is_success = copy_image_to_folder(img["file"], name)
    destination = os.path.join(destination_folder, name)
    change_created_date(destination, img["date"])
    return is_success


def process_png_image(file, destination, date):
    if not date:
        update_counter(copy_image_to_folder(file, destination, True))
    elif date:
        update_counter(copy_image_to_folder(file, destination))
        change_created_date(destination, date)


def change_created_date(img_path, date):
    img = filedate.File(img_path)
    img.set(
        created=date.strftime("%Y-%m-%d %H:%M:%S"),
        modified=date.strftime("%Y-%m-%d %H:%M:%S")
    )


def update_counter(is_success: bool):
    count['success'] += is_success
    count['error'] += (1 - is_success)


def find_date_in_name(file, date_formats, _regex_pattern: list = None):
    file_name, file_extension = os.path.splitext(file)
    if _regex_pattern is None:
        _regex_pattern = [
            r"(\d{4}[-._]\d{2}[-._]\d{2}[-._]\d{2}[-._]\d{2}[-._]\d{2})",
            r"(\d{4}[-._]\d{2}[-._]\d{2}[-._]\d{6})",
            r"(\d{8}[-._]\d{2}[-._]\d{2}[-._]\d{2})",
            r"(\d{8}[-._]\d{6})",
            r"(\d{4}[-._]\d{2}[-._]\d{2})",
            r"(\d{14})"
            r"(\d{8})",
        ]
    for pattern in _regex_pattern:
        match = re.search(pattern, file_name)
        if match:
            matched_string = match.group(1)
            for date_format in date_formats:
                try:
                    return datetime.strptime(matched_string, date_format)
                except ValueError:
                    continue
        if not match:
            continue


def check_extension(file):
    file_name, file_extension = os.path.splitext(file)
    try:
        if file_extension.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"{file} : We don't support {f'the {file_extension}' if file_extension else 'this'} "
                             f"extension. Supported formats are {SUPPORTED_EXTENSIONS}")
    except ValueError as e:
        print(e)


def process_no_exif_image(file, dst_folder, date_formats):
    no_exif_folder = os.path.join(dst_folder, "NoExif")
    os.makedirs(no_exif_folder, exist_ok=True)
    date = find_date_in_name(file, date_formats)
    if date:
        destination = os.path.join(no_exif_folder, file)
        is_success = copy_image_to_folder(file, destination)
        change_created_date(destination, date)
    else:
        no_exif_and_date_folder = os.path.join(no_exif_folder, "NoDate")
        os.makedirs(no_exif_and_date_folder, exist_ok=True)
        destination = os.path.join(no_exif_and_date_folder, file)
        is_success = copy_image_to_folder(file, destination)
    return is_success


def exif_date_change(src_folder, dst_folder):
    date_formats = generate_date_time_formats()
    os.makedirs(dst_folder, exist_ok=True)
    files = [file for file in os.listdir(src_folder) if os.path.isfile(file) and '.' in os.path.basename(file)]
    file_count = len(files)
    print(file_count)
    for file in files:
        file_name, file_extension = os.path.splitext(file)
        check_extension(file)
        if file_extension.lower() in (".jpg", ".jpeg"):
            with open(file, 'rb'):
                img = Image(file)
                if not img.has_exif:
                    update_counter(process_no_exif_image(file, dst_folder, date_formats))
                else:
                    date, time = img.datetime.split(' ')
                    img_exif_date = datetime.strptime(date + ' ' + time, "%Y:%m:%d %H:%M:%S")
                    img = {
                        "file": file,
                        "name": file_name,
                        "ext": file_extension,
                        "date": img_exif_date
                    }
                    update_counter(process_exif_image(img))

        elif file_extension.lower() == '.png':
            png_folder = os.path.join(dst_folder, "PngFiles")
            os.makedirs(png_folder, exist_ok=True)

            date = find_date_in_name(file, date_formats)

            destination = os.path.join(png_folder, file)
            process_png_image(file, destination, date)
        else:
            continue

    print_final_count(count, destination_folder)


exif_date_change(source_folder, destination_folder)
input("Press enter to proceed...")
