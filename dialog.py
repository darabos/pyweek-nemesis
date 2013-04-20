# coding: utf8
import math
import pygame
import random
import rendering
import ships
import sys
from OpenGL.GL import *

class DialogLine(object):
  textures = {}
  side = 'left'
  quad = None

  def __init__(self, text, label='', face='', trigger=None, action=None):
    self.text = text
    self.label = label
    self.face = face
    self.trigger = trigger
    self.action = action
    self.t = 0

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
class Kraken(DialogLine):
  character = 'Kraken'
  side = 'right'
class AuntMenace(DialogLine):
  character = 'Menace'
  side = 'right'
class Tom(DialogLine):
  character = 'Tom'
class Prince(DialogLine):
  character = 'Prince'
  side = 'right'
class Victoria(DialogLine):
  character = 'Victoria'
class KidsNemesis(DialogLine):
  character = 'Kid-Nemesis'
class FathersNemesis(DialogLine):
  character = 'Father-Nemesis'
  side = 'right'


class HUD(rendering.Texture):

  def __init__(self, filename):
    rendering.Texture.__init__(self, pygame.image.load(filename))
    self.lastvalue = None
    self.text = None

  def Render(self, x, value):
    glColor(1, 1, 1, 1)
    with self as t:
      glPushMatrix()
      glTranslate(-rendering.RATIO + 0.5 * t.width + x, 1 - 0.5 * t.height, 0)
      glScale(t.width, t.height, 1)
      Dialog.quad.Render()
      glPopMatrix()
    if self.lastvalue != value:
      if self.text:
        self.text.Delete()
      self.lastvalue = value
      self.text = rendering.Texture(Dialog.RenderFont(self.lastvalue))
    with self.text as t:
      glBlendFunc(GL_ZERO, GL_ONE_MINUS_SRC_COLOR)
      glPushMatrix()
      glTranslate(-0.5 * t.width - rendering.RATIO + 0.52 + x, 0.85, 0)
      glScale(t.width, t.height, 1)
      Dialog.quad.Render()
      glPopMatrix()

def OnEdge(z):
  while True:
    x = random.uniform(-1.5, 1.5)
    y = random.uniform(-1.5, 1.5)
    if not (abs(x) < 1.2 and abs(y) < 1.2):
      return x, y, z

def Victory(game):
  for ship in game.ships:
    if ship.faction != 1:
      return False
  return True

