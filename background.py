import OpenGL
import math
from OpenGL.GL import *
import assets

class BackGround(object):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def Draw(self, dt):
        glDisable(GL_BLEND)
        glUseProgram(assets.BACKGROUND_PROGRAM)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_1D, assets.WAVE_TEXTURE)
        location = glGetUniformLocation(assets.BACKGROUND_PROGRAM, 'tex')
        glUniform1i(location, 0)

        location = glGetUniformLocation(assets.BACKGROUND_PROGRAM, 'offset')
        glUniform1f(location, dt%7)

        location = glGetUniformLocation(assets.BACKGROUND_PROGRAM, 'color')
        glUniform4f(location, 0., 0.3, 0.75, 1.)

        glBegin(GL_QUADS)
        glVertex(self.x[0], self.y[1])
        glVertex(self.x[0], self.y[0])
        glVertex(self.x[1], self.y[0])
        glVertex(self.x[1], self.y[1])
        glEnd()

        glUseProgram(0)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_1D,0)
