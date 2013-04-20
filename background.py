import OpenGL
from OpenGL.GL import *
import assets

class BackGround(object):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def Draw(self):
        glUseProgram(assets.BACKGROUND_PROGRAM)

        location = glGetUniformLocation(assets.BACKGROUND_PROGRAM, 'color')
        glUniform4f(location, 0., 0., 0., 1.)

        #glColor(self.color[0], self.color[1], self.color[2])
        glBegin(GL_QUADS)
        glVertex(self.x[0], self.y[1])
        glVertex(self.x[0], self.y[0])
        glVertex(self.x[1], self.y[0])
        glVertex(self.x[1], self.y[1])
        glEnd()

        glUseProgram(0)
