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
  def __init__(self, max_crystals, min_x=-1, max_x=1, min_y=-1, max_y=1):
    self.crystals = []
    for i in range(max_crystals):
      crystal = Crystal(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
      self.crystals.append(crystal)

  def __iter__(self):
    return self.crystals.__iter__()
  def __getitem__(self, key):
    return self.crystals.__getitem__(key)
  def remove(self, key):
    return self.crystals.remove(key)

  def Render(self):
    for crystal in self.crystals:
      crystal.Render()
