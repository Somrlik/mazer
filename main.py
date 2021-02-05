import argparse
import enum
import math
import os
import random
from typing import Tuple, Callable, Optional

from PIL import Image, ImageDraw

HASHING_CONSTANT: int = 50000


class CellState(enum.Enum):
    WALL = 2
    EMPTY = 3
    START = 50
    END = 100


def random_between(min_value: int, max_value: int) -> int:
    return math.floor(random.random() * (max_value - min_value)) + min_value


def get_char_for_state(state: CellState) -> str:
    if state == CellState.WALL:
        return '#' # u'\u2588'
    elif state == CellState.EMPTY:
        return '.'
    elif state == CellState.START:
        return '.'
    elif state == CellState.END:
        return '.'
    else:
        return '?'


class Point(object):
    x, y = 0, 0

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def is_in_maze(self, maze) -> bool:
        if 0 > self.x >= maze.width:
            return False
        if 0 > self.y >= maze.height:
            return False
        return True

    def __str__(self) -> str:
        return '[' + str(self.x) + ', ' + str(self.y) + ']'


class Maze(object):
    width: int
    height: int
    solvable: bool

    start_point: Point
    end_point: Point

    map: list

    def __init__(self, width: int, height: int, solvable: bool, one_step_callback: Callable[[Image.Image, int], None]):
        """
        The maze is indexed from top left.

        :param width:
        :param height:
        :param solvable:
        """
        self.map = []
        if width < 10:
            raise AttributeError('The width of the maze must be at least 10')
        self.width = width
        if height < 10:
            raise AttributeError('The height of the maze must be at least 10')
        self.height = height
        self.solvable = solvable
        self.generate(one_step_callback)

        if not solvable:
            self.make_unsolvable()

    def generate(self, one_step_callback: Callable[[Image.Image, int], None] = None) -> None:
        self.map = [[CellState.WALL for x in range(self.width)] for y in range(self.height)]

        RandomizedPrim(self, one_step_callback)

        self.start_point = self.find_start()
        self.mark_point_as(self.start_point, CellState.START)

        self.end_point = self.find_end()
        self.mark_point_as(self.end_point, CellState.END)
        pass

    def find_start(self) -> Point:
        """
        The start point should be in the top quadrant of the top quadrant
        :return:
        """
        state: CellState = None
        possible_point: Point = None
        while state != CellState.EMPTY:
            x: int = random_between(0, math.floor(self.width / 4.0))
            y: int = random_between(0, math.floor(self.height / 4.0))
            possible_point: Point = Point(x, y)
            state = self.get_state_of_cell(possible_point)
        return possible_point

    def find_end(self) -> Point:
        """
        The end point should be in the bottom quadrant of the bottom quadrant
        :return:
        """
        state: CellState = None
        possible_point: Point = None
        while state != CellState.EMPTY:
            x = random_between(self.width - math.ceil(self.width / 4.0), self.width - 1)
            y = random_between(self.height - math.ceil(self.height / 4.0), self.height - 1)
            possible_point: Point = Point(x, y)
            state = self.get_state_of_cell(possible_point)
        return possible_point

    def mark_point_as(self, point: Point, state: CellState) -> None:
        if point.is_in_maze(self):
            self.map[point.y][point.x] = state
        else:
            raise AttributeError('The point is not in maze!')

    def get_state_of_cell(self, point: Point, invalid_coordinates_state: CellState = CellState.EMPTY) -> CellState:
        if point.x < 0 or point.y < 0:
            return invalid_coordinates_state

        try:
            return self.map[point.y][point.x]
        except IndexError:
            return invalid_coordinates_state

    def print_maze(self) -> None:
        print(self.height, self.width)
        print(self.start_point.y, self.start_point.x)
        print(self.end_point.y, self.end_point.x)
        for i in self.map:
            for j in i:
                print(get_char_for_state(j), end='')
            print(end='\n')

    def make_unsolvable(self):
        while True:
            maze_solver = DepthFirstSolver(self)
            maze_solution = maze_solver.solve()
            if maze_solution is None:
                break
            else:
                random_point: Point = maze_solution[random_between(0, len(maze_solution) - 1)]
                self.mark_point_as(random_point, CellState.WALL)


