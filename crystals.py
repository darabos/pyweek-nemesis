from OpenGL.GL import *

import rendering
import random

def DrawCrystal(x, y, width, height):
  """
  Args:
    x, y: Coordinates of center of crystal.
    width, height: Width and height of crystal.
  """
  # Placeholder.
  glColor(1, 1, 1, 1)
  glPushMatrix()
  glTranslatef(x, y, 0)
  Crystal.vbo.Render()
  glPopMatrix()

class Crystal(object):
  vbo = None
  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.type = 0
    if not Crystal.vbo:
      Crystal.vbo = rendering.Quad(0.02, 0.02)
  def Render(self):
    DrawCrystal(self.x, self.y, 0.02, 0.02)

class Crystals(object):
  states = ['no_crystals', 'one_triangle', 'keep_max']

  def __init__(self, max_crystals, total_crystals, min_x=-0.9, max_x=0.9, min_y=-0.9, max_y=0.9):
    self.min_x = min_x
    self.max_x = max_x
    self.min_y = min_y
    self.max_y = max_y
    self.max_crystals = max_crystals
    self.crystals_left = total_crystals
    self.crystals = []
    self.SetState('no_crystals')

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

  def CreateCrystals(self, number):
    number = min(self.crystals_left, number)
    self.crystals_left -= number
    for i in range(number):
      crystal = Crystal(random.uniform(self.min_x, self.max_x), random.uniform(self.min_y, self.max_y))
      self.crystals.append(crystal)

  def Update(self, dt, game):
    if game.lines_drawn > 2:
      if len(game.shapes) == 0:
        self.SetState('one_triangle')
      else:
        self.SetState('keep_max')

    if self.IsInState('one_triangle'):
      if len(self.crystals) == 0:
        self.CreateCrystals(3)
    if self.IsInState('keep_max'):
      crystals_needed = self.max_crystals - len(self.crystals)
      if crystals_needed > 0:
        self.CreateCrystals(crystals_needed)

  def Render(self):
    for crystal in self.crystals:
      crystal.Render()
