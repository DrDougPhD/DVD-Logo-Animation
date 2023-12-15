import pathlib

from PIL import Image


def main():
    logo_image_path = './logo.png'
    logo_image = Image.open(logo_image_path)

    resolution = 3840, 2160
    frame = Image.new(
        mode='RGBA',
        size=resolution,
        color=0
    )

    center_x = resolution[0] // 2
    center_y = resolution[1] // 2
    width, height = logo_image.size
    paste_x = center_x - (width // 2)
    paste_y = center_y - (height // 2)
    frame.paste(
        logo_image,
        (paste_x, paste_y)
    )

    output_directory = pathlib.Path('./output')
    output_directory.mkdir(exist_ok=True, parents=True)

    frame.save(output_directory / '00001.png')


if __name__ == '__main__':
    main()
