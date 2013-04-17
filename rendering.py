import math
import pygame
from OpenGL.GL import *


class Quad(object):

  def __init__(self, w, h):
    self.buf = (ctypes.c_float * (4 * 5))()
    for i, x in enumerate([-w/2, -h/2, 0, 0, 0, w/2, -h/2, 0, 1, 0, w/2, h/2, 0, 1, 1, -w/2, h/2, 0, 0, 1]):
      self.buf[i] = x
    self.id = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, self.id)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(self.buf), self.buf, GL_STATIC_DRAW)

  def Render(self):
    F = ctypes.sizeof(ctypes.c_float)
    FP = lambda x: ctypes.cast(x * F, ctypes.POINTER(ctypes.c_float))
    glBindBuffer(GL_ARRAY_BUFFER, self.id)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glVertexPointer(3, GL_FLOAT, 5 * F, FP(0))
    glTexCoordPointer(2, GL_FLOAT, 5 * F, FP(3))
    glDrawArrays(GL_QUADS, 0, 4)


class Texture(object):
  def __init__(self, surface):
    data = pygame.image.tostring(surface, 'RGBA', 1)
    self.id = glGenTextures(1)
    self.width = surface.get_width()
    self.height = surface.get_height()
    glBindTexture(GL_TEXTURE_2D, self.id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    #self.width /= HEIGHT / 2
    #self.height /= HEIGHT / 2
  def Delete(self):
    glDeleteTextures(self.id)
  def __enter__(self):
    glBindTexture(GL_TEXTURE_2D, self.id)
    glEnable(GL_TEXTURE_2D)
  def __exit__(self, exc_type, exc_val, exc_tb):
    glDisable(GL_TEXTURE_2D)


def DrawPath(path):
  glBegin(GL_TRIANGLE_STRIP)
  lx = ly = None
  for x, y in path:
    if lx is None:
      glVertex(x, y, 0)
    else:
      dx = x - lx
      dy = y - ly
      n = 0.005 / math.hypot(dx, dy)
      dx *= n
      dy *= n
      glVertex(x + dy, y - dx, 0)
      glVertex(x - dy, y + dx, 0)
    lx = x
    ly = y
  glEnd()
