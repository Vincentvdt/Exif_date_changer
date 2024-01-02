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
    try:
        exif_data = picture.getexif()
        date = exif_data.get(306)
        if date and date != '0000:00:00 00:00:00':
            return datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
        else:
            return None
    except Exception as exif_error:
        logging.error(f"[{picture.name}] Error extracting EXIF data: {exif_error}")
        return None


def change_created_date(img_path, date):
    if date:
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        try:
            img = filedate.File(img_path)
            img.set(created=date_str, modified=date_str)
        except Exception as filedate_error:
            logging.error(f"[{img_path.name}] Error setting file dates: {filedate_error}")


def create_copy(source_file):
    relative_path = source_file.relative_to(SOURCE_FOLDER_PATH)
    dest_file = Path(DEST_FOLDER_PATH, relative_path)
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source_file, dest_file)
        return dest_file
    except Exception as copy_error:
        logging.error(f"[{source_file.name}] Error copying file: {copy_error}")
        return None


def generate_date_time_formats():
    separators = ['-', '.', '_', '']
    dates = [f"%Y{sep}%m{sep}%d" for sep in separators] + [f"%d{sep}%m{sep}%Y" for sep in separators]
    times = [f"%H{sep}%M{sep}%S" for sep in separators]
    return [f"{_date_format}{separator}{time_format}" for _date_format in dates
            for separator in separators for time_format in times] + dates


date_formats = generate_date_time_formats()


def find_date_in_name(picture):
    name = picture.stem
    regex_patterns = [
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

    for pattern in regex_patterns:
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
    return None


def main():
    pictures = get_all_pictures(SOURCE_FOLDER_PATH)
    with tqdm(pictures, leave=True, smoothing=1) as pbar:
        for picture in pbar:
            pbar.set_description("Progress", refresh=True)
            pbar.set_postfix(file="{}".format(picture))
            try:
                with Image.open(picture) as image:
                    date = get_exif_date(image) or find_date_in_name(picture)
                    if date is None:
                        logging.warning(f"[{picture.name}] Unable to determine creation date.")
                    new_picture = create_copy(picture)
                    if new_picture:
                        change_created_date(new_picture, date)
                    else:
                        logging.error(f"[{picture.name}] Skipping due to copy error.")
            except Exception as error:
                logging.error(f"[{picture.name}] An exception occurred: {error}")
                print(f"Error processing {picture.name}: {error}")


if __name__ == "__main__":
    main()
