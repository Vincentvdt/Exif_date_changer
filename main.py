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
from collections import Counter
from datetime import datetime

import filedate
import pyinputplus as pyip
from exif import Image
from tqdm import tqdm

count = Counter()


def get_user_input(prompt):
    return True if pyip.inputYesNo(prompt=prompt) == "yes" else False


overwrite = get_user_input("Activate overwrite option ? [Y/n]")
rename = get_user_input("Rename file if exif date is found [Y/n]")
sort = get_user_input("Do you want to organize your pictures by years [Y/n]")
separate = get_user_input("Do you want to separate PNG pictures into an other folder ? [Y/n]")


SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
name_date_format = "%Y-%m-%d_%H-%M-%S"


source_folder = os.getcwd()
dir_name = os.path.basename(source_folder)
dist_folder = pyip.inputStr('Dossier de destination (Default: ' + dir_name + '):', blank=True)
if not dist_folder:
    dist_folder = dir_name

destination_folder = os.path.join(source_folder, dist_folder)


errors = []


def generate_date_time_formats():
    separators = ['-', '.', '_', '']
    _date_formats = [f"%Y{sep}%m{sep}%d" for sep in separators]
    _date_formats += [f"%d{sep}%m{sep}%Y" for sep in separators]

    time_formats = [f"%H{sep}%M{sep}%S" for sep in separators]
    date_time_formats = [f"{_date_format}{separator}{time_format}" for _date_format in _date_formats for separator in
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
        with open(file_name, "w") as _f:
            _f.write("\n".join(errors))

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
    errors.append(msg)


def check_extension(file):
    _, file_extension = os.path.splitext(file)
    try:
        if file_extension.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"{file} : Invalid file format. Supported formats: {SUPPORTED_EXTENSIONS}")
    except ValueError as e:
        update_counter(False)
        errors.append(str(e))


def copy_image_to_folder(source, img_destination_path):

    try:
        os.makedirs(os.path.dirname(img_destination_path), exist_ok=True)
        if os.path.exists(img_destination_path) and not overwrite:
            raise FileExistsError(f"'{os.path.basename(img_destination_path)}' "
                                  f"already exists at '{os.path.relpath(img_destination_path)}'.")
        shutil.copy2(source, img_destination_path)
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


def find_date_in_name(file):
    file_name, _ = os.path.splitext(file)
    regex_pattern = [
            r"(\d{4}[-._]\d{2}[-._]\d{2}[-._]\d{2}[-._]\d{2}[-._]\d{2})",
            r"(\d{2}[-._]\d{2}[-._]\d{4}[-._]\d{2}[-._]\d{2}[-._]\d{2})",
            r"(\d{4}[-._]\d{2}[-._]\d{2}[-._]\d{6})",
            r"(\d{2}[-._]\d{2}[-._]\d{4}[-._]\d{6})",
            r"(\d{8}[-._]\d{2}[-._]\d{2}[-._]\d{2})",
            r"(\d{8}[-._]\d{6})",
            r"(\d{4}[-._]\d{2}[-._]\d{2})",
            r"(\d{2}[-._]\d{2}[-._]\d{4})",
            r"(\d{14})",
            r"(\d{8})",
        ]
    for pattern in regex_pattern:
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


def create_folder(path):
    os.makedirs(path, exist_ok=True)


def process_no_exif_image(file):
    no_exif_folder = os.path.join(destination_folder, "NoExif")
    os.makedirs(no_exif_folder, exist_ok=True)
    date = find_date_in_name(file)
    if date:
        if sort:
            no_exif_folder = os.path.join(no_exif_folder, str(date.year))
            create_folder(no_exif_folder)

        img_destination_path = os.path.join(no_exif_folder, file)
        is_success = copy_image_to_folder(file, img_destination_path)
        change_created_date(date, img_destination_path)
    else:
        no_exif_and_date_folder = os.path.join(no_exif_folder, "NoDate")
        os.makedirs(no_exif_and_date_folder, exist_ok=True)
        img_destination_path = os.path.join(no_exif_and_date_folder, file)
        is_success = copy_image_to_folder(file, img_destination_path)
    return is_success


def process_exif_image(img):
    image, name, ext, date = img.values()
    _dist_folder = destination_folder
    if rename:
        name = f'{date.strftime(name_date_format)}_{name}{ext}'
    else:
        name = image

    if sort:
        _dist_folder = os.path.join(destination_folder, str(date.year))
        create_folder(_dist_folder)

    img_destination_path = os.path.join(_dist_folder, name)
    is_success = copy_image_to_folder(image, img_destination_path)
    change_created_date(date, img_destination_path)

    return is_success


def process_jpg_image(image):
    with open(image, 'rb'):
        img = Image(image)
        image_name, image_extension = os.path.splitext(image)
        if not img.has_exif or not hasattr(img, "datetime"):
            update_counter(process_no_exif_image(image))
        else:
            _date, _time = img.datetime.split(' ')
            img_exif_date = datetime.strptime(_date + ' ' + _time, "%Y:%m:%d %H:%M:%S")
            img = {
                "image": image,
                "name": image_name,
                "ext": image_extension,
                "date": img_exif_date
            }
            update_counter(process_exif_image(img))


def process_png_image(image):
    dst_folder = destination_folder
    date = find_date_in_name(image)

    if separate:
        dst_folder = os.path.join(dst_folder, "PngFiles")
        os.makedirs(dst_folder, exist_ok=True)

    if date and sort:
        dst_folder = os.path.join(dst_folder, str(date.year))
        os.makedirs(dst_folder, exist_ok=True)

    img_destination_path = os.path.join(dst_folder, image)
    update_counter(copy_image_to_folder(image, img_destination_path))

    if date:
        change_created_date(date, img_destination_path)


def exif_date_change():
    os.makedirs(destination_folder, exist_ok=True)
    files = [file for file in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, file))]
    if "Timekeeper.exe" in files:
        files.remove("Timekeeper.exe")
    pbar = tqdm(files, leave=True, smoothing=1)
    for file in pbar:
        pbar.set_description("Progress", refresh=True)
        pbar.set_postfix(file="{}".format(file))
        _, file_extension = os.path.splitext(file)
        check_extension(file)
        if file_extension.lower() in (".jpg", ".jpeg"):
            process_jpg_image(file)
        elif file_extension.lower() == '.png':
            process_png_image(file)
        else:
            continue

    print_final_count(count, destination_folder)


exif_date_change()
input("Press enter to proceed...")
