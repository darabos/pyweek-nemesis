import collections
import math
import numpy
from OpenGL.GL import *


# Factors for the amount of scoring penalty for a shape with unequal
# side lengths or angles.
MISSED_LENGTH_PENALTY = 0.2
MISSED_ANGLE_PENALTY = 1.0

# Allowed error between the mouse path and the crystal position
# should be dependent on the crystal size.
DISTANCE_THRESHOLD = 0.1

def FilterMiddlePoints(mouse_path, angle_threshold):
  threshold = math.cos(math.radians(angle_threshold))
  if len(mouse_path) < 5:
      return mouse_path
  vectors = [
    (numpy.array([c2[0] - c1[0], c2[1] - c1[1]]), numpy.array([c3[0] - c2[0], c3[1] - c2[1]]))
    for c1, c2, c3 in zip(mouse_path[:-2], mouse_path[1:-1], mouse_path[2:])
  ]
  unit_vectors = [(v1 / numpy.linalg.norm(v1), v2 / numpy.linalg.norm(v2)) for v1, v2 in vectors]
  dots = [v1.dot(v2) for v1, v2 in unit_vectors]
  good_points = [mouse_path[i+1] for i in range(len(dots)) if dots[i] < threshold]
  return [mouse_path[0]] + good_points + [mouse_path[-1]]

def ShapeFromMouseInput(mouse_path, crystals):
  """
  Args:
    mouse_path: List of (x, y) coordinate tuples (normalized to [-1,+1] in
  each dimension) of raw mouse movement.
    crystals: List of Crystal objects with x, y, type attributes. x, y
    are coordinates, also normalized to [-1,+1], type is an integer
    indicating the type of crystal.

  Returns:
    A list of Crystal objects of connected crystals in the crystal
  list (which must be all be of the same type), or None if the mouse
  path does not form a shape with crystals at the corners. A crystal
  can occur only once in the list, except the first, which may be (and
  will be if the shape is closed) equal to the last.

  (This should handle being called with an incomplete path, in which case
  the trailing part of the mouse input might not be included in the shape.
  These shapes won't be valid for scoring, but we might want to draw them
  incrementally and start moving the ship in the general direction before we
  know if the shape is complete and valid.)
  """

  # dictionaries for { type : [ .. indexes ..] }
  touched_crystals = collections.defaultdict(list)
  num_touched_crystals = collections.defaultdict(int)

  used_crystals = set()
  last_crystal = None

  for mouse_coordinate in mouse_path:
    mouse_coordinate_x = mouse_coordinate[0]
    mouse_coordinate_y = mouse_coordinate[1]
    for crystal_index, crystal in enumerate(crystals):
      if not crystal.in_shape:
        left_margin = crystal.x - DISTANCE_THRESHOLD
        right_margin = crystal.x + DISTANCE_THRESHOLD
        if left_margin < mouse_coordinate_x < right_margin:
          bottom_margin = crystal.y - DISTANCE_THRESHOLD
          top_margin = crystal.y + DISTANCE_THRESHOLD
          if bottom_margin < mouse_coordinate_y < top_margin:
            last_crystal = crystal
            if crystal not in used_crystals:
              num_touched_crystals[crystal.type] += 1
              touched_crystals[crystal.type].append(crystal_index)
              used_crystals.add(crystal)

  if len(num_touched_crystals) == 0:
    return None
  max_type = max(num_touched_crystals, key=lambda x: num_touched_crystals[x])
  if len(touched_crystals[max_type]) < 3:
    return None

  # If the path is closed (and not degenerate), we add the last
  # crystal (equal to the first); it would not be added in the loop
  # since it'd already be in used_crystals.
  path = [crystals[i] for i in touched_crystals[max_type]]
  if last_crystal and last_crystal == path[0] and len(path) > 1:
    path.append(last_crystal)
  return path

def ShapeScore(shape):
  """
  Args:
    shape: List of (x,y) coordinates ([-1,+1]) of a shape path.

  Returns:
    The score of this shape. This is a product of the regularity
    (score from 0 to 1 depending on how equal the lengths of sides and
    angles between sides are, with 1.0 for perfectly regular), the
    number of sides, and x2 if the shape is self-intersecting (like a
    pentagram).
  """
  sides = len(shape)
  if sides < 3:
    return 0
  vectors = []
  lengths = []
  for i in xrange(sides):
    p0 = shape[i]
    p1 = shape[(i + 1) % sides]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    l = math.hypot(dx, dy)
    lengths.append(l)
    if l <= 0:
      l = 1
    vectors.append((dx / l, dy / l))

  angles = []
  for i in xrange(sides):
    v0 = vectors[i]
    v1 = vectors[(i + 1) % sides]
    dot = v0[0] * v1[0] + v0[1] * v1[1]
    side = math.copysign(1, v0[0] * v1[1] - v0[1] * v1[0])
    angle = math.acos(dot) * side
    angles.append(angle)

  angle_sum = abs(sum(angles) / math.pi)
  
  if sides >= 5:
    self_intersecting = angle_sum < 1.9 or angle_sum > 2.1
  else:
    self_intersecting = False
    
  avg_length = sum(lengths) / sides
  avg_angle = sum(angles) / sides
  angle_diffs = 0
  score = sides
  for l, a in zip(lengths, angles):
    l = 1 - abs(l / avg_length - 1) * MISSED_LENGTH_PENALTY
    angle_diffs += abs(a - avg_angle)
    score *= l
  score /= (1 + angle_diffs / math.pi * MISSED_ANGLE_PENALTY)

  if self_intersecting:
    score *= 2

  return score


