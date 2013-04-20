import pygame
import OpenGL
import sys
from OpenGL.GL import *

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

    background_fragment_shader = """\
#version 120

varying vec2 position;
uniform vec4 color;

void main(){
  gl_FragColor = mix(color, vec4(1, 0, 0, 1), 0.3);
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
  float image = texture2D(crystal_tex, pos_tex).r;
  gl_FragColor = vec4(vec3(image), alpha);
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


def Init():
    BackGroundShader()
    CrystalShader()
