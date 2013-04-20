import pygame
import OpenGL
import sys
from OpenGL.GL import *

import rendering


def Help(vshader_src, fshader_src):
    program = glCreateProgram()

    for kind, src, txt in ((GL_VERTEX_SHADER, vshader_src, 'vertex'),
                           (GL_FRAGMENT_SHADER, fshader_src, 'fragment')):
        if src:
            shader = glCreateShader(kind)
            glShaderSource(shader, [src])
            glCompileShader(shader)
            result = glGetShaderiv(shader, GL_COMPILE_STATUS)
            if not result:
                print ('shader %s compilation failed: %s'
                       % (txt, glGetShaderInfoLog(shader)))
                sys.exit(1)
            glAttachShader(program, shader)
            glDeleteShader(shader)
    glLinkProgram(program)
    glValidateProgram(program)

    return program

def BackGroundShader():

    data = (ctypes.c_ubyte * 5)()
    hl = 80
    for i, v in enumerate([0, hl, 0, hl, 0]):
        data[i] = v

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_1D, texture)
    glTexImage1D(GL_TEXTURE_1D, 0, 1, 8, 0, GL_RED, GL_UNSIGNED_BYTE, data)
    glTexParameter(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameter(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameter(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glBindTexture(GL_TEXTURE_1D, 0)

    global WAVE_TEXTURE
    WAVE_TEXTURE = texture

    global WATER_TEXTURE

    tex = glGenTextures(1)
    surface = pygame.image.load("art/texture/water.png")
    texture_size = surface.get_size()
    raw_data = pygame.image.tostring(surface, 'RGBA', False)

    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                   GL_LINEAR_MIPMAP_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameter(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, texture_size[0], texture_size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, raw_data)

    WATER_TEXTURE = tex

    background_fragment_shader = """\
#version 120

varying vec2 position;
uniform vec4 color;
uniform float offset;
uniform sampler1D tex;
uniform sampler2D water_tex;

void main(){
  float v = cos(offset + position.x) * sin ( offset + position.y);
  float w = sin(offset - position.x) * cos ( offset - position.y);
  v += sin(2 * offset + position.x) * cos ( 4 * offset - position.y);
  w += cos(0.5 * offset - position.x) * sin(7 * offset - position.y);
  float img = mix(v, w, 0.5);

  gl_FragColor = mix(color, vec4(0.0, 0.2, 0.9, 0.7), img);
}
"""
    background_vertex_shader = """\
#version 120

varying vec2 position;

void main() {
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
  gl_FrontColor = gl_Color;
  position = gl_Vertex.xy;
}

"""

    global BACKGROUND_PROGRAM
    BACKGROUND_PROGRAM = Help(background_vertex_shader, background_fragment_shader)

def CrystalShader():

    global CRYSTAL_TEXTURE

    tex = glGenTextures(1)
    surface = pygame.image.load("art/texture/crystal.png")
    texture_size = surface.get_size()
    raw_data = pygame.image.tostring(surface, 'RGBA', False)

    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                   GL_LINEAR_MIPMAP_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameter(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, texture_size[0], texture_size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, raw_data)

    CRYSTAL_TEXTURE = tex

    crystal_fragment_shader = """\
#version 120

varying vec2 position;
varying vec2 pos_tex;
uniform sampler2D crystal_tex;
uniform float alpha;

void main() {
  vec4 image = texture2D(crystal_tex, pos_tex);
  gl_FragColor = vec4(vec3(image.rgb), alpha);
}
"""
    crystal_vertex_shader = """
#version 120

varying vec2 position;
varying vec2 pos_tex;
 
void main() {
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
  gl_FrontColor = gl_Color;
  position = gl_Vertex.xy;
  pos_tex = gl_MultiTexCoord0.xy; 
}

"""
    global CRYSTAL_PROGRAM
    CRYSTAL_PROGRAM = Help(crystal_vertex_shader, crystal_fragment_shader)


class Meshes(object):
    @classmethod
    def Init(self):
        self.ship = rendering.ObjMesh(
            'models/ship/Ship.obj',
            rendering.Texture(pygame.image.load(
                    'models/ship/Ship.png'), mipmap=True),
            scale=[0.5, 0.5, 0.5],
            offset=[0.0, 0.0, 0.0])
        self.other_ship = rendering.ObjMesh(
            'models/other-ship/OtherShip.obj',
            rendering.Texture(pygame.image.load(
                    'models/other-ship/OtherShip.png'), mipmap=True),
            scale=[0.5, 0.5, 0.5],
            offset=[0.0, 0.0, 0.0])
        self.jellyfish = rendering.ObjMesh(
            'models/jellyfish/Jellyfish.obj',
            rendering.Texture(pygame.image.load(
                    'models/jellyfish/Jellyfish.png'), mipmap=True),
            scale=[0.2, 0.2, 0.2],
            offset=[0, 0, 0])
        self.kraken = rendering.ObjMesh(
            'models/kraken/Kraken.obj',
            rendering.Texture(pygame.image.load(
                    'models/kraken/Kraken.png'), mipmap=True),
            scale=[0.2, 0.2, 0.2],
            offset=[0, 0.1, 0])


def Init():
    BackGroundShader()
    CrystalShader()
    Meshes.Init()
