import os
from PIL import Image

dates = [
    "2023_05_23.15_05_25",
    "2023_05_23-15_05_25",
    "2023_05_23_15_05_25",
    "2023-05-23.15_05_25",
    "2023-05-23-15_05_25",
    "2023-05-23_15_05_25",
    "2023.05.23.15_05_25",
    "2023.05.23-15_05_25",
    "2023.05.23_15_05_25",
    "2023_05_23.15.05.25",
    "2023_05_23-15.05.25",
    "2023_05_23_15.05.25",
    "2023-05-23.15.05.25",
    "2023-05-23-15.05.25",
    "2023-05-23_15.05.25",
    "2023.05.23.15.05.25",
    "2023.05.23-15.05.25",
    "2023.05.23_15.05.25",
    "2023_05_23.15-05-25",
    "2023_05_23-15-05-25",
    "2023_05_23_15-05-25",
    "2023-05-23.15-05-25",
    "2023-05-23-15-05-25",
    "2023-05-23_15-05-25",
    "2023.05.23.15-05-25",
    "2023.05.23-15-05-25",
    "2023.05.23_15-05-25",
    "2023-05-23_15-05-25",
    "2023-05-23.15-05-25",
    "2023-05-23-15-05-25",
    "2023-05-23_15.05.25",
    "2023-05-23.15.05.25",
    "2023-05-23-15.05.25",
    "2023-05-23_15_05_25",
    "2023-05-23.15_05_25",
    "2023-05-23-15_05_25",
    "2023_05_23_150525",
    "2023_05_23.150525",
    "2023_05_23-150525",
    "2023.05.23_150525",
    "2023.05.23.150525",
    "2023.05.23-150525",
    "2023-05-23_150525",
    "2023-05-23.150525",
    "2023-05-23-150525",
    "20230523",
    "20230523-150525",
    "20230523_150525",
    "20230523.150525",
    "20230523-15_05_25",
    "20230523_15_05_25",
    "20230523.15_05_25",
    "20230523-15-05-25",
    "20230523_15-05-25",
    "20230523.15-05-25",
    "20230523-15.05.25",
    "20230523_15.05.25",
    "20230523.15.05.25",
    "20230523150525",
    "2023_05_23",
    "2023.05.23",
    "2023-05-23"
]


def save_images(image_path, names):
    # Open the image file
    with Image.open(image_path) as img:
        # Iterate over the names in the list
        for name in names:
            # Create the new file name
            new_file_name = "{}{}".format(f'{name}-541841848', os.path.splitext(image_path)[1])
            # Save the image with the new file name
            img.save(new_file_name)
            print("Image saved as: {}".format(new_file_name))


# Example usage
save_images("img.png", dates)
