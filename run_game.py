# coding: utf8
import math
import pygame
import random
import sys
from OpenGL.GL import *

import rendering
import shapes
import ships


WIDTH, HEIGHT = 900.0, 600.0
RATIO = WIDTH / HEIGHT

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
    DrawCrystal(self.x, self.y, 0.01, 0.01)


class Jellyship(object):
  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.quad = rendering.Quad(0.2, 0.2)
    self.texture = rendering.Texture(pygame.image.load('Jellyfish.png'))
  def Render(self):
    glPushMatrix()
    glTranslatef(self.x, self.y, 0)
    with self.texture:
      self.quad.Render()
    glPopMatrix()


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
    x = math.exp(-10 * self.t)
    sign = 1 if self.side == 'right' else -1
    glPushMatrix()
    glTranslate(sign * (x + RATIO - 1 / 3.), -1 + 1 / 3., 0)
    glScale(2 / 3., 2 / 3., 1)
    with self.GetTexture('bg') as texture:
      self.quad.Render()
    with self.GetTexture(self.face) as texture:
      glPushMatrix()
      lx = math.exp(-10 * max(0.125, self.t))
      glRotate(100 * lx * math.sin(-11 * lx), 0, 0, -sign)
      self.quad.Render()
      glPopMatrix()
    with self.GetTexture('fg') as texture:
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
           trigger=lambda game: game.mana > 0),
    Father(u'Let us collect at least 1,000,000 so it feeds the whole family!'),
    Kid(u'Look, jellyfish! Can they speak?', face='wonder', label='look-jellyfish',
        trigger=lambda game: game.mana >= 10000),
    Jellyfish(u'Yes we can, tasty human!'),
    Father(u'Keep the Needle away from them! I will handle these beasts.'),
    Kid(u'What was that? A ship under the water snatched our Mana!',
        label='what-was-that', face='scared',
        trigger=lambda game: False),
    Father(u'It’s an Undership!'),
    Father(u'On the Sea of Good and Bad our reflections have their own minds.'),
    Father(u'And they will steal our dinner if we let them!'),
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
    pygame.font.init()
    self.font = pygame.font.Font('OpenSans-Regular.ttf', 20)
    self.RenderText()

  def State(self, label):
    for i, d in enumerate(self.dialog):
      if d.label == label:
        return i
    raise ValueError('Label {} not found.'.format(label))

  def Update(self, dt, game):
    dialog = self.dialog[self.state]
    if self.prev.t > 0:
      self.prev.t -= dt
      if self.prev.t < 0:
        self.RenderText()
    elif self.paused:
      dialog.t = min(0.5, dialog.t + dt)
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
      if w > WIDTH * 0.6:
        words.pop()
        assert words
        self.textures.append(
          renderingTexture(
            self.RenderFont(' '.join(words), antialias=True,
                            color=(0, 0, 0), background=(255, 255, 255))))
        words = [word]
    self.textures.append(
      rendering.Texture(
        self.RenderFont(' '.join(words), antialias=True,
                        color=(0, 0, 0), background=(255, 255, 255))))

  def Render(self):
    if not self.paused and self.prev.t <= 0:
      return
    glColor(1, 1, 1, 1)
    if self.prev.t > 0:
      dialog = self.prev
    else:
      dialog = self.dialog[self.state]
    # White block.
    glPushMatrix()
    bgpos = -0.8 - 0.4 * math.exp(-10 * dialog.t)
    glTranslate(0, bgpos, 0)
    glScale(2 * RATIO, 0.4, 1)
    self.quad.Render()
    glPopMatrix()
    # Face.
    dialog.RenderFace()
    # Text.
    for i, t in enumerate(self.textures):
      with t:
        glBlendFunc(GL_ZERO, GL_SRC_COLOR)
        glPushMatrix()
        glTranslate(-RATIO + 0.5 * t.width / 300. + (0.8 if dialog.side == 'left' else 0.2), bgpos + 0.1 - 0.1 * i, 0)
        glScale(t.width / 300., t.height / 300., 1)
        self.quad.Render()
        glPopMatrix()
    glDisable(GL_BLEND)


