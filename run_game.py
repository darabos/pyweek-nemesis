# coding: utf8
import math
import pygame
import random
import sys
from OpenGL.GL import *

import rendering
import shapes


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

def ShipPathFromWaypoints(starting_location, starting_velocity, waypoints, acceleration=1):
  """
  Args:
    starting_location: tuple (x, y) ([-1, +1] again) of the starting
  position of the ship.
    starting_velocity: tuple (x,y) of the starting velocity of the ship in
  units per second.
    waypoints: List of tuples (x, y) of points the ship should pass through.

  Returns:
    A callable that takes a single argument 'time' and returns a tuple (x,
  y, dx, dy) of the position and velocity of the ship at the given time,
  assuming the ship was at the given starting location with the given
  starting velocity at time 0 and is moving to pass (exactly) through each
  given waypoint in order, with arbitrary velocity except at the final
  waypoint where the velocity should be (0, 0).

  (Thus, when passed time=0, it should return starting_location,
  starting_velocity. For any time >= the time it takes to reach the final
  waypoint, it should return (final_waypoint, 0, 0).)
  """
  waypoints_with_starting_location = [starting_location] + waypoints
  waypoint_pairs = [(waypoints_with_starting_location[i], waypoints[i]) for i in range(len(waypoints))]
  distances = [math.hypot(end[0] - start[0], end[1] - start[1])
               for (start, end) in waypoint_pairs]
  total_distance = sum(distances)
  total_time = math.sqrt(total_distance / acceleration) * 2
  braking_time = total_time / 2
  velocity_at_braking_time = braking_time * acceleration
  distance_at_braking_time = velocity_at_braking_time * braking_time / 2

  def curve(progress):
    distance = progress * total_distance
    accumulator = 0
    for i in range(len(distances)):
      if distance < accumulator + distances[i]:
        start, end = waypoint_pairs[i]
        small_progress = (distance - accumulator) / distances[i]
        return (
          start[0] + (end[0] - start[0]) * small_progress,
          start[1] + (end[1] - start[1]) * small_progress,
          (end[0] - start[0]) / distances[i],
          (end[1] - start[1]) / distances[i],
          i)
      accumulator += distances[i]
    return waypoints[-1] + (0, 0, i + 1)

  def control(time):
    distance = 0
    velocity = 0
    if time < 0:
      distance = 0
      velocity = 0
    elif time > total_time:
      distance = total_distance
      velocity = 0
    else:
      if time < braking_time:
        velocity = acceleration * time
        distance = time * velocity / 2
      else:
        velocity = velocity_at_braking_time - (time - braking_time) * acceleration
        distance = distance_at_braking_time + (time - braking_time) * (velocity_at_braking_time + velocity) / 2
    progress = distance / total_distance
    (locationX, locationY, directionX, directionY, index) = curve(progress)
    return (
      locationX,
      locationY,
      directionX * velocity,
      directionY * velocity,
      index)

  return control


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


class Ship(object):
  def __init__(self, x, y, size):
    self.x = x
    self.y = y
    self.vbo = rendering.Quad(size, size)
  def Render(self):
    glColor(1, 1, 1, 1)
    glPushMatrix()
    glTranslatef(self.x, self.y, 0)
    self.vbo.Render()
    glPopMatrix()

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
    texture = self.GetTexture()
    with texture:
      glPushMatrix()
      if self.side == 'left':
        glTranslate(-RATIO + 1 / 3., -1 + 1 / 3., 0)
      elif self.side == 'right':
        glTranslate(RATIO - 1 / 3., -1 + 1 / 3., 0)
      glScale(2 / 3., 2 / 3., 1)
      self.quad.Render()
      glPopMatrix()
  def GetTexture(self):
    filename = 'art/portraits/' + self.character
    if self.face:
      filename += '-' + self.face
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
    Father(u'Here we are, my son. The Sea of Good and Bad.',
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
    self.paused = False
    self.textures = []
    self.quad = rendering.Quad(1.0, 1.0)
    pygame.font.init()
    self.font = pygame.font.Font('OpenSans-Regular.ttf', 20)

  def State(self, label):
    for i, d in enumerate(self.dialog):
      if d.label == label:
        return i
    raise ValueError('Label {} not found.'.format(label))

  def Pause(self, game):
    dialog = self.dialog[self.state]
    if self.paused:
      for e in pygame.event.get():
        if e.type == pygame.KEYUP or e.type == pygame.MOUSEBUTTONUP:
          self.state += 1
          for t in self.textures:
            t.Delete()
          self.textures = []
          if self.dialog[self.state].label:
            self.paused = False
    else:
      if dialog.trigger(game):
        self.paused = True

  def RenderFont(self, text, antialias, color, background):
    return self.font.render(text, antialias, color, background)
  def Render(self):
    if not self.paused:
      return
    glColor(1, 1, 1, 1)
    dialog = self.dialog[self.state]
    if not self.textures:
      words = []
      for word in dialog.text.split():
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
    # White block.
    glPushMatrix()
    glTranslate(0, -0.8, 0)
    glScale(2 * RATIO, 0.4, 1)
    self.quad.Render()
    glPopMatrix()
    # Face.
    dialog.RenderFace()
    # Text.
    glEnable(GL_BLEND)
    glBlendFunc(GL_ZERO, GL_SRC_COLOR)
    for i, t in enumerate(self.textures):
      with t:
        glPushMatrix()
        glTranslate(-RATIO + 0.5 * t.width / 300. + (0.7 if dialog.side == 'left' else 0.1), -0.7 - 0.1 * i, 0)
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
    self.small_ship = Ship(0, 0, 0.05)
    self.small_ship.drawing = []
    self.small_ship.path_func = None
    self.small_ship.path_func_start_time = None
    self.objects.append(self.small_ship)
    self.big_ship = Ship(0, 0, 0.2)
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
      dt = clock.tick()
      if not self.dialog.Pause(self):
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
    dt *= 0.001
    self.time += dt
    for e in pygame.event.get():
      if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit(0)
      if e.type == pygame.MOUSEBUTTONUP and e.button == 3:
        self.big_ship.path_func = ShipPathFromWaypoints((self.big_ship.x, self.big_ship.y), (0, 0), [self.GameSpace(*e.pos)], 0.1)
        self.big_ship.path_func_start_time = self.time

      if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
        shape_path = shapes.ShapeFromMouseInput(
          self.small_ship.drawing, self.crystals)
        if self.shape_being_drawn.CompleteWithPath(shape_path):
          # If it's a valid shape, the ship will now trace the path to
          # activate the shape.
          self.small_ship.path_func = ShipPathFromWaypoints(
            (self.small_ship.x, self.small_ship.y), (0, 0),
            [(c.x, c.y) for c in shape_path], 10)
          self.lines_drawn += 1
          self.shape_being_traced = self.shape_being_drawn
        else:
          # Otherwise just move to the final location.
          self.small_ship.path_func = ShipPathFromWaypoints(
            (self.small_ship.x, self.small_ship.y), (0, 0),
            [self.small_ship.drawing[-1]], 10)
        self.small_ship.path_func_start_time = self.time
        self.shape_being_drawn = None
        self.small_ship.drawing = []

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
        if ship == self.small_ship and self.shape_being_traced:
          self.shape_being_traced.ShipVisited(i)
        ship.x = x
        ship.y = y

    if self.shape_being_traced:
      if self.shape_being_traced.DoneTracing():
        self.shapes.append(self.shape_being_traced)
        self.shape_being_traced = None


if __name__ == '__main__':
  Game().Start()