class RandomizedPrim(object):
    maze: Maze
    wall_list: list
    visited: list

    def __init__(self, maze: Maze, one_step_callback: Callable[[Image.Image, int], None] = None):
        self.maze = maze
        self.wall_list = []
        self.visited = []

        origin = Point(random_between(0, maze.width - 1), random_between(0, maze.height - 1))
        self.maze.mark_point_as(origin, CellState.EMPTY)

        self.add_surrounding_walls_to_list(origin)

        while len(self.wall_list):
            wall: (Point, Point) = self.get_random_wall_from_list()
            new_point: Point = self.check_surroundings_for_one_empty(wall)
            if new_point is not None:
                if one_step_callback is not None:
                    one_step_callback(
                        ImageGenerator.generate_image_from_maze(self.maze, new_point),
                        ImageGenerator.ITERATION
                    )

    def check_surroundings_for_one_empty(self, wall: Tuple[Point, Point]) -> Optional[Point]:
        """
        Checks to surroundings for exactly one empty cell

        If only one surrounding cell is empty, we make it a passage and the next one in the direction too.

        Returns True if something interesting happens, because I probably don't really understand how to not
        check all walls and not create irregular patterns
        :param wall:
        :return:
        """
        origin: Point = wall[0]
        wall: Point = wall[1]

        x_to_get: int = wall.x - (origin.x - wall.x)
        y_to_get: int = wall.y - (origin.y - wall.y)

        new_point: Point = Point(x_to_get, y_to_get)

        origin_state: CellState = self.maze.get_state_of_cell(origin)
        final_state: CellState = self.maze.get_state_of_cell(new_point)

        states: list = [origin_state, final_state]

        if states.count(CellState.EMPTY) == 1:
            try:
                self.maze.mark_point_as(wall, CellState.EMPTY)
                self.maze.mark_point_as(new_point, CellState.EMPTY)
                self.add_surrounding_walls_to_list(new_point)
                return new_point
            except AttributeError:
                return None
        else:
            return None

    def add_surrounding_walls_to_list(self, origin: Point) -> None:
        for i in [-1, 1]:
            try:
                point: Point = Point(origin.x + i, origin.y)
                state: CellState = self.maze.get_state_of_cell(point)
                if state == CellState.WALL and not self.was_this_position_visited(point):
                    self.wall_list.append((origin, point))
                    self.mark_position_as_visited(point)
            finally:
                pass

            try:
                point: Point = Point(origin.x, origin.y + i)
                state: CellState = self.maze.get_state_of_cell(point)
                if state == CellState.WALL and not self.was_this_position_visited(point):
                    self.wall_list.append((origin, point))
                    self.mark_position_as_visited(point)
            finally:
                pass

        pass

    def get_random_wall_from_list(self) -> Tuple[Point, Point]:
        index: int = random_between(0, len(self.wall_list))
        point: Tuple[Point, Point] = self.wall_list[index]
        del self.wall_list[index]
        return point

    def mark_position_as_visited(self, point: Point) -> None:
        self.visited.append(HASHING_CONSTANT * point.x + point.y)
        pass

    def was_this_position_visited(self, point: Point) -> bool:
        check: int = HASHING_CONSTANT * point.x + point.y
        try:
            self.visited.index(check)
            return True
        except ValueError:
            return False


class DepthFirstSolver(object):
    maze: Maze
    current_point: Point
    path_stack: list
    visited: list

    def __init__(self, maze: Maze):
        self.maze = maze
        self.current_point = Point(maze.start_point.x, maze.start_point.y)
        self.path_stack = []
        self.visited = []

    def solve(self, one_step_callback: Callable[[Image.Image, int], None] = None) -> Optional[Tuple[Point, ...]]:
        """
        Goes through the maze using depth first / Trémaux algorithm and finds a path, if it exists

        :return: A tuple of Points that lead from start to end, not including start and end. Or None, if it cannot be
                 solved.
        """
        try:
            while True:
                if self.is_at_target():
                    self.path_stack.pop(0)
                    self.visited.pop(0)
                    return tuple(self.path_stack)

                self.mark_position_as_visited(self.current_point)
                self.path_stack.append(self.current_point)

                direction: Point = self.choose_one_direction_at_random_without_visited(self.current_point)
                if direction is None:
                    self.current_point = self.perform_rollback()
                    continue
                else:
                    self.current_point = direction

                if one_step_callback is not None:
                    one_step_callback(
                        ImageGenerator.draw_solution_step(
                            self.maze, self.path_stack, self.visited, self.current_point
                        ),
                        ImageGenerator.ITERATION
                    )
        except IndexError:
            return None

    def perform_rollback(self) -> Optional[Point]:
        while True:
            popped_point: Point = self.path_stack.pop()
            random_destination: Point = self.choose_one_direction_at_random_without_visited(popped_point)

            if random_destination is not None:
                self.path_stack.append(popped_point)
                return random_destination

    def choose_one_direction_at_random_without_visited(self, point: Point) -> Optional[Point]:
        up: Point = Point(point.x, point.y + 1)
        down: Point = Point(point.x, point.y - 1)
        left: Point = Point(point.x - 1, point.y)
        right: Point = Point(point.x + 1, point.y)

        # The order is biased to finding the solution from top left to bottom right, it should be truly random
        for point in [down, right, up, left]:
            state = self.maze.get_state_of_cell(point, CellState.WALL)
            if state == CellState.EMPTY or state == CellState.END:
                if not self.was_this_position_visited(point):
                    return point

        return None

    def choose_one_direction_at_random(self, point: Point) -> Optional[Point]:
        up: Point = Point(point.x, point.y + 1)
        down: Point = Point(point.x, point.y - 1)
        left: Point = Point(point.x - 1, point.y)
        right: Point = Point(point.x + 1, point.y)

        for point in [up, down, left, right]:
            if self.maze.get_state_of_cell(point, CellState.WALL) == CellState.EMPTY:
                return point

        return None

    def is_at_target(self) -> bool:
        return self.current_point.x == self.maze.end_point.x and self.current_point.y == self.maze.end_point.y

    def mark_position_as_visited(self, point: Point) -> None:
        self.visited.append(HASHING_CONSTANT * point.x + point.y)
        pass

    def was_this_position_visited(self, point: Point) -> bool:
        check: int = HASHING_CONSTANT * point.x + point.y
        try:
            self.visited.index(check)
            return True
        except ValueError:
            return False


