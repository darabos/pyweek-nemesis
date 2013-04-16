import collections
import math


# Factors for the amount of scoring penalty for a shape with unequal
# side lengths or angles.
MISSED_LENGTH_PENALTY = 0.2
MISSED_ANGLE_PENALTY = 1.0

# Allowed error between the mouse path and the crystal position
# should be dependent on the crystal size.
# currently: (0.01 + 0.002) / 2
DISTANCE_THRESHOLD = 0.006

def ShapeFromMouseInput(mouse_path, crystals):
  """
  Args:
    mouse_path: List of (x, y) coordinate tuples (normalized to [-1,+1] in
  each dimension) of raw mouse movement.
    crystals: List of tuples of (x, y, type) coordinate tuples. x, y are
  coordinates, also normalized to [-1,+1], type is an integer indicating
  the type of crystal.

  Returns:
    A list of indices of connected crystals in the crystal list (which must
  be all be of the same type), or None if the mouse path does not form a
  shape with crystals at the corners. An crystal index can occur only once
  in the list, except the first index, which may be (and will be if the
  shape is closed) equal to the last index.

  (This should handle being called with an incomplete path, in which case
  the trailing part of the mouse input might not be included in the shape.
  These shapes won't be valid for scoring, but we might want to draw them
  incrementally and start moving the ship in the general direction before we
  know if the shape is complete and valid.)
  """

  # dictionaries for { type : [ .. indexes ..] }
  touched_crystals = collections.defaultdict(list)
  num_touched_crystals = collections.defaultdict(int)

  for mouse_coordinate in mouse_path:
    mouse_coordinate_x = mouse_coordinate[0]
    mouse_coordinate_y = mouse_coordinate[1]
    for crystal_index, crystal in enumerate(crystals):
      crystal_x, crystal_y, crystal_type = crystal
      left_margin = crystal_x - DISTANCE_THRESHOLD
      right_margin = crystal_x + DISTANCE_THRESHOLD
      if left_margin < mouse_coordinate_x <  right_margin:
        bottom_margin = crystal_y - DISTANCE_THRESHOLD
        top_margin = crystal_y + DISTANCE_THRESHOLD
        if bottom_margin < mouse_coordinate_y < top_margin:
          num_touched_crystals[crystal_type] += 1
          touched_crystals[crystal_type].append(crystal_index)

  if len(num_touched_crystals) == 0: return None
  max_type = max(num_touched_crystals, key=lambda x: num_touched_crystals[x])
  if len(touched_crystals[max_type]) < 3: return None

  return touched_crystals[max_type]

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
    l = math.sqrt(dx * dx + dy * dy)
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

  self_intersecting = angle_sum < 1.9 or angle_sum > 2.1

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
