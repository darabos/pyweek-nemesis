from OpenGL.GL import *

import rendering
import random
import math
import numpy
import shapes

class Crystal(object):
  vbo = None
  def __init__(self, loc):
    self.x, self.y = loc
    self.type = 0
    self.visible = False
    self.start_fade_in_time = random.uniform(1, 8)
    self.fade_in_time = random.uniform(2, 4)
    self.t = self.start_fade_in_time + self.fade_in_time
    self.matching = False
    self.in_shape = False
    if not Crystal.vbo:
      Crystal.vbo = rendering.Quad(0.03, 0.03)

  def DistanceFromCoord(self, x, y):
    return math.hypot(self.x - x, self.y - y)

  def Update(self, dt, matching):
    self.matching = matching
    self.t = max(0, self.t - dt)
    if self.t < self.fade_in_time / 2:
      self.visible = True

  def Render(self):
    if self.t < self.fade_in_time:
      alpha = 1 - (self.t / self.fade_in_time)
      glColor(0, self.matching and 0.5 or 1, 1, alpha)
      glPushMatrix()
      glTranslatef(self.x, self.y, 0)
      Crystal.vbo.RenderCrystal(alpha)
      glPopMatrix()

  def __repr__(self):
    return "Crystal at %2f:%2f" % (self.x, self.y)

class Crystals(object):
  states = ['NoCrystals', 'OneTriangle', 'KeepMax']

  def rotation_matrix(self, degree):
    rad = math.radians(degree)
    return numpy.matrix([[math.cos(rad), -math.sin(rad)], [math.sin(rad), math.cos(rad)]])

  def __len__(self):
    return len(self.crystals)

  def UpdateNoCrystals(self, dt, game):
    if game.lines_drawn > 1:
      self.SetState('OneTriangle')

  def UpdateOneTriangle(self, dt, game):
    if len(self.crystals) == 0:
      self.crystals.append(Crystal((-0.5, -0.5)))
      self.crystals.append(Crystal((-0.5, 0)))
      self.CreateCrystals(1)
    if game.shapes:
      self.SetState('KeepMax')

  def UpdateKeepMax(self, dt, game):
    crystals_needed = self.max_crystals - len(self.crystals)
    if crystals_needed > 0:
      self.CreateCrystals(crystals_needed)

  def __init__(self, max_crystals, total_crystals, min_x=-0.9*rendering.RATIO, max_x=0.9*rendering.RATIO, min_y=-0.9, max_y=0.9):
    self.min_x = min_x
    self.max_x = max_x
    self.min_y = min_y
    self.max_y = max_y
    self.max_crystals = max_crystals
    self.crystals_left = total_crystals
    self.crystals = []
    self.SetState('NoCrystals')

  def __iter__(self):
    return self.crystals.__iter__()
  def __getitem__(self, key):
    return self.crystals.__getitem__(key)
  def remove(self, key):
    return self.crystals.remove(key)

  def SetState(self, name):
    if name in self.states:
      self.state = name
    else:
      raise Exception("no such Crystals state " + name)

  def IsInState(self, name):
    if name in self.states:
      return name == self.state
    else:
      raise Exception("no such Crystals state " + name)

  def MinDistanceFromExistingCrystals(self, coord):
    return min([(1000, None)] + [(crystal.DistanceFromCoord(*coord), crystal) for crystal in self.crystals])

  def GetGoodRandomLocation(self, number_of_tries=10):
    centers = [(random.uniform(self.min_x, self.max_x), random.uniform(self.min_y, self.max_y)) for i in range(number_of_tries)]
    distances = [self.MinDistanceFromExistingCrystals(center)[0] for center in centers]
    return max(zip(distances, centers))[1]

  def GetLocationCreatingAShape(self, degree):
    if len(self.crystals) > 1:
      c1, c2 = random.sample(self.crystals, 2)
      v1, v2 = numpy.array((c2.x, c2.y)), numpy.array((c1.x, c1.y))
      v3 = (v2 - v1) * self.rotation_matrix(degree) + v2
      new_loc = (v3.item(0), v3.item(1))
      if self.min_x < new_loc[0] < self.max_x and self.min_y < new_loc[1] < self.max_y:
        return new_loc
    return None

  # def CreatePerfectPolygon(self, number_of_sides):
  #   tries = 10
  #   polygons = []
  #   for i in range(tries):
  #     radius = random.uniform(0.1, min(self.max_x - self.min_x, self.max_y - self.min_y) / 2)
  #     min_x = self.min_x + radius
  #     max_x = self.max_x - radius
  #     min_y = self.min_y + radius
  #     max_y = self.max_y - radius
  #     center = random.uniform(min_x, max_x), random.uniform(min_y, max_y)
  #     angle_per_side = 2 * math.pi / number_of_sides
  #     starting_angle = random.uniform(0, angle_per_side)
  #     angles = [starting_angle + angle_per_side * i for i in range(number_of_sides)]
  #     coords = [(center[0] + radius * math.sin(angle), center[1] + radius * math.cos(angle)) for angle in angles]
  #     crystals = [Crystal(coord) for coord in coords]
  #     min_distance = min([
  #       min([
  #         new_crystal.DistanceFrom(crystal) for crystal in self.crystals
  #       ] + [1]) for new_crystal in crystals
  #     ] + [1])
  #     polygons.append({
  #       'crystals': crystals,
  #       'min_distance': min_distance
  #     })
  #   best_polygon = max(polygons, key=lambda p: p['min_distance'])
  #   return best_polygon['crystals']

  def CreateCrystals(self, number):
    number_of_tries = 20
    distance_threshold = 0.1

    number = min(self.crystals_left, number)
    self.crystals_left -= number

    interesting_degrees = (120, 90, 72)
    for i in range(number):
      degree = random.choice(interesting_degrees)
      locations = [
        (self.MinDistanceFromExistingCrystals(loc)[0], loc)
        for loc in [self.GetLocationCreatingAShape(degree) for i in range(number_of_tries)]
        if loc is not None
      ]
      if len(locations) == 0:
        crystal = Crystal(self.GetGoodRandomLocation())
      else:
        best_distance, best_location = max(locations)
        if best_distance < distance_threshold:
          crystal = Crystal(self.GetGoodRandomLocation())
        else:
          crystal = Crystal(best_location)
      self.crystals.append(crystal)

  def Update(self, dt, game):
    getattr(self, 'Update' + self.state)(dt, game)
    min_distances = [self.MinDistanceFromExistingCrystals(coord) for coord in game.needle_ship.drawing]
    crystals_matching_path = [crystal for distance, crystal in min_distances if distance < shapes.DISTANCE_THRESHOLD]
    for crystal in self.crystals:
      crystal.Update(dt, crystal in crystals_matching_path)

  def Render(self):
    for crystal in self.crystals:
      crystal.Render()
