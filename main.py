import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

import filedate
from PIL import Image, ImageFile
from tqdm import tqdm

ImageFile.LOAD_TRUNCATED_IMAGES = True
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

SOURCE_FOLDER_PATH = "Pictures"
DEST_FOLDER_PATH = "Dest"


def get_all_pictures(folder_path):
    folder_path = Path(folder_path)
    return [file_path for file_path in folder_path.rglob("*.[jJnNgGpPeE][pPnNeEgG]*") if file_path.is_file()]


def get_exif_date(picture):
    exif_data = picture.getexif()
    date = exif_data.get(306)
    if date and date != '0000:00:00 00:00:00':
        return datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
    else:
        return None


def change_created_date(img_path, date):
    if date:
        date = date.strftime("%Y-%m-%d %H:%M:%S")
        img = filedate.File(img_path)
        img.set(
            created=date,
            modified=date
        )


def create_copy(source_file):
    relative_path = source_file.relative_to(SOURCE_FOLDER_PATH)
    dest_file = Path(DEST_FOLDER_PATH, relative_path)
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, dest_file)
    return dest_file


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


def find_date_in_name(picture):
    name = picture.stem
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
    current_year = datetime.today().year

    for pattern in regex_pattern:
        match = re.search(pattern, name)
        if match:
            matched_string = match.group(1)
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(matched_string, date_format)
                    if 1900 <= parsed_date.year <= current_year:
                        return parsed_date
                except ValueError:
                    continue
        if not match:
            continue


def main():
    pictures = get_all_pictures(SOURCE_FOLDER_PATH)
    pbar = tqdm(pictures, leave=True, smoothing=1)
    for picture in pbar:
        pbar.set_description("Progress", refresh=True)
        pbar.set_postfix(file="{}".format(picture))
        try:
            with Image.open(picture) as image:
                date = get_exif_date(image)
                new_picture = create_copy(picture)
                if date is None:
                    date = find_date_in_name(new_picture)
                change_created_date(new_picture, date)
        except Exception as error:
            logging.error(f"[{picture.name}] An exception occurred: {error}")


if __name__ == "__main__":
    main()