class Game(object):

  def __init__(self):
    self.objects = []
    self.crystals = []
    self.shapes = []
    self.lines_drawn = 0
    self.mana = 0

  def Start(self):
    self.Init()
    self.Loop()

  def Init(self):
    pygame.init()
    pygame.display.set_mode((int(WIDTH), int(HEIGHT)), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption('Nemesis')
    glViewport(0, 0, int(WIDTH), int(HEIGHT))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-RATIO, RATIO, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)

    self.dialog = Dialog()
    for i in range(100):
      crystal = Crystal(random.uniform(-1, 1), random.uniform(-1, 1))
      self.crystals.append(crystal)

    self.small_ship = ships.Ship(0, 0, 0.05)
    self.small_ship.drawing = []
    self.small_ship.path_func = None
    self.small_ship.path_func_start_time = None
    self.objects.append(self.small_ship)

    self.big_ship = ships.BigShip(0, 0, 0.2)
    self.big_ship.chasing_shapes = True
    self.big_ship.target = None
    self.big_ship.target_reevaluation = 0
    self.big_ship.path_func = None
    self.big_ship.path_func_start_time = None
    self.objects.append(self.big_ship)

    self.jelly_ship = Jellyship(-0.5, 0.5)
    self.objects.append(self.jelly_ship)

    # Track in-progress shapes.
    # Shape being drawn right now:
    self.shape_being_drawn = None
    # Shape being traced by the small ship:
    self.shape_being_traced = None

  def Loop(self):
    clock = pygame.time.Clock()
    self.time = 0
    while True:
      dt = 0.001 * clock.tick()
      self.dialog.Update(dt, self)
      if not self.dialog.paused:
        self.Update(dt)
      glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
      glColor(1, 1, 1, 1)
      rendering.DrawPath(self.small_ship.drawing)
      if self.shape_being_drawn:
        self.shape_being_drawn.Render()
      if self.shape_being_traced:
        self.shape_being_traced.Render()
      for o in self.shapes:
        o.Render()
      for o in self.crystals:
        o.Render()
      for o in self.objects:
        o.Render()
      self.dialog.Render()
      pygame.display.flip()

  def GameSpace(self, x, y):
    return 2 * x / HEIGHT - RATIO, 1 - 2 * y / HEIGHT

  def Update(self, dt):
    self.time += dt
    for e in pygame.event.get():
      if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit(0)

      if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
        shape_path = shapes.ShapeFromMouseInput(
          self.small_ship.drawing, self.crystals)
        if self.shape_being_drawn.CompleteWithPath(shape_path):
          # If it's a valid shape, the ship will now trace the path to
          # activate the shape.
          self.small_ship.path_func = ships.ShipPathFromWaypoints(
            (self.small_ship.x, self.small_ship.y), (0, 0),
            [(c.x, c.y) for c in shape_path], 5)
          self.shape_being_traced = self.shape_being_drawn
        else:
          # Otherwise just follow the mouse path.
          self.small_ship.path_func = ships.ShipPathFromWaypoints(
            (self.small_ship.x, self.small_ship.y), (0, 0),
            self.small_ship.drawing, 5)
          self.shape_being_traced = None
        self.small_ship.path_func_start_time = self.time
        self.shape_being_drawn = None
        self.small_ship.drawing = []
        self.lines_drawn += 1

      if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
        self.small_ship.drawing = [self.GameSpace(*e.pos)]
        self.shape_being_drawn = shapes.Shape(self)
        shape_path = shapes.ShapeFromMouseInput(
          self.small_ship.drawing, self.crystals)

      if e.type == pygame.MOUSEMOTION and e.buttons[0]:
        self.small_ship.drawing.append(self.GameSpace(*e.pos))
        # TODO(alex): Updating while in progress is nice, but too
        # now. Need to incrementally build the path for this to work.
        #shape_path = shapes.ShapeFromMouseInput(
        #  self.small_ship.drawing, self.crystals)
        #self.shape_being_drawn.UpdateWithPath(shape_path)

    for ship in [self.small_ship, self.big_ship]:
      if ship.path_func:
        (x, y, dx, dy, i) = ship.path_func(
          self.time - ship.path_func_start_time)
        ship.x = x
        ship.y = y
        if ship == self.small_ship and self.shape_being_traced:
          self.shape_being_traced.ShipVisited(i)

    if self.big_ship.chasing_shapes:
      if self.big_ship.InRangeOfTarget():
        shape = self.big_ship.target
        self.shapes.remove(shape)
        for c in shape.path:
          # TODO(alex): need to flag crystals earlier so they can't
          # get re-used for other paths, or delete earlier paths if a
          # later path reuses the same crystal
          self.crystals.remove(c)
        # TODO(alex): trigger animation on shape when it's being hauled in
        self.mana += 100 * shape.score
        print 'mana is now %r' % self.mana
        self.big_ship.target = None
        self.big_ship.target_reevaluation = self.time + 0.5

      if self.time > self.big_ship.target_reevaluation:
        self.big_ship.target_reevaluation = self.time + 0.5
        nearest = self.big_ship.NearestTarget(self.shapes)
        if nearest and nearest != self.big_ship.target:
          self.big_ship.target = nearest
          self.big_ship.path_func = ships.ShipPathFromWaypoints(
            (self.big_ship.x, self.big_ship.y), (0, 0),
            [(nearest.x, nearest.y)], 0.2)
          self.big_ship.path_func_start_time = self.time

    if self.shape_being_traced:
      if self.shape_being_traced.DoneTracing():
        self.shapes.append(self.shape_being_traced)
        self.shape_being_traced = None


if __name__ == '__main__':
  Game().Start()