class ImageGenerator(object):
    """
    The generation of images is extremely poorly optimized.
    """
    ITERATION: int = 0

    CELL_SIZE: int = 5

    # debug_font = ImageFont.truetype("/usr/share/fonts/truetype/DejaVuSans.ttf", 12)

    @classmethod
    def generate_image_from_maze(cls, maze: Maze, active_cell: Point = Point(-1, -1)) -> Image.Image:
        # This makes the images even sized, because ffmpeg can have problems with odd sizes
        image_width: int = maze.width * cls.CELL_SIZE + (maze.width * cls.CELL_SIZE) % 2
        image_height: int = maze.height * cls.CELL_SIZE + (maze.height * cls.CELL_SIZE) % 2
        im = Image.new('RGB', (image_width, image_height), (0, 0, 0))

        for i in range(0, maze.width):
            for j in range(0, maze.height):
                state: CellState = maze.get_state_of_cell(Point(i, j))
                if state == CellState.WALL:
                    fill = (0, 0, 0)
                    pass
                elif state == CellState.EMPTY:
                    fill = (255, 255, 255)
                elif state == CellState.START or state == CellState.END:
                    fill = (255, 0, 255)
                else:
                    fill = (255, 0, 0)

                cls.draw_one_cell(im, i, j, fill)

                """
                text_color = tuple([abs(x - 255) for x in fill])
                ImageDraw.Draw(im).text(
                    (i * cls.CELL_SIZE, j * cls.CELL_SIZE),
                    str(i) + ',' + str(j),
                    text_color,
                    font=cls.debug_font
                )
                """

        cls.draw_one_cell(im, active_cell.x, active_cell.y, (0, 255, 0))

        cls.ITERATION += 1
        return im

    @classmethod
    def draw_solution_to_image(cls, im, points: Tuple[Point, ...]) -> Image.Image:
        for point in points:
            cls.draw_one_cell(im, point.x, point.y, (0, 0, 255))

        return im

    @classmethod
    def draw_solution_step(cls, maze: Maze, path_stack: list, visited: list, current_point: Point):
        im = cls.generate_image_from_maze(maze, current_point)
        im = cls.draw_visited_in_solution(im, visited)
        im = cls.draw_solution_to_image(im, tuple(path_stack))
        cls.ITERATION += 1
        return im

    @classmethod
    def draw_visited_in_solution(cls, im, visited: list) -> Image.Image:
        for encoded in visited:
            x = encoded / HASHING_CONSTANT
            y = encoded % HASHING_CONSTANT
            cls.draw_one_cell(im, x, y, (255, 255, 0))
        return im

    @classmethod
    def draw_one_cell(cls, im: Image.Image, x: int, y: int, fill: Tuple = (0, 0, 0)) -> None:
        ImageDraw.Draw(im).rectangle([
            x * cls.CELL_SIZE,
            y * cls.CELL_SIZE,
            (x + 1) * cls.CELL_SIZE,
            (y + 1) * cls.CELL_SIZE
        ], fill=fill)


def save_image(image, iteration) -> None:
    image.save('images/' + str(iteration).zfill(10) + '.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates maze with given parameters')
    parser.add_argument('width', type=int, help='The width of maze')
    parser.add_argument('height', type=int, help='The height of maze')
    parser.add_argument('-u', '--unsolvable', dest='solvable', action='store_true',
                        help='Specify if it should be unsolvable')
    parser.add_argument('-v', '--save-video', dest='save_video', action='store_true',
                        help='Specify if the images should be saved')
    parser.add_argument('-f', '--framerate', dest='framerate', default=10,
                        help='Specify the framerate of resulting video')
    parser.add_argument('-s', '--cell-size', dest='cell_size', default=5,
                        help='Specify the size of cells in images and video')

    args = parser.parse_args()

    if args.save_video:
        callback = save_image
    else:
        callback = None

    ImageGenerator.CELL_SIZE = int(args.cell_size)

    generatedMaze = Maze(args.height, args.width, not args.solvable, callback)
    generatedMaze.print_maze()
    final_image: Image.Image = ImageGenerator.generate_image_from_maze(generatedMaze)
    final_image.save('final_image.png')

    solver = DepthFirstSolver(generatedMaze)
    solution = solver.solve(callback)

    if solution is None:
        print('This maze is unsolvable!')
    else:
        solved_image = ImageGenerator.draw_solution_to_image(final_image, solution)
        solved_image.save('final_solved.png')

    if args.save_video:
        os.system(
            "ffmpeg -y -framerate " + str(args.framerate) +
            " -pattern_type glob -i 'images/*.png' -c:v libx264 -r 30 -pix_fmt yuv420p out.mp4"
        )
        os.system("rm -fr images/*.png")
    else:
        pass
