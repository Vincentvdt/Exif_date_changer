from pathlib import Path
from PIL import Image


import filedate
import shutil
from datetime import datetime

SOURCE_FOLDER_PATH = "Pictures"
DEST_FOLDER_PATH = "Dest"


def get_all_pictures(folder_path):
    folder_path = Path(folder_path)
    file_paths = []
    for file_path in folder_path.rglob("*.[jJnNgGpPeE][pPnNeEgG]*"):
        if file_path.is_file():
            file_paths.append(file_path)
    return file_paths


def get_exif_date(picture):
    exif_data = picture.getexif()
    date = exif_data.get(306)
    if date and date != '0000:00:00 00:00:00':
        return datetime.strptime(date, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    else:
        return None


def change_created_date(img_path, date):
    if date:
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


def handle_no_exif_date(picture):
    pass


def main():
    pictures = get_all_pictures(SOURCE_FOLDER_PATH)
    for picture in pictures:
        try:
            with Image.open(picture) as image:
                date = get_exif_date(image)
                new_picture = create_copy(picture)
                if date is not None:
                    change_created_date(new_picture, date)
                else:
                    handle_no_exif_date(image)
        except Exception as error:
            # handle the exception
            print("An exception occurred:", error)


if __name__ == "__main__":
    main()
