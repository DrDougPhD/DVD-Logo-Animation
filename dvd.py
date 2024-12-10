import collections
import dataclasses
import argparse
from collections.abc import Callable
import pathlib
import subprocess
from typing import Tuple

from PIL import Image
from tqdm import tqdm


@dataclasses.dataclass
class AbsoluteBoundingBox:
    left_x: int
    right_x: int
    top_y: int
    bottom_y: int

    @property
    def x(self):
        return self.left_x
    
    @property
    def y(self):
        return self.top_y

    @classmethod
    def from_origin(cls, x: int, y: int, width: int, height: int):
        return cls(
            left_x=x,
            top_y=y,
            right_x=(x + width),
            bottom_y=(y + height),
        )

    def __iadd__(self, delta: Tuple[int, int]):
        if delta[0] != 0:
            self.left_x += delta[0]
            self.right_x += delta[0]
        if delta[1] != 0:
            self.top_y += delta[1]
            self.bottom_y += delta[1]
        return self
    
    def __add__(self, delta: Tuple[int, int]):
        return AbsoluteBoundingBox(
            left_x=self.left_x + delta[0],
            right_x=self.right_x + delta[0],
            top_y=self.top_y + delta[1],
            bottom_y=self.bottom_y + delta[1],
        )


FrameResolution = collections.namedtuple(
    "FrameResolution", (
        "width",
        "height",
    )
)
VelocityFunction = Callable[[AbsoluteBoundingBox], AbsoluteBoundingBox]


def velocity_update(
        next_location_velocity: VelocityFunction,
        current_north_south_boundary_crossed: Callable,
        current_east_west_boundary_crossed: Callable,
        reverse_north_south_boundary_crossed: Callable,
        reverse_east_west_boundary_crossed: Callable,
        current_image_location: AbsoluteBoundingBox,
        frame_resolution: FrameResolution,
        velocity: int,
):
    new_location: AbsoluteBoundingBox = next_location_velocity(
        current_image_location=current_image_location,
        velocity=velocity,
    )

    north_boundary_delta = current_north_south_boundary_crossed(
        image_location=new_location,
        frame_resolution=frame_resolution,
    )
    east_boundary_delta = current_east_west_boundary_crossed(
        image_location=new_location,
        frame_resolution=frame_resolution,
    )

    new_velocity_keywords = dict(
        current_image_location=new_location,
    )

    if north_boundary_delta == 0 and east_boundary_delta == 0:
        return new_velocity_keywords
    
    new_location += (east_boundary_delta, north_boundary_delta)

    if north_boundary_delta != 0:
        # Crosses over North / South boundary, but not East / West boundary.
        # We need to head in the opposite vertical direction.
        new_velocity_keywords |= dict(
            current_north_south_boundary_crossed=reverse_north_south_boundary_crossed,
            reverse_north_south_boundary_crossed=current_north_south_boundary_crossed,
        )
        next_location_velocity = swaps[VERTICAL][next_location_velocity]
    
    if east_boundary_delta != 0:
        # Does not cross over North / South boundary, but does cross East / West boundary.
        # We need to head in the opposite horizontal direction.
        new_velocity_keywords |= dict(
            current_east_west_boundary_crossed=reverse_east_west_boundary_crossed,
            reverse_east_west_boundary_crossed=current_east_west_boundary_crossed,
            flip=True,
        )
        next_location_velocity = swaps[HORIZONTAL][next_location_velocity]
        
    # Reaching here means we crossed no boundaries, so keep in the same direction.
    new_velocity_keywords["next_location_velocity"] = next_location_velocity
    return new_velocity_keywords


def move_southeast(current_image_location: AbsoluteBoundingBox, velocity: int) -> Tuple[int, int]:
    return current_image_location + (velocity, velocity)


def move_northeast(current_image_location: AbsoluteBoundingBox, velocity: int) -> Tuple[int, int]:
    return current_image_location + (velocity, -velocity)


def move_northwest(current_image_location: AbsoluteBoundingBox, velocity: int) -> Tuple[int, int]:
    negative_velocity = -1 * velocity
    return current_image_location + (negative_velocity, negative_velocity)


def move_southwest(current_image_location: AbsoluteBoundingBox, velocity: int) -> Tuple[int, int]:
    return current_image_location + (-velocity, velocity)


