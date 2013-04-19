import math
from OpenGL.GL import *

import rendering


def ShipPathFromWaypoints(starting_location, starting_velocity, waypoints, max_velocity=1):
  """
  Args:
    starting_location: tuple (x, y) ([-1, +1] again) of the starting
  position of the ship.
    starting_velocity: tuple (x,y) of the starting velocity of the ship in
  units per second.
    waypoints: List of tuples (x, y) of points the ship should pass through.

  Returns:
    A callable that takes a single argument 'time' and returns a tuple (x,
  y, dx, dy) of the position and velocity of the ship at the given time,
  assuming the ship was at the given starting location with the given
  starting velocity at time 0 and is moving to pass (exactly) through each
  given waypoint in order, with arbitrary velocity except at the final
  waypoint where the velocity should be (0, 0).

  (Thus, when passed time=0, it should return starting_location,
  starting_velocity. For any time >= the time it takes to reach the final
  waypoint, it should return (final_waypoint, 0, 0).)
  """
  waypoints_with_starting_location = [starting_location] + waypoints
  waypoint_pairs = [(waypoints_with_starting_location[i], waypoints[i]) for i in range(len(waypoints))]
  distances = [math.hypot(end[0] - start[0], end[1] - start[1])
               for (start, end) in waypoint_pairs]
  total_distance = sum(distances)
  total_time = total_distance / max_velocity

  def curve(progress):
    distance = progress * total_distance
    accumulator = 0
    for i in range(len(distances)):
      if distance < accumulator + distances[i]:
        start, end = waypoint_pairs[i]
        small_progress = (distance - accumulator) / distances[i]
        return (
          start[0] + (end[0] - start[0]) * small_progress,
          start[1] + (end[1] - start[1]) * small_progress,
          (end[0] - start[0]) / distances[i],
          (end[1] - start[1]) / distances[i],
          i)
      accumulator += distances[i]
    return waypoints[-1] + (0, 0, i + 1)

  def control(time):
    distance = 0
    velocity = 0
    if time < 0:
      distance = 0
      velocity = 0
    elif time > total_time:
      distance = total_distance
      velocity = 0
    else:
      velocity = max_velocity
      distance = time / total_time * total_distance
    (locationX, locationY, directionX, directionY, index) = curve(distance / total_distance)
    return (
      locationX,
      locationY,
      directionX * velocity,
      directionY * velocity,
      index)

  return control


class Ship(object):
  def __init__(self, x, y, size):
    self.x = x
    self.y = y
    self.size = size
    self.vbo = rendering.Quad(size, size)
    self.texture = []
    self.health = 1.0
    self.max_health = 10.0

  def Render(self):
    glColor(1, 1, 1, 1)
    glPushMatrix()
    glTranslatef(self.x, self.y, 0)
    with self.texture:
      self.vbo.Render()
    glPopMatrix()

class BigShip(Ship):
  def InRangeOfTarget(self):
    if not self.target:
      return False
    dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
    return dist <= 0.002


  def NearestTarget(self, shapes):
    if not shapes:
      return None
    nearest = min(shapes,
                  key=lambda shape: math.hypot(shape.x - self.x,
                                               shape.y - self.y))
    return nearest
