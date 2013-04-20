import math
import pygame
from OpenGL.GL import *

WIDTH, HEIGHT = 900.0, 600.0
RATIO = WIDTH / HEIGHT

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
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    self.width /= HEIGHT / 2
    self.height /= HEIGHT / 2
  def Delete(self):
    glDeleteTextures(self.id)
  def __enter__(self):
    glBindTexture(GL_TEXTURE_2D, self.id)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    return self
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


class ObjMesh(object):
  def __init__(self, filename):
    vertices = []
    texture_vertices = []
    faces = []
    for line in file(filename):
      if line[0] == '#':
        continue
      if line.startswith('v '):
        vert = map(float, line.split()[1:4])
        vertices.append(vert)
        continue
      if line.startswith('vt '):
        vert = map(float, line.split()[1:3])
        texture_vertices.append(vert)
        continue
      if line.startswith('f '):
        vtps = [tuple(map(int, vtp.split('/'))) for vtp in line.split()[1:4]]
        faces.append(vtps)
        continue

    print '%i vertices, %i tvertices, %i faces' % (len(vertices), len(texture_vertices), len(faces))

    vtp_seen = {}
    gl_vertices = []
    num_v = 0
    gl_indices = []
    for face in faces:
      for vtp in face:
        if vtp not in vtp_seen:
          v = vertices[vtp[0] - 1]
          vt = texture_vertices[vtp[1] - 1]
          gl_vertices += v
          gl_vertices += vt
          vtp_seen[vtp] = num_v
          num_v += 1
        gl_indices.append(vtp_seen[vtp])

    print '%i glverts, %i glindices, %i num_v' % (len(gl_vertices), len(gl_indices), num_v)

    self.vbo, self.ibo = glGenBuffers(2)
    self.vbuf = (ctypes.c_float * (num_v * 5))(self.gl_vertices)

    glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(self.vbuf), self.vbuf,
                 GL_STATIC_DRAW)
