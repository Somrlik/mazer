# Mazer

Makes and solves mazes in python. Also makes videos of it.

Includes sample images of final maze and solution as well as a video
shoving the algorithms at work.

# Installation

You will need
 - `python` > 3.5
 - `pillow` > 5.3.0 for image generation or any other PIL fork
 - `ffmpeg` for video generation
 
# Running

```python main.py --help```

# Algorithms

## Maze generation

Maze generation uses a modified Prim's algorithm for finding a minimum spanning tree for a weighted graph.
The modification lies in the randomness of "edges" and fullness of the graph.

It can be further optimized, but I hacked this thing together in like
6 hours, so I cannot be arsed.

The algorithm is as follows:
 - Start with a maze full of walls
 - Pick a random starting point, mark it as a passage
 - Add all of its surrounding walls to a list
 - While the list of walls is not empty:
   - Pick a random wall from list
   - If there is only one empty cell on either side of this wall:
     - Make the wall and the other side an empty space
     - Add all neighbouring walls of the last cell to the wall list
 
## Path finding in maze

Its a simple depth-first search.

Here we go:
 - Start with an empty list of visited cells
 - Start at a starting position, add this position to visited cells and put in onto a stack
 - While the stack is not empty
   - Choose a direction that you haven't visited yet at random
   - If there is an available direction
     - Go there, put it on stack and in visited locations and continue
   - Else rollback
    - While the stack is not empty
      - Pop last visited location from stack
      - If there is a direction that you haven't visited yet
        - Go there, put it on stack and in visited locations and break
      - Else continue, until you find one possible direction or the stack is empty
 
If the stack empties at any time, you will know that the maze is unsolvable.

# TODO
 - Optimize handling of images, right now I am redrawing the whole thing every frame, that can be optimized using layers
   or just drawing over the needed rectangles.
 - Split the classes into multiple files

# License
MIT

# Contributions
Welcome
