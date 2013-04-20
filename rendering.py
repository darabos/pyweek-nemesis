import math
import pygame
from OpenGL.GL import *

import assets

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

  def RenderCrystal(self, alpha):
    F = ctypes.sizeof(ctypes.c_float)
    FP = lambda x: ctypes.cast(x * F, ctypes.POINTER(ctypes.c_float))
    glBindBuffer(GL_ARRAY_BUFFER, self.id)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    glUseProgram(assets.CRYSTAL_PROGRAM)
    glEnable(GL_TEXTURE_2D)

    location = glGetUniformLocation(assets.CRYSTAL_PROGRAM, 'alpha')
    glUniform1f(location, alpha)

    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, assets.CRYSTAL_TEXTURE)
    location = glGetUniformLocation(assets.CRYSTAL_PROGRAM, 'crystal_tex')
    glUniform1i(location, 0)

    glVertexPointer(3, GL_FLOAT, 5 * F, FP(0))
    glTexCoordPointer(2, GL_FLOAT, 5 * F, FP(3))
    glDrawArrays(GL_QUADS, 0, 4)

    glUseProgram(0)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)


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
  def __init__(self, filename, texture):
    self.texture = texture

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

    print 'calculating normals'
    normals = [[0, 0, 0, 0]] * len(vertices)
    for face in faces:
      v0 = vertices[face[0][0] - 1]
      v1 = vertices[face[1][0] - 1]
      v2 = vertices[face[2][0] - 1]
      dv = [x - y for x, y in zip(v1, v0)]
      dw = [x - y for x, y in zip(v2, v0)]
      n = [dv[1] * dw[2] - dv[2] * dw[1],
           dv[2] * dw[0] - dv[0] * dw[2],
           dv[0] * dw[1] - dv[1] * dw[0]]
      for i in xrange(3):
        normals[face[i][0] - 1] = [
          x + y for x, y in zip(normals[face[i][0] - 1], n + [1])]

    print 'normalizing normals'
    norm_normals = []
    for n in normals:
      n[0] /= n[3]
      n[1] /= n[3]
      n[2] /= n[3]
      d = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
      n[0] /= d
      n[1] /= d
      n[2] /= d
      norm_normals.append(n[:3])

    print 'filling buffers'
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
          n = norm_normals[vtp[0] - 1]
          gl_vertices += n
          vtp_seen[vtp] = num_v
          num_v += 1
        gl_indices.append(vtp_seen[vtp])

    print '%i glverts, %i glindices, %i num_v' % (len(gl_vertices), len(gl_indices), num_v)

    self.vbo, self.ibo = glGenBuffers(2)
    vbuf = (ctypes.c_float * (num_v * 8))()
    for i, v in enumerate(gl_vertices):
      vbuf[i] = v
    ibuf = (ctypes.c_uint * len(gl_indices))()
    for i, v in enumerate(gl_indices):
      ibuf[i] = v

    glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(vbuf), vbuf,
                 GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, ctypes.sizeof(ibuf), ibuf,
                 GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    self.num_vert = len(gl_indices)
    self.r = 0

  def Render(self):
    F = ctypes.sizeof(ctypes.c_float)
    FP = lambda x: ctypes.cast(x * F, ctypes.POINTER(ctypes.c_float))
    glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)

    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)

    glVertexPointer(3, GL_FLOAT, 8 * F, FP(0))
    glTexCoordPointer(2, GL_FLOAT, 8 * F, FP(3))
    glNormalPointer(GL_FLOAT, 8 * F, FP(5))
    self.r += 0.1

    glLight(GL_LIGHT0, GL_POSITION, [-0.577, 0.577, 0.577, 0])
    glLight(GL_LIGHT0, GL_SPECULAR, [0, 0, 0, 0])
    glLight(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 0])
    glLight(GL_LIGHT0, GL_AMBIENT, [0, 0, 0, 0])
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glPushMatrix()
    glRotate(self.r, 0, 1, 0)
    glScale(0.5, 0.5, 0.5)
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    with self.texture:
      glDrawElements(GL_TRIANGLES, self.num_vert, GL_UNSIGNED_INT, None)
    glPopMatrix()
    glDisable(GL_LIGHT0)
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY)
    glDisableClientState(GL_NORMAL_ARRAY)
