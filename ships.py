import pygame
import math
from OpenGL.GL import *

import rendering


def ShipPathFromWaypoints(starting_location, starting_velocity, waypoints, max_velocity):
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
  if total_distance == 0:
    return lambda time: (starting_location[0], starting_location[1], 0, 0, 0)

  if total_distance == 0:
    return lambda time: (starting_location[0], starting_location[1], 0, 0, 0)

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
    self.path_func = None
    self.path_func_start_time = None
    self.vbo = rendering.Quad(size, size)
    self.texture = rendering.Texture(pygame.image.load('art/ships/birdie.png'))

  def Render(self):
    glColor(1, 1, 1, 1)
    glPushMatrix()
    glTranslatef(self.x, self.y, 0)
    with self.texture:
      self.vbo.Render()
    glPopMatrix()

class Projectile(Ship):
  def __init__(self, x, y, size):
    super(Projectile, self).__init__(x, y, size)
    self.damage = 0.5
    self.texture = rendering.Texture(pygame.image.load('art/ships/balls.png'))    
    self.max_velocity = 1.2
    self.owner = None

class JellyFish(Ship):
  def __init__(self, x, y, size):
    super(JellyFish, self).__init__(x, y, size)
    self.damage = 0.01
    self.texture = rendering.Texture(pygame.image.load('art/ships/Jellyfish.png'))
    self.health = size * 10.0
    self.max_health = size * 10.0
    self.max_velocity = 0.05

class SmallShip(Ship):
  def __init__(self, x, y, size):
    super(SmallShip, self).__init__(x, y, size)
    self.health = 1.0
    self.max_health = 1.0
    self.name = 'Needle'
    self.drawing = []
    self.max_velocity = 1.0

class BigShip(Ship):
  def __init__(self, x, y, size):
    super(BigShip, self).__init__(x, y, size)
    self.mana = 100.0
    self.health = 10.0
    self.max_health = 10.0
    self.name = 'Big Ship'
    self.chasing_shapes = False
    self.target = None
    self.target_reevaluation = 0
    self.max_velocity = 0.2
    self.combat_range = 0.4
    self.cooldown = 1.0
    self.prev_fire = 1.0
    self.ammo_cost = 20.0