def passes_north_boundary(image_location: AbsoluteBoundingBox, frame_resolution: FrameResolution) -> bool:
    if image_location.top_y < 0:
        return image_location.top_y
    return 0


def passes_west_boundary(image_location: AbsoluteBoundingBox, frame_resolution: FrameResolution) -> bool:
    if image_location.left_x < 0:
        return image_location.left_x
    return 0


def passes_south_boundary(image_location: AbsoluteBoundingBox, frame_resolution: FrameResolution) -> bool:
    return min(0, frame_resolution.height - image_location.bottom_y)


def passes_east_boundary(image_location: AbsoluteBoundingBox, frame_resolution: FrameResolution) -> bool:
    return min(0, frame_resolution.width - image_location.right_x)


HORIZONTAL = 0
VERTICAL = 1

swaps = [{
    move_northeast: move_northwest,
    move_southeast: move_southwest,
    move_northwest: move_northeast,
    move_southwest: move_southeast,
}, {
    move_northeast: move_southeast,
    move_southeast: move_northeast,
    move_northwest: move_southwest,
    move_southwest: move_northwest,
}]


def main(args):
    logo_image = Image.open(args.logo)
    resolution = FrameResolution(width=3840, height=2160)
    frame = Image.new(
        mode='RGBA',
        size=resolution,
        color=0,
    )

    center_x = resolution[0] // 2
    center_y = resolution[1] // 2
    width, height = logo_image.size

    current_image_location = AbsoluteBoundingBox.from_origin(
        x=center_x - (width // 2),
        y=center_y - (height // 2),
        width=width,
        height=height,
    )

    frames_to_generate = args.duration * args.fps
    digits = len(str(frames_to_generate))

    output_directory = pathlib.Path(args.output_directory) / args.logo.with_suffix("").name
    print(f"Output to {output_directory}/")
    output_directory.mkdir(exist_ok=True, parents=True)

    # Get two flips in the center
    initial_frame = frame.copy()
    initial_frame.paste(
        logo_image,
        (current_image_location.x, current_image_location.y)
    )
    initial_frame.save(output_directory / 'left.png')

    initial_frame = frame.copy()
    initial_frame.paste(
        logo_image.transpose(Image.FLIP_LEFT_RIGHT),
        (current_image_location.x, current_image_location.y)
    )
    initial_frame.save(output_directory / 'right.png')

    keywords = dict(
        flip=True,
        next_location_velocity=move_southeast,
        velocity=args.velocity,
        current_north_south_boundary_crossed=passes_south_boundary,
        current_east_west_boundary_crossed=passes_east_boundary,
        reverse_north_south_boundary_crossed=passes_north_boundary,
        reverse_east_west_boundary_crossed=passes_west_boundary,
        frame_resolution=resolution,
        current_image_location=current_image_location,
    )

    progress = tqdm(total=frames_to_generate, desc='Goldfish Bowl!')
    for index in range(frames_to_generate):
        progress.update()

        if keywords.pop("flip", False):
            logo_image = logo_image.transpose(Image.FLIP_LEFT_RIGHT)
        
        current_frame = frame.copy()
        current_image_location = keywords["current_image_location"]
        current_frame.paste(
            logo_image,
            (current_image_location.x, current_image_location.y),
        )
        
        frame_filename = str(index).zfill(digits)
        current_frame.save(output_directory / f'{frame_filename}.png')

        # Update the x and y direction based on current direction and potential boundary collisions.
        keywords |= velocity_update(**keywords)
    
    subprocess.run([
        './stitch.sh',
        str(args.fps),
        str(output_directory / ('%0' + str(digits) + 'd.png')),
    ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='DVD Logo Bouncing',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        help='duration in seconds',
        default=40,
    )
    parser.add_argument(
        '--fps', '-f',
        type=int,
        help='frames per second',
        default=30,
    )
    parser.add_argument(
        '--velocity',
        type=int,
        help='change in x and y pixels each frame',
        default=10,  # 600,  # 4,
    )
    parser.add_argument(
        '--logo', '-i',
        type=pathlib.Path,
        help='logo to use',
        default="./input/goldfish-logo.png",
    )
    parser.add_argument(
        '--output-directory', '-o',
        type=pathlib.Path,
        help='directory to store generated frames',
        default="./output/",
    )
    main(args=parser.parse_args())