class Dialog(object):
  dialog = [
Father(u'Here we are, my daughter. The Sea of Good and Bad.',
       label='here-we-are', trigger=lambda game: game.time > 1),
Father(u'Get in the Needle and let’s collect some Mana!'),
Kid(u'I get to pilot the Needle?!', face='wonder'),
Father(u'That’s right. Just draw lines with the mouse and the Needle will follow them.'),
Father(u'You can hold either the left mouse button or the SHIFT key.'),

Father(u'We’re here to collect Mana, remember?',
       trigger=lambda game: game.lines_drawn > 2),
Father(u'Weave the Needle through three white crystals to form a triangle, will you?',
       action=lambda game: game.crystals.SetState('OneTriangle')),

Father(u'Well done. That’s a perfect triangle!',
       trigger=lambda game: game.shapes),
Father(u'Perfect shapes provide the most Mana.'),
Father(u'Just right click on the shape and I’ll come and haul it in.'),
Father(u'Or use A, S, D and W to guide me there if you prefer.'),

Father(u'Oh, your mother will summon us a delicious dinner using this Mana when we get home!',
       face='laughing', trigger=lambda game: game.father_ship.mana > 0),
Father(u'Let us collect at least 1,000 so it feeds the whole family.'),
Father(u'Bigger regular shapes with more crystals give even more Mana.'),
Father(u'And arcane shapes, like a pentagram, yield twice as much.'),
Kid(u'Wow! I’ll make a dodecagram then!', face='wonder',
       action=lambda game: game.crystals.SetState('KeepMax')),

Kid(u'Look, jellyfish! Can they speak?', face='wonder',
    trigger=lambda game: game.father_ship.mana >= 1000),
Jellyfish(u'Yes we can, tasty human!'),
Father(u'Keep the Needle away from them! I will handle these beasts. We can use some mana to fight them!',
       action=lambda game: [game.AddEnemy(ships.JellyFish(*OnEdge(random.gauss(0.15, 0.03)))) for i in range(6)]),

Kid(u'What was that? A ship under the water snatched our Mana!',
    face='scared', trigger=Victory),
Father(u'It’s an Undership!'),
Father(u'On the Sea of Good and Bad our reflections have their own minds.'),
Father(u'And they will steal our dinner if we let them!',
        action=lambda game: [game.AddEnemy(ships.OtherBigShip(*OnEdge(0.2), AI='Chasing shapes'))]),

Kid(u'Victory! The Undership is retreating!', face='wonder', trigger=Victory),
Father(u'All the bad thoughts we think sink to the bottom of the water and form your Nemesis and mine.'),
Father(u'They are piloting the Undership and they will be back...',
       action=lambda game: game.StartTimer()),

AuntMenace(u'What a lovely family!', face='laughing', trigger=lambda game: game.GetTimer() > 10),
AuntMenace(u'Thank you for showing the way to this rich field of crystals!'),
Father(u'Creta, unfold your sails.'),
Father(u'Your aunt knows no mercy. We have to defend ourselves!',
       action=lambda game: game.AddEnemy(ships.OtherBigShip(*OnEdge(0.3)))),

AuntMenace(u'I see you’re not a child anymore, Creta.', trigger=Victory),
AuntMenace(u'Maybe one day you’ll pilot my Needle and we will terrorize the harbors together.', face='laughing'),
AuntMenace(u'Until then!', face='laughing'),
Kid(u'Why does Aunt Menace have to be like that...', face='scared'),
Father(u'They say the people from Under walk the Earth at new moon.'),
Father(u'If they find an unattended baby, they will steal it and put its Nemesis in the cradle.'),
Kid(u'So there is a good Aunt Menace under the sea?!', face='scared'),
Father(u'That is not the moral of this story...', face='puzzled'),
Father(u'Look. There is another pack of jellyfish coming!'),
Jellyfish(u'It is your lucky day, my delicious friends!'),
Jellyfish(u'You will be somebody else’s dinner tonight.'),
Kid(u'What is that behind them?!', face='scared'),
Father(u'The Kraken!',
       action=lambda game: game.AddEnemy(ships.Kraken(-0.1, -0.8, 0.5))),

Kraken(u'Get out of my way, little one!', trigger=Victory),
Kraken(u'Let me take my prey to the Kingdom Under the Waves.'),
Tom(u'Not so fast, Kraken!'),
Tom(u'I will fight along these brave sailors and make our stand against your evil.',
       action=lambda game: [game.AddEnemy(ships.Kraken(-0.1, -0.8, 0.5)),
                            game.AddAlly(ships.OurBigShip(*OnEdge(0.3)))]),

Father(u'Thank you, stranger.', trigger=Victory),
Father(u'What a day! I wonder what stirred the old beast...'),
Tom(u'Well, about that...'),
Kid(u'Underships coming in fast from starboard!', face='scared'),
Tom(u'Uh-oh, looks like my Nemesis has caught up with me.'),
Tom(u'Which side will you take, brave sailors?'),
Father(u'No Underman is my friend.'),
Tom(u'Then prepare to meet the Prince of Turtles in combat!',
    action=lambda game: game.AddEnemy(ships.OtherBigShip(*OnEdge(0.3)))),

Prince(u'Why are you defending this criminal?', trigger=Victory),
Prince(u'He stole from me!'),
Victoria(u'He didn’t steal me! I left you!', face='scared'),
Victoria(u'I’m not your property you know! I want to see the world...'),
Prince(u'Come back with me and we can rule the world!'),
Victoria(u'I couldn’t if I wanted to, Thomas.'),
Victoria(u'I walked through the Labyrinth with Tom and I am not of your world anymore.'),
Tom(u'Yeah, take that, Nemesis!'),
Victoria(u'Oh, shut up. You two are more alike than you realize.', face='scared',
         action=lambda game: game.StartTimer()),

Victoria(u'Thank you very much, dear sailors for helping us escape.', face='happy',
         trigger=lambda game: game.GetTimer() > 3),
Victoria(u'My name is Victoria Menace.', face='happy'),
Kid(u'You are the good version of Aunt Menace!', face='scared'),
Kid(u'You’re my dear Auntie who was snatched as a baby and replaced with a murderous monster of a pirate baby!', face='wonder'),
Kid(u'You’re saved! Yay!', face='wonder'),
Father(u'Speak of the devil... Aunt Menace is back with a vengeance.'),
Victoria(u'My Nemesis?!'),
AuntMenace(u'So happy to meet you one last time, Victoria!'),
AuntMenace(u'My dear Tom has brought you here so we can become one.'),
AuntMenace(u'By subtracting you and adding endless power to me!'),
Victoria(u'Help me!', face='scared',
         action=lambda game: [game.AddEnemy(ships.OtherBigShip(*OnEdge(0.3))),
                              game.TomBetrayal()]),

AuntMenace(u'Argh! This cannot be! I’m sinking!', trigger=Victory),
Kid(u'Yeah! Back to where you once belonged!', face='wonder'),
AuntMenace(u'Hahaha! You believe in fairy tales, girl.', face='laughing'),
AuntMenace(u'Nobody is stealing babies. Me and your precious Victoria were just the same when we were born.'),
AuntMenace(u'But each time we faced an opportunity, I took it before she could!'),
AuntMenace(u'Do I steal this cookie or do I let her steal it?'),
AuntMenace(u'Do I pillage this harbor or do I let her do it?'),
AuntMenace(u'The world is always in balance on the Sea of Good and Bad.'),
AuntMenace(u'You’re only hurting yourself if you let your Nemesis take the spoils!'),
Kid(u'...', face='scared'),
Kid(u'Is that an Undership coming to her?', face='scared'),
Father(u'And not just any Undership! Looks like my Nemesis and yours are coming to her aid!'),
Kid(u'I see they don’t know her very well...', face='scared',
    action=lambda game: game.AddEnemy(ships.OtherBigShip(*OnEdge(0.3)))),

AuntMenace(u'Your Nemesis is an even lousier captain than you are, Radîr!', trigger=Victory),
AuntMenace(u'I’ve got to leave for now and search for adequate allies.'),
KidsNemesis(u'Hey, we did our best!', face='scared'),
FathersNemesis(u'Yeah, Victoria is much nicer than Captain Menace.'),
FathersNemesis(u'Tom, let her go, and forget about this episode.'),
FathersNemesis(u'My Nemesis was actually right this time.'),
Kid(u'...', face='scared'),
Kid(u'Your Nemesis thinks you are his Nemesis?', face='scared'),
KidsNemesis(u'My Nemesis thinks she’s the real me?!', face='scared'),
Father(u'Let’s... Let’s just take our Mana home.', face='puzzled'),
Father(u'I’m starving!', face='laughing'),

    Kid(u'The End', face='wonder', trigger=lambda game: False),  # Sentinel.
  ]
  def FatherDestroyed(self):
    self.dialog[self.state:self.state] = [
      Father(u'I’m sinking! We lost.', face='puzzled'),
      Kid(u'Can’t we play a bit longer, Papa...?', face='scared'),
      Father(u'I guess I can’t say no to you, Creta!', face='laughing'),
      Father(u'Ship magically repaired. We need to be more careful from now though.',
             action=lambda game: game.HealBack()),
      ]
    self.RenderText()
    self.paused = True

  def NeedleDestroyed(self):
    dishes = ['hamburgers', 'gnocchi', 'fried elderberries']
    self.dialog[self.state:self.state] = [
      Kid(u'Everybody is shooting at me!', face='scared'),
      Kid(u'They turned the Needle into a heap of junk!', face='scared'),
      Father(u'I don’t have any Mana for repairs...', face='puzzled'),
      Father(u'Creta, think of dinner and put that ship back together!'),
      Kid(u'Mmm, {}...'.format(random.choice(dishes)),
          action=lambda game: game.HealBack(), face='wonder'),
      ]
    self.RenderText()
    self.paused = True

  def __init__(self):
    self.state = self.State('here-we-are')
    self.dialog[self.state].t = 0
    self.prev = Father('')
    self.prev.t = 0
    self.paused = False
    self.textures = []
    Dialog.quad = rendering.Quad(1.0, 1.0)
    self.background = rendering.Texture(pygame.image.load('art/dialog-background.png'))
    pygame.font.init()
    Dialog.font = pygame.font.Font('OpenSans-Regular.ttf', 24)
    self.RenderText()
    self.mana = HUD('art/Mana.png')
    self.health = HUD('art/Heart.png')

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
        elif e.type == pygame.KEYDOWN and e.unicode or e.type == pygame.MOUSEBUTTONDOWN:
          if dialog.action:
            dialog.action(game)
          self.prev = dialog
          self.state += 1
          dialog = self.dialog[self.state]
          if dialog.trigger:
            # This is a condition-triggered state. Unpause.
            self.paused = False
          elif dialog.character == self.prev.character:
            self.RenderText()
            dialog.t = self.prev.t
            self.prev.t = 0
    else:
      if dialog.trigger(game):
        self.paused = True

  @classmethod
  def RenderFont(cls, text, antialias=True, color=(255, 255, 255), background=(0, 0, 0)):
    return cls.font.render(text, antialias, color, background)

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
        self.textures.append(rendering.Texture(self.RenderFont(' '.join(words))))
        words = [word]
    self.textures.append(rendering.Texture(self.RenderFont(' '.join(words))))

  def Render(self, game):
    # Surprise! We actually render the HUD too.
    self.mana.Render(0, str(int(game.father_ship.mana)))
    self.health.Render(0.5, str(int(10 * game.father_ship.health)) + '%')

    if not self.paused and self.prev.t <= 0:
      return
    glColor(1, 1, 1, 1)
    if self.prev.t > 0:
      dialog = self.prev
    else:
      dialog = self.dialog[self.state]
    # Background.
    glPushMatrix()
    if self.dialog[self.state].trigger is None:
      # Do not lower background if we are talking more.
      bgpos = 0.25
    else:
      bgpos = dialog.t
    bgpos = -1 + 0.5 * self.background.height * (1 - math.exp(-10 * bgpos))
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
        glPushMatrix()
        glTranslate(-rendering.RATIO + 0.5 * t.width + (0.8 if dialog.side == 'left' else 0.2), bgpos + 0.1 - 0.12 * i, 0)
        glScale(t.width, t.height, 1)
        glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR)
        for shadow in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            glPushMatrix()
            glTranslate(shadow[0] * -0.005 / t.width, shadow[1] * 0.05, 0)
            self.quad.Render()
            glPopMatrix()
        glBlendFunc(GL_ZERO, GL_ONE_MINUS_SRC_COLOR)
        self.quad.Render()
        glPopMatrix()
