# coding: utf8
import rendering
import pygame
import math
import sys
from OpenGL.GL import *

class DialogLine(object):
  textures = {}
  side = 'left'
  quad = None

  def __init__(self, text, label='', face='', trigger=None):
    self.text = text
    self.label = label
    self.face = face
    self.trigger = trigger

  def RenderFace(self):
    if DialogLine.quad is None:
      DialogLine.quad = rendering.Quad(1.0, 1.0)
    glColor(1, 1, 1, 1)
    x = math.exp(-20 * self.t)
    sign = 1 if self.side == 'right' else -1
    with self.GetTexture(self.face) as texture:
      glPushMatrix()
      glTranslate(sign * (x + rendering.RATIO - 0.5 * texture.width), -1 + 0.5 * texture.height, 0)
      glScale(texture.width, texture.height, 1)
      self.quad.Render()
      glPopMatrix()

  def GetTexture(self, which):
    filename = 'art/portraits/' + self.character
    if which:
      filename += '-' + which
    filename += '.png'
    if filename not in self.textures:
      self.textures[filename] = rendering.Texture(pygame.image.load(filename))
    return self.textures[filename]

class Father(DialogLine):
  character = 'Father'
class Kid(DialogLine):
  character = 'Kid'
  side = 'right'
class Jellyfish(DialogLine):
  character = 'Jellyfish'


class Dialog(object):
  dialog = [
    Father(u'Here we are, my daughter. The Sea of Good and Bad.',
           label='here-we-are', trigger=lambda game: game.time > 1),
    Father(u'Get in the Needle and let’s collect some Mana!'),
    Kid(u'I get to control the Needle?!', face='wonder'),
    Father(u'That’s right. Just draw lines with the mouse and the Needle will follow them.'),
    Father(u'We’re here to collect Mana, remember?', label='to-collect-mana',
           trigger=lambda game: game.lines_drawn > 2),
    Father(u'Weave the Needle through three white crystals to form a triangle, will you?'),
    Father(u'Well done. That’s a perfect triangle!', label='just-right-click',
           trigger=lambda game: game.shapes),
    Father(u'Perfect shapes provide the most Mana.'),
    Father(u'Let’s wait a bit for it to fully charge. Let me know when it’s ready.'),
    Father(u'Just right click on the shape and I’ll come and haul it in.'),
    Father(u'Oh, your mother will summon us a delicious dinner using this Mana when we get home.',
           label='oh-your-mother', face='laughing',
           trigger=lambda game: game.big_ship.mana > 0),
    Father(u'Let us collect at least 1,000,000 so it feeds the whole family!'),
    Kid(u'Look, jellyfish! Can they speak?', face='wonder', label='look-jellyfish',
        trigger=lambda game: game.big_ship.mana >= 1000),
    Jellyfish(u'Yes we can, tasty human!'),
    Father(u'Keep the Needle away from them! I will handle these beasts.'),
    Kid(u'What was that? A ship under the water snatched our Mana!',
        label='what-was-that', face='scared',
        trigger=lambda game: False),
    Father(u'It’s an Undership!'),
    Father(u'On the Sea of Good and Bad our reflections have their own minds.'),
    Father(u'And they will steal our dinner if we let them!'),
    Father(u'GAME OVER', label='game-over', trigger=lambda game: False),  # Sentinel.
    Father(u'I\'m sinking! I\'m sinking! GAME OVER', label='health-zero', trigger=lambda game: True),
    Father(u'GAME OVER', label='game-over', trigger=lambda game: False),  # Sentinel.
  ]

  def __init__(self):
    self.state = self.State('here-we-are')
    self.dialog[self.state].t = 0
    self.prev = Father('')
    self.prev.t = 0
    self.paused = False
    self.textures = []
    self.quad = rendering.Quad(1.0, 1.0)
    self.background = rendering.Texture(pygame.image.load('art/dialog-background.png'))
    pygame.font.init()
    self.font = pygame.font.Font('OpenSans-Regular.ttf', 20)
    self.RenderText()

  def State(self, label):
    for i, d in enumerate(self.dialog):
      if d.label == label:
        return i
    raise ValueError('Label {} not found.'.format(label))

  def JumpTo(self, label):
    self.prev = self.dialog[self.state]
    self.state = self.State(label)
    self.dialog[self.state].t = 0
    self.RenderText()

  def Update(self, dt, game):
    dialog = self.dialog[self.state]

    # animating dialogs for 0.25 sec (prev out, dialog in)
    if self.prev.t > 0:
      self.prev.t -= dt
      if self.prev.t < 0:
        self.RenderText()
    elif self.paused:
      dialog.t = min(0.25, dialog.t + dt)

    if self.paused:
      for e in pygame.event.get():
        if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit(0)
        elif e.type == pygame.KEYUP or e.type == pygame.MOUSEBUTTONUP:
          self.prev = dialog
          self.state += 1
          self.dialog[self.state].t = 0
          if self.dialog[self.state].label:
            self.paused = False
          elif self.dialog[self.state].character == self.prev.character:
            self.RenderText()
            self.dialog[self.state].t = self.prev.t
            self.prev.t = 0
    else:
      if dialog.trigger(game):
        self.paused = True

  def RenderFont(self, text, antialias, color, background):
    return self.font.render(text, antialias, color, background)

  def RenderText(self):
    text = self.dialog[self.state].text
    for t in self.textures:
      t.Delete()
    self.textures = []
    words = []
    for word in text.split():
      words.append(word)
      w, h = self.font.size(' '.join(words))
      if w > rendering.WIDTH * 0.6:
        words.pop()
        assert words
        self.textures.append(
          rendering.Texture(
            self.RenderFont(' '.join(words), antialias=True,
                            background=(0, 0, 0), color=(255, 255, 255))))
        words = [word]
    self.textures.append(
      rendering.Texture(
        self.RenderFont(' '.join(words), antialias=True,
                        background=(0, 0, 0), color=(255, 255, 255))))

  def Render(self):
    if not self.paused and self.prev.t <= 0:
      return
    glColor(1, 1, 1, 1)
    if self.prev.t > 0:
      dialog = self.prev
    else:
      dialog = self.dialog[self.state]
    # Background.
    glPushMatrix()
    bgpos = -1 + 0.5 * self.background.height * (1 - math.exp(-10 * dialog.t))
    glTranslate(0, bgpos, 0)
    glScale(self.background.width, self.background.height, 1)
    with self.background:
      self.quad.Render()
    glPopMatrix()
    # Face.
    dialog.RenderFace()
    # Text.
    for i, t in enumerate(self.textures):
      with t:
        glBlendFunc(GL_ZERO, GL_ONE_MINUS_SRC_COLOR)
        glPushMatrix()
        glTranslate(-rendering.RATIO + 0.5 * t.width + (0.8 if dialog.side == 'left' else 0.2), bgpos + 0.1 - 0.1 * i, 0)
        glScale(t.width, t.height, 1)
        self.quad.Render()
        glPopMatrix()
    glDisable(GL_BLEND)
