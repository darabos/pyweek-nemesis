from OpenGL.GL import *

import rendering
import random
import math

class Crystal(object):
  vbo = None
  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.type = 0
    if not Crystal.vbo:
      Crystal.vbo = rendering.Quad(0.03, 0.03)

  def DistanceFrom(self, crystal):
    return math.hypot(self.x - crystal.x, self.y - crystal.y)

  def Render(self):
    glColor(1, 1, 1, 1)
    glPushMatrix()
    glTranslatef(self.x, self.y, 0)
    Crystal.vbo.Render()
    glPopMatrix()

class Crystals(object):
  states = ['NoCrystals', 'OneTriangle', 'KeepMax']

  def UpdateNoCrystals(self, dt, game):
    if game.lines_drawn > 2:
      self.SetState('OneTriangle')

  def UpdateOneTriangle(self, dt, game):
    if len(self.crystals) == 0:
      self.CreateCrystals(3)
    if game.shapes:
      self.SetState('KeepMax')

  def UpdateKeepMax(self, dt, game):
    crystals_needed = self.max_crystals - len(self.crystals)
    if crystals_needed > 0:
      self.CreateCrystals(crystals_needed)

  def __init__(self, max_crystals, total_crystals, min_x=-0.9, max_x=0.9, min_y=-0.9, max_y=0.9):
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

  def CreatePerfectPolygon(self, number_of_sides):
    tries = 10
    polygons = []
    for i in range(tries):
      radius = random.uniform(0.1, min(self.max_x - self.min_x, self.max_y - self.min_y) / 2)
      min_x = self.min_x + radius
      max_x = self.max_x - radius
      min_y = self.min_y + radius
      max_y = self.max_y - radius
      center = random.uniform(min_x, max_x), random.uniform(min_y, max_y)
      angle_per_side = 2 * math.pi / number_of_sides
      starting_angle = random.uniform(0, angle_per_side)
      angles = [starting_angle + angle_per_side * i for i in range(number_of_sides)]
      coords = [(center[0] + radius * math.sin(angle), center[1] + radius * math.cos(angle)) for angle in angles]
      crystals = [Crystal(coord[0], coord[1]) for coord in coords]
      min_distance = min([
        min([
          new_crystal.DistanceFrom(crystal) for crystal in self.crystals
        ] + [1]) for new_crystal in crystals
      ] + [1])
      polygons.append({
        'crystals': crystals,
        'min_distance': min_distance
      })
    best_polygon = max(polygons, key=lambda p: p['min_distance'])
    return best_polygon['crystals']

  def CreateCrystals(self, number):
    number = min(self.crystals_left, number)
    self.crystals_left -= number
    while number >= 3:
      crystals = self.CreatePerfectPolygon(3)
      self.crystals.extend(crystals)
      number -= 3
    for i in range(number):
      crystals = self.CreatePerfectPolygon(1)
      self.crystals.extend(crystals)

  def Update(self, dt, game):
    getattr(self, 'Update' + self.state)(dt, game)

  def Render(self):
    for crystal in self.crystals:
      crystal.Render()
