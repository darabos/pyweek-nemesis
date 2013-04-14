import math
import pygame
import random
import sys
from OpenGL.GL import *


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

def ShapeScore(shape):
  """
  Args:
    shape: List of (x,y) coordinates ([-1,+1]) of a shape path.

  Returns:
    The score of this shape. This is a product of the regularity (score from
  0 to 1 depending on how equal the lengths of sides and angles between
  sides are, with 1.0 for perfectly regular), the number of sides, and x2
  if the shape is self-intersecting (like a pentagram).
  """

def DrawCrystal(x, y, width, height):
  """
  Args:
    x, y: Coordinates of center of crystal.
    width, height: Width and height of crystal.
  """
  # Placeholder.
  glBindBuffer(GL_ARRAY_BUFFER, Crystal.vbo.id)
  glEnableClientState(GL_VERTEX_ARRAY)
  glVertexPointer(3, GL_FLOAT, 0, None)
  glPushMatrix()
  glTranslatef(x, y, 0)
  glDrawArrays(GL_QUADS, 0, 4)
  glPopMatrix()

def ShipPathFromWaypoints(starting_location, starting_velocity, waypoints, acceleration=1):
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
  destination = waypoints[-1]  # we only do the first one yet and we ignore the starting_velocity
  target_vector = (destination[0] - starting_location[0], destination[1] - starting_location[1])
  total_distance = math.sqrt(target_vector[0] ** 2 + target_vector[1] ** 2)
  direction_vector = (target_vector[0] / total_distance, target_vector[1] / total_distance)
  total_time = math.sqrt(total_distance / acceleration) * 2
  braking_time = total_time / 2
  velocity_at_braking_time = braking_time * acceleration
  distance_at_braking_time = velocity_at_braking_time * braking_time / 2

  def curve(progress):
    return (
      starting_location[0] + progress * total_distance * direction_vector[0],
      starting_location[1] + progress * total_distance * direction_vector[1]
    )

  def control(time):
    time *= 0.001
    distance = 0
    velocity = 0
    if time < 0:
      distance = 0
      velocity = 0
    elif time > total_time:
      distance = total_distance
      velocity = 0
    else:
      if time < braking_time:
        velocity = acceleration * time
        distance = time * velocity / 2
      else:
        velocity = velocity_at_braking_time - (time - braking_time) * acceleration
        distance = distance_at_braking_time + (time - braking_time) * (velocity_at_braking_time + velocity) / 2
    progress = distance / total_distance
    location = curve(progress)
    return (
      location[0],
      location[1],
      velocity * direction_vector[0],
      velocity * direction_vector[1]
    )

  return control



class Quad(object):
  def __init__(self, w, h):
    self.buf = (ctypes.c_float * (4 * 3))()
    for i, x in enumerate([-w/2, -h/2, 0, w/2, -h/2, 0, w/2, h/2, 0, -w/2, h/2, 0]):
      self.buf[i] = x
    self.id = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, self.id)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(self.buf), self.buf, GL_STATIC_DRAW)


class Crystal(object):
  vbo = None
  def __init__(self, x, y):
    self.x = x
    self.y = y
    if not Crystal.vbo:
      Crystal.vbo = Quad(0.01, 0.01)
  def Render(self):
    DrawCrystal(self.x, self.y, 0.01, 0.01)


class Ship(object):
  def __init__(self, x, y, size):
    self.x = x
    self.y = y
    self.vbo = Quad(size, size)
  def Render(self):
    glBindBuffer(GL_ARRAY_BUFFER, self.vbo.id)
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, None)
    glPushMatrix()
    glTranslatef(self.x, self.y, 0)
    glDrawArrays(GL_QUADS, 0, 4)
    glPopMatrix()


class Game(object):

  def __init__(self):
    self.objects = []

  def Start(self):
    self.Init()
    self.Loop()

  def Init(self):
    pygame.init()
    self.width, self.height = 600, 600
    pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption('Nemesis')
    glViewport(0, 0, self.width, self.height)

    for i in range(100):
      self.objects.append(Crystal(random.uniform(-1, 1), random.uniform(-1, 1)))
    self.small_ship = Ship(0, 0, 0.05)
    self.small_ship.drawing = []
    self.small_ship.path_func = None
    self.small_ship.path_func_start_time = None
    self.objects.append(self.small_ship)
    self.big_ship = Ship(0, 0, 0.2)
    self.big_ship.path_func = None
    self.big_ship.path_func_start_time = None
    self.objects.append(self.big_ship)

  def Loop(self):
    clock = pygame.time.Clock()
    time = 0
    while True:
      dt = clock.tick()
      time += dt
      self.Update(dt, time)
      glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
      self.DrawPath(self.small_ship.drawing)
      for o in self.objects:
        o.Render()
      pygame.display.flip()

  def GameSpace(self, x, y):
    w, h = float(self.width), float(self.height)
    return 2 * x / w - 1, 1 - 2 * y / h

  def DrawPath(self, path):
    glBegin(GL_TRIANGLE_STRIP)
    lx = None
    for x, y in path:
      if lx is None:
        glVertex(x, y, 0)
      else:
        dx = x - lx
        dy = y - ly
        n = 0.005 / math.sqrt(dx * dx + dy * dy)
        dx *= n
        dy *= n
        glVertex(x + dy, y - dx, 0)
        glVertex(x - dy, y + dx, 0)
      lx = x
      ly = y
    glEnd()

  def Update(self, dt, time):
    dt *= 0.001
    for e in pygame.event.get():
      if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit(0)
      if e.type == pygame.MOUSEBUTTONUP and e.button == 3:
        self.big_ship.path_func = ShipPathFromWaypoints((self.big_ship.x, self.big_ship.y), (0, 0), [self.GameSpace(*e.pos)])
        self.big_ship.path_func_start_time = time
      if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
        self.small_ship.path_func = ShipPathFromWaypoints((self.small_ship.x, self.small_ship.y), (0, 0), self.small_ship.drawing, 10)
        self.small_ship.path_func_start_time = time
      if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
        self.small_ship.drawing = [self.GameSpace(*e.pos)]
      if e.type == pygame.MOUSEMOTION and e.buttons[0]:
        self.small_ship.drawing.append(self.GameSpace(*e.pos))

    for ship in [self.small_ship, self.big_ship]:
      if ship.path_func:
        (x, y, dx, dy) = ship.path_func(time - ship.path_func_start_time)
        ship.x = x
        ship.y = y


if __name__ == '__main__':
  Game().Start()
