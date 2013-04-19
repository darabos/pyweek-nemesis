# coding: utf8
import math
import random
import pygame
import sys
from OpenGL.GL import *

import rendering
import shapes
import ships
import crystals


WIDTH, HEIGHT = 900.0, 600.0
RATIO = WIDTH / HEIGHT

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
      glTranslate(sign * (x + RATIO - 0.5 * texture.width), -1 + 0.5 * texture.height, 0)
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
      if w > WIDTH * 0.6:
        words.pop()
        assert words
        self.textures.append(
          rendering.Texture(
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
        glTranslate(-RATIO + 0.5 * t.width + (0.8 if dialog.side == 'left' else 0.2), bgpos + 0.1 - 0.1 * i, 0)
        glScale(t.width, t.height, 1)
        self.quad.Render()
        glPopMatrix()
    glDisable(GL_BLEND)


class Game(object):

  def __init__(self):
    self.objects = []
    self.crystals = []
    self.shapes = []
    self.enemies = []
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
    glClearColor(0.0, 0.3, 0.6, 1)

    self.dialog = Dialog()
    self.crystals = crystals.Crystals(max_crystals=20, total_crystals=100)

    self.small_ship = ships.SmallShip(0, 0, 0.05)
    self.objects.append(self.small_ship)

    self.big_ship = ships.BigShip(0, 0, 0.2)
    self.objects.append(self.big_ship)

    for i in range(10):
      while True:
        x = random.uniform(-0.9, 0.9)
        y = random.uniform(-0.9, 0.9)
        if not (abs(x) < 0.25 and abs(y) < 0.25):
          break
      jellyship = ships.JellyFish(x, y, random.gauss(0.15, 0.02))
      self.enemies.append(jellyship)

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
      self.crystals.Render()
      for o in self.objects:
        o.Render()
      for o in self.enemies:
        o.Render()
      self.dialog.Render()
      pygame.display.flip()

  def GameSpace(self, x, y):
    return 2 * x / HEIGHT - RATIO, 1 - 2 * y / HEIGHT
  
  def Distance(self, ship1, ship2):
    return math.hypot(ship1.x - ship2.x, ship1.y - ship2.y)

  def Update(self, dt):
    self.time += dt
    self.crystals.Update(dt, self)
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
            [(c.x, c.y) for c in shape_path])
          self.shape_being_traced = self.shape_being_drawn
        else:
          # Otherwise just follow the mouse path.
          self.small_ship.path_func = ships.ShipPathFromWaypoints(
            (self.small_ship.x, self.small_ship.y), (0, 0),
            self.small_ship.drawing)
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

      if not self.big_ship.chasing_shapes:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
          # free movement
          target = self.GameSpace(*e.pos)
          nearest = self.big_ship.NearestTarget(target, self.shapes)
          if nearest:
            dist = math.hypot(nearest.x - target[0], nearest.y - target[1])
            if dist < 0.05:
              self.big_ship.target = nearest
              self.big_ship.path_func = ships.ShipPathFromWaypoints(
                (self.big_ship.x, self.big_ship.y), (0, 0),
                [(nearest.x, nearest.y)], 0.2)
            else:
              nearest = False
          if not nearest:
            self.big_ship.path_func = ships.ShipPathFromWaypoints(
              (self.big_ship.x, self.big_ship.y), (0, 0),
              [(target[0], target[1])], 0.2)
          self.big_ship.path_func_start_time = self.time

    for ship in [self.small_ship, self.big_ship]:
      if ship.path_func:
        (x, y, dx, dy, i) = ship.path_func(
          self.time - ship.path_func_start_time)
        ship.x = x
        ship.y = y
        if ship == self.small_ship and self.shape_being_traced:
          self.shape_being_traced.ShipVisited(i)


    if self.big_ship.InRangeOfTarget():
      shape = self.big_ship.target
      self.shapes.remove(shape)
      for c in shape.path:
        # TODO(alex): need to flag crystals earlier so they can't
        # get re-used for other paths, or delete earlier paths if a
        # later path reuses the same crystal
        self.crystals.remove(c)
      # TODO(alex): trigger animation on shape when it's being hauled in
      to_heal = min(max((self.big_ship.max_health - self.big_ship.health), 0), shape.score)
      self.big_ship.health += to_heal
      self.mana += 100 * (shape.score - to_heal)
      print 'mana is now %r' % self.mana
      print 'health is now %r' % self.big_ship.health
      self.big_ship.target = None
      self.big_ship.target_reevaluation = self.time + 0.5

    if self.big_ship.chasing_shapes:
      if self.time > self.big_ship.target_reevaluation:
        self.big_ship.target_reevaluation = self.time + 0.5
        nearest = self.big_ship.NearestTarget((self.big_ship.x,self.big_ship.y), self.shapes)
        if nearest and nearest != self.big_ship.target:
          self.big_ship.target = nearest
          self.big_ship.path_func = ships.ShipPathFromWaypoints(
            (self.big_ship.x, self.big_ship.y), (0, 0),
            [(nearest.x, nearest.y)], 0.2)
          self.big_ship.path_func_start_time = self.time
    
    for enemy in self.enemies:
      for ship in self.objects:
        if enemy.damage > 0 and self.Distance(enemy, ship) < (enemy.size + ship.size) / 2:
          ship.health -= enemy.damage
          print 'ouch, this hurts! %s\'s health is now %0.2f/%0.2f' % (ship.name, ship.max_health, ship.health)

    if self.big_ship.health <= 0:
      self.dialog.JumpTo('health-zero')
    
    if self.shape_being_traced:
      if self.shape_being_traced.DoneTracing():
        self.shapes.append(self.shape_being_traced)
        self.shape_being_traced = None      


if __name__ == '__main__':
  Game().Start()