class Shape(object):
  BEING_DRAWN = 0
  SHIP_TRACING_PATH = 1
  DONE = 2

  def __init__(self, game):
    self.state = self.BEING_DRAWN
    self.path = []
    self.ship_visited_to = 0
    self.game = game
    self.score = None

  def UpdateWithPath(self, path):
    if path is None:
      path = []
    self.path = path

  def CompleteWithPath(self, path):
    """Complete a path, must be called at most once.

    UpdateWithPath must not be called after this has been called. Sets
    the score, x, and y attributes.

    Returns:
      True if the shape is valid. False if it is not (degenerate, not
      closed, etc.), in which case the object is invalid.
    """
    if path is None:
      return False
    if path[0] != path[-1]:
      # Not closed, not valid.
      return False
    self.path = path[:-1]
    vertices = [(c.x, c.y) for c in self.path]
    self.score = ShapeScore(vertices)
    self.x, self.y = (v / len(vertices) for v in map(sum, zip(*vertices)))
    if self.score <= 0:
      return False
    self.state = self.SHIP_TRACING_PATH
    for crystal in self.path:
      crystal.in_shape = True
    return True

  def Cancel(self):
    for crystal in self.path:
      crystal.in_shape = False

  def ShipVisited(self, index):
    self.ship_visited_to = index

  def DoneTracing(self):
    """Returns true and moves to the done state if the shape is fully traced."""
    if self.ship_visited_to > len(self.path):
      self.state = self.DONE
      return True
    return False

  def Render(self):
    if self.state == self.BEING_DRAWN:
      return

    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    for i in xrange(len(self.path)):
      v0 = [self.path[i].x, self.path[i].y]
      v1 = [self.path[(i + 1) % len(self.path)].x,
            self.path[(i + 1) % len(self.path)].y]
      dx = v1[0] - v0[0]
      dy = v1[1] - v0[1]
      l = math.hypot(dx, dy)
      dx = dx / l * 0.01
      dy = dy / l * 0.01
      if i < self.ship_visited_to - 1:
        glColor(1.0, 1.0, 0.2, 1.0)
      else:
        glColor(0.2, 0.2, 0.2, 0.6)
      glBegin(GL_QUADS)
      glVertex(v0[0] + dy, v0[1] - dx)
      glVertex(v0[0] - dy, v0[1] + dx)
      glVertex(v1[0] - dy, v1[1] + dx)
      glVertex(v1[0] + dy, v1[1] - dx)
      glEnd()

      if i >= self.ship_visited_to - 1:
        continue

      dx *= 4
      dy *= 4
      glEnable(GL_BLEND)
      glBegin(GL_TRIANGLES)

      glColor(1.0, 1.0, 0.2, 0.5)
      glVertex(v0[0]     , v0[1]     )
      glColor(1.0, 1.0, 0.2, 0.0)
      glVertex(v0[0] + dy, v0[1] - dx)
      glVertex(v0[0] - dy, v0[1] + dx)

      glColor(1.0, 1.0, 0.2, 0.5)
      glVertex(v0[0]     , v0[1]     )
      glColor(1.0, 1.0, 0.2, 0.0)
      glVertex(v0[0] + dy, v0[1] - dx)
      glVertex(v1[0] + dy, v1[1] - dx)

      glColor(1.0, 1.0, 0.2, 0.5)
      glVertex(v0[0]     , v0[1]     )
      glColor(1.0, 1.0, 0.2, 0.0)
      glVertex(v0[0] - dy, v0[1] + dx)
      glVertex(v1[0] - dy, v1[1] + dx)

      glColor(1.0, 1.0, 0.2, 0.5)
      glVertex(v0[0]     , v0[1]     )
      glVertex(v1[0]     , v1[1]     )
      glColor(1.0, 1.0, 0.2, 0.0)
      glVertex(v1[0] - dy, v1[1] + dx)

      glColor(1.0, 1.0, 0.2, 0.5)
      glVertex(v0[0]     , v0[1]     )
      glVertex(v1[0]     , v1[1]     )
      glColor(1.0, 1.0, 0.2, 0.0)
      glVertex(v1[0] + dy, v1[1] - dx)

      glColor(1.0, 1.0, 0.2, 0.5)
      glVertex(v1[0]     , v1[1]     )
      glColor(1.0, 1.0, 0.2, 0.0)
      glVertex(v1[0] + dy, v1[1] - dx)
      glVertex(v1[0] - dy, v1[1] + dx)

      glEnd()
      glDisable(GL_BLEND)

    if self.state == self.DONE:
      verts = [(c.x, c.y) for c in self.path]
      verts = sorted(verts,
                     key=lambda (x, y): math.atan2(y - self.y, x - self.x))
      goodness = min(1, self.score / 5.)
      glEnable(GL_BLEND)
      glBegin(GL_TRIANGLES)
      glColor(0, 1, 0, 1)
      for i in xrange(len(verts)):
        v0 = verts[i]
        v1 = verts[(i + 1) % len(verts)]

        glColor(1.0 - goodness, 1.0 - goodness, 0.2, goodness * 1.0 + 0.2)
        glVertex(self.x, self.y)
        glColor(1.0 - goodness, 1.0 - goodness, 0.2, 0.0)
        glVertex(v0[0], v0[1])
        glVertex((v0[0] + v1[0] + self.x) / 3.,
                 (v0[1] + v1[1] + self.y) / 3.)

        glColor(1.0 - goodness, 1.0 - goodness, 0.2, goodness * 1.0 + 0.2)
        glVertex(self.x, self.y)
        glColor(1.0 - goodness, 1.0 - goodness, 0.2, 0.0)
        glVertex((v0[0] + v1[0] + self.x) / 3.,
                 (v0[1] + v1[1] + self.y) / 3.)
        glVertex(v1[0], v1[1])

      glEnd()
      glDisable(GL_BLEND)
