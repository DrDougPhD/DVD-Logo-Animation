import itertools
import pathlib
from typing import Tuple

from PIL import Image
from tqdm import tqdm


def move_southeast(x: int, y: int, velocity: int) -> Tuple[int, int]:
    return x + velocity, y + velocity


def move_northeast(x: int, y: int, velocity: int) -> Tuple[int, int]:
    return x + velocity, y - velocity


def move_northwest(x: int, y: int, velocity: int) -> Tuple[int, int]:
    return x - velocity, y - velocity


def move_southwest(x: int, y: int, velocity: int) -> Tuple[int, int]:
    return x - velocity, y + velocity


def passes_north_boundary(top_x: int, top_y: int, bottom_x: int, bottom_y: int, width: int, height: int, velocity: int) -> bool:
    return top_y - velocity < 0


def passes_west_boundary(top_x: int, top_y: int, bottom_x: int, bottom_y: int, width: int, height: int, velocity: int) -> bool:
    return top_x - velocity < 0


def passes_south_boundary(top_x: int, top_y: int, bottom_x: int, bottom_y: int, width: int, height: int, velocity: int) -> bool:
    return bottom_x + velocity > width


def passes_east_boundary(top_x: int, top_y: int, bottom_x: int, bottom_y: int, width: int, height: int, velocity: int) -> bool:
    return bottom_y + velocity > height


move_functions = itertools.cycle([move_southeast, move_northeast, move_northwest, move_southwest])
passes_boundary_functions = itertools.cycle([
    (passes_south_boundary, passes_east_boundary),
    (passes_north_boundary, passes_east_boundary),
    (passes_north_boundary, passes_west_boundary),
    (passes_south_boundary, passes_west_boundary)
])


def main():
    logo_image_path = './logo.png'
    logo_image = Image.open(logo_image_path)

    fps = 60
    duration = 1  # seconds
    frames_to_generate = duration * fps

    velocity = 20

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
    
    output_directory = pathlib.Path('./output')
    output_directory.mkdir(exist_ok=True, parents=True)

    digits = len(str(frames_to_generate))

    current_move_function = next(move_functions)
    current_boundary_function = next(passes_boundary_functions)

    progress = tqdm(total=frames_to_generate, desc='Image Rendering')
    for index in range(frames_to_generate):
        progress.update()

        current_frame = frame.copy()
        current_frame.paste(
            logo_image,
            (paste_x, paste_y)
        )

        for boundary_function in current_boundary_function:
            if boundary_function(top_x=paste_x, top_y=paste_y, bottom_x=paste_x + width, bottom_y=paste_y + height, width=resolution[0], height=resolution[1], velocity=velocity):
                current_boundary_function = next(passes_boundary_functions)
                current_move_function = next(move_functions)
                break

        paste_x, paste_y = current_move_function(x=paste_x, y=paste_y, velocity=velocity)

        frame_filename = str(index).zfill(digits)
        current_frame.save(output_directory / f'{frame_filename}.png')


if __name__ == '__main__':
    main()
