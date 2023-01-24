import os
import re
import shutil
from collections import Counter
from datetime import datetime

import filedate
from exif import Image

count = Counter()

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png"]
current_folder = os.getcwd()
destination_folder = os.path.join(current_folder, "Pictures")
regex_pattern = [
    r"(^\d{4}[-._]\d{2}[-._]\d{2}(?:[-._]\d{2}[-._]\d{2}[-._]\d{2})?)",
    r"(^\d{4}[-._]\d{2}[-._]\d{2}(?:[-._]\d{6})?)",
    r"(^\d{8}(?:[-._]\d{2}[-._]\d{2}[-._]\d{2})?)",
    r"(^\d{8}(?:[-._]\d{6})?)",
    r"(\d{14})"
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


def print_final_count(counter):
    success_count, error_count = counter.values()
    print('\n')
    print(
        "\033[1;32m" + f'SUCCESS: {success_count} image{"s" if success_count != 1 else ""} have been processed and '
                       f'saved.' + "\033[0m")
    print(
        "\033[1;31m" + f'ERROR: {error_count} image{"s" if error_count != 1 else ""} already existed and were not '
                       f'overwritten.' + "\033[0m")


def extract_exif_date(file):
    with open(file, 'rb'):
        img = Image(file)
        if img.has_exif:
            date, time = img.datetime.split(' ')
            return datetime.strptime(date + ' ' + time, "%Y:%m:%d %H:%M:%S")
        else:
            return img.has_exif


def copy_image(source, destination_name, custom_success_message=None):
    try:
        destination = os.path.join(destination_folder, destination_name)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source, destination)
        if custom_success_message:
            print(custom_success_message)
        else:
            print(f"{f'SUCCESS: {destination} image have been processed and saved.'}")
        return True
    except Exception as e:
        print("\033[1;31m" + f"An error occurred: {e} " + "\033[0m")
        return False


def process_exif_image(img):
    name = f'{img["date"].strftime("%Y-%m-%d_%H-%M-%S")}_{img["name"]}{img["ext"]}'
    is_success = copy_image(img["file"], name)
    destination = os.path.join(destination_folder, name)
    change_created_date(destination, img["date"])
    return is_success


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
            r"(^\d{4}[-._]\d{2}[-._]\d{2}(?:[-._]\d{2}[-._]\d{2}[-._]\d{2})?)",
            r"(^\d{4}[-._]\d{2}[-._]\d{2}(?:[-._]\d{6})?)",
            r"(^\d{8}(?:[-._]\d{2}[-._]\d{2}[-._]\d{2})?)",
            r"(^\d{8}(?:[-._]\d{6})?)",
            r"(\d{14})"
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
            break


def exif_date_change(src_folder, dst_folder):
    date_formats = generate_date_time_formats()
    os.makedirs(dst_folder, exist_ok=True)
    for file in os.listdir(src_folder):
        file_name, file_extension = os.path.splitext(file)

        if file_extension.lower() not in SUPPORTED_FORMATS:
            continue

        if file_extension.lower() in (".jpg", ".jpeg"):
            with open(file, 'rb'):
                img = Image(file)
                if not img.has_exif:
                    no_exif_folder = os.path.join(dst_folder, "NoExif")
                    os.makedirs(no_exif_folder, exist_ok=True)
                    destination = os.path.join(no_exif_folder, file)
                    update_counter(copy_image(file, destination))
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
            if not date:
                message = f"{f'SUCCESS: {destination} image have been '}" \
                            f"processed and saved BUT no date was found in the image name."
                update_counter(copy_image(file, destination, message))

            elif date:
                update_counter(copy_image(file, destination))
                change_created_date(destination, date)
        else:
            continue

    print_final_count(count)


exif_date_change(current_folder, destination_folder)
