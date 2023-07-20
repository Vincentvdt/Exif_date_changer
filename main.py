# File name : main.py
# Name : Timekeeper
# Created by : Vincent Vidot
# Date created : January 29, 2023.
# Description : This script does something cool
#
# Special thanks to ChatGPT for providing helpful information and support during the development of this script


import os
import re
import shutil
import time
from collections import Counter
from datetime import datetime

import filedate
import pyinputplus as pyip
from exif import Image
from tqdm import tqdm

count = Counter()

overwrite = True if pyip.inputYesNo(prompt="Activate overwrite option ? [Y/n]") == "yes" else False
rename = True if pyip.inputYesNo(prompt="Rename file if exif date is found [Y/n]") == "yes" else False

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

errors = []


def generate_date_time_formats():
    separators = ['-', '.', '_', '']
    _date_formats = ["%Y{}%m{}%d".format(sep, sep) for sep in separators]
    _date_formats.append("%Y%m%d")
    time_formats = ["%H{}%M{}%S".format(sep, sep) for sep in separators]
    time_formats.append("%H%M%S")
    date_time_formats = [date_format + separator + time_format for date_format in _date_formats for separator in
                         separators for time_format in time_formats]
    date_time_formats += _date_formats
    return date_time_formats


date_formats = generate_date_time_formats()


def handle_errors():
    now = datetime.now()
    file_name = f"error_log_{now.year}-{now.month}-{now.day}.txt"
    display_error = "yes" if len(errors) <= 20 else pyip.inputYesNo(prompt="Do you want to display the errors despite "
                                                                           "the high number of them? [Y/n]")
    if display_error == "yes":
        for error in errors:
            print(f"    {error}")

    create_file = pyip.inputYesNo(prompt="Do you want to save the errors in a text file? [Y/n]")
    if create_file == "yes":
        with open(file_name, "w") as f:
            f.write("\n".join(errors))

        print(f"File created at {file_name} in {os.path.basename(source_folder)}!")


def print_final_count(counter, _destination_folder):
    success_count, error_count = counter.values()
    print("", end='\r')

    if success_count:
        print("\033[1;32m" + f'SUCCESS: {success_count} image{"s" if success_count != 1 else ""} processed '
                             f'successfully. Saved to \\{os.path.relpath(_destination_folder)} folder.' + "\033[0m")
    if error_count:
        print("\033[1;31m" + f'ERROR: {error_count} file{"s" if error_count != 1 else ""} encountered errors during '
                             f'processing : ' + "\033[0m")
        handle_errors()


def print_error_message(msg):
    msg = f"\033[1;31m{str(msg)}\033[0m"
    # print(msg)
    errors.append(msg)


def check_extension(file):
    file_name, file_extension = os.path.splitext(file)
    try:
        if file_extension.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"{file} : Invalid file format. Supported formats: {SUPPORTED_EXTENSIONS}")
    except ValueError as e:
        # print(e)
        update_counter(False)
        errors.append(str(e))


def copy_image_to_folder(source, destination_name):
    try:
        img_destination_path = os.path.join(destination_folder, destination_name)
        os.makedirs(os.path.dirname(img_destination_path), exist_ok=True)
        if os.path.exists(img_destination_path) and not overwrite:
            raise FileExistsError(f"'{os.path.basename(img_destination_path)}' "
                                  f"already exists at '{os.path.relpath(img_destination_path)}'.")
        shutil.copy2(source, img_destination_path)
        # print(f"The file '{os.path.basename(source)}' has been copied to "
        #       f"the directory '{os.path.dirname(img_destination_path)}'"
        #       f"{' BUT no date was found in the image name.' if no_date_found else '.'}")

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


def change_created_date(date, img_path):
    img = filedate.File(img_path)
    img.set(
        created=date.strftime("%Y-%m-%d %H:%M:%S"),
        modified=date.strftime("%Y-%m-%d %H:%M:%S")
    )


def update_counter(is_success: bool):
    count['success'] += is_success
    count['error'] += (1 - is_success)


def find_date_in_name(file, _regex_pattern: list = None):
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


def process_no_exif_image(file, dst_folder):
    no_exif_folder = os.path.join(dst_folder, "NoExif")
    os.makedirs(no_exif_folder, exist_ok=True)
    date = find_date_in_name(file)
    if date:
        img_destination_path = os.path.join(no_exif_folder, file)
        is_success = copy_image_to_folder(file, img_destination_path)
        change_created_date(date, img_destination_path)
    else:
        no_exif_and_date_folder = os.path.join(no_exif_folder, "NoDate")
        os.makedirs(no_exif_and_date_folder, exist_ok=True)
        img_destination_path = os.path.join(no_exif_and_date_folder, file)
        is_success = copy_image_to_folder(file, img_destination_path)
    return is_success


def process_exif_image(img, dst_folder):
    image, name, ext, date = img.values()
    if rename:
        name = f'{date.strftime(name_date_format)}_{name}{ext}'
    else:
        name = image

    is_success = copy_image_to_folder(image, name)
    img_destination_path = os.path.join(dst_folder, name)
    change_created_date(date, img_destination_path)

    return is_success


def process_jpg_image(image, dst_folder):
    with open(image, 'rb'):
        img = Image(image)
        image_name, image_extension = os.path.splitext(image)
        if not img.has_exif or not hasattr(img, "datetime"):
            update_counter(process_no_exif_image(image, dst_folder))
        else:
            _date, _time = img.datetime.split(' ')
            img_exif_date = datetime.strptime(_date + ' ' + _time, "%Y:%m:%d %H:%M:%S")
            img = {
                "image": image,
                "name": image_name,
                "ext": image_extension,
                "date": img_exif_date
            }
            update_counter(process_exif_image(img, dst_folder))


def process_png_image(image, dst_folder):
    png_folder = os.path.join(dst_folder, "PngFiles")
    os.makedirs(png_folder, exist_ok=True)
    date = find_date_in_name(image)
    img_destination_path = os.path.join(png_folder, image)
    if not date:
        update_counter(copy_image_to_folder(image, img_destination_path))
    elif date:
        update_counter(copy_image_to_folder(image, img_destination_path))
        change_created_date(date, img_destination_path)


def exif_date_change(src_folder, dst_folder):
    os.makedirs(dst_folder, exist_ok=True)
    files = [file for file in os.listdir(src_folder) if os.path.isfile(os.path.join(src_folder, file))]
    if "Timekeeper.exe" in files:
        files.remove("Timekeeper.exe")
    pbar = tqdm(files, leave=True, smoothing=1)
    for file in pbar:
        # time.sleep(0.05)
        # pbar.set_description("Processing file {}".format(file), refresh=True)
        pbar.set_description("Progress", refresh=True)
        pbar.set_postfix(file="{}".format(file))
        file_name, file_extension = os.path.splitext(file)
        check_extension(file)
        if file_extension.lower() in (".jpg", ".jpeg"):
            process_jpg_image(file, dst_folder)
        elif file_extension.lower() == '.png':
            process_png_image(file, dst_folder)
        else:
            continue

    print_final_count(count, destination_folder)


exif_date_change(source_folder, destination_folder)
input("Press enter to proceed...")
