import OpenGL
import math
from OpenGL.GL import *
import assets

class BackGround(object):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def Draw(self, time, second_pass):
        glUseProgram(assets.BACKGROUND_PROGRAM)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_1D, assets.WAVE_TEXTURE)
        location = glGetUniformLocation(assets.BACKGROUND_PROGRAM, 'tex')
        glUniform1i(location, 0)

        location = glGetUniformLocation(assets.BACKGROUND_PROGRAM, 'offset')
        glUniform1f(location, time%100)

        location = glGetUniformLocation(assets.BACKGROUND_PROGRAM, 'color')
        glUniform4f(location, 0., 0.3, 0.75, 0.7)

        if second_pass:
            glDepthFunc(GL_LESS)
            glEnable(GL_BLEND)
        else:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_BLEND)
        glBegin(GL_QUADS)
        glVertex(self.x[0], self.y[1], -0.01)
        glVertex(self.x[0], self.y[0], -0.01)
        glVertex(self.x[1], self.y[0], -0.01)
        glVertex(self.x[1], self.y[1], -0.01)
        glEnd()
        if second_pass:
            glDepthFunc(GL_ALWAYS)
        else:
            glEnable(GL_DEPTH_TEST)

        glUseProgram(0)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_1D,0)
