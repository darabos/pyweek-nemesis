# coding: utf8
import math
import random
import pygame
import sys
from OpenGL.GL import *

import assets
import background
import crystals
import dialog
import rendering
import shapes
import ships

BIGSHIP_UP_KEY = pygame.K_w
BIGSHIP_DOWN_KEY = pygame.K_s
BIGSHIP_LEFT_KEY = pygame.K_a
BIGSHIP_RIGHT_KEY = pygame.K_d
BIGSHIP_CONTROL_KEYS = [BIGSHIP_UP_KEY, BIGSHIP_DOWN_KEY, BIGSHIP_LEFT_KEY, BIGSHIP_RIGHT_KEY]


def Music(filename):
  try:
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play(-1)
  except Exception as e:
    print "Music playback doesn't seem to work (%r). Sorry." % e


class Game(object):

  def __init__(self):
    self.ships = []
    self.crystals = []
    self.shapes = []
    self.projectiles = []
    self.drawing = []
    self.paths_followed = 0
    self.drawing_in_progress = False

  def Start(self):
    self.Init()
    Music('music/vinylwaltz.ogg')
    self.Loop()

  def Init(self):
    pygame.init()
    pygame.display.set_mode((int(rendering.WIDTH), int(rendering.HEIGHT)), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption('Nemesis')
    glViewport(0, 0, int(rendering.WIDTH), int(rendering.HEIGHT))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-rendering.RATIO, rendering.RATIO, -1, 1, -1, 1)
    glMultMatrixd([1, 0, 0, 0,
                   0, 1, 0, 0,
                   -0.2, 0.4, 1, 0,
                   #-1.5, 1.5, 1, 0,
                   0, 0, 0, 1])
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.0, 0.05, 0.6, 1)

    glLight(GL_LIGHT0, GL_POSITION, [0.4082, -0.4082, 0.8165, 0])
    glLight(GL_LIGHT0, GL_SPECULAR, [0, 0, 0, 0])
    glLight(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 0])
    glLight(GL_LIGHT0, GL_AMBIENT, [0, 0, 0, 0])
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_ALWAYS)

    assets.Init()
    self.b = background.BackGround((-rendering.RATIO, rendering.RATIO), (-1, 1), (0.9, 0.3, 0.6))

    self.dialog = dialog.Dialog()
    self.crystals = crystals.Crystals(max_crystals=20)

    self.father_ship = ships.OurBigShip(-0.5, 0, 0.2)
    self.father_ship.AI = 'HumanFather'
    self.father_ship.mana = 0
    self.father_ship.path_func = ships.ShipPathFromWaypoints(
      (self.father_ship.x, self.father_ship.y), (self.father_ship.dx, self.father_ship.dy),
      [(0, 0)], self.father_ship.max_velocity)
    self.father_ship.path_func_start_time = 0
    self.ships.append(self.father_ship)
    self.needle_ship = ships.SmallShip(-0.5, 0, 0.05)
    self.needle_ship.AI = 'HumanNeedle'
    self.needle_ship.owner = self.father_ship
    self.ships.append(self.needle_ship)

    # self.big_ship = ships.OurBigShip(0.6, 0.6, 0.3)
    # self.big_ship.AI = 'Chasing shapes'
    # self.ships.append(self.big_ship)
    # self.needle_ship2 = ships.SmallShip(0, 0.9, 0.05)
    # self.needle_ship2.AI = 'Evil Needle'
    # self.needle_ship2.owner = self.big_ship
    # self.ships.append(self.needle_ship2)

    # self.enemybig_ship = ships.OtherBigShip(0.6, -0.6, 0.3)
    # self.enemybig_ship.AI = 'Moron'
    # self.enemybig_ship.faction = 2
    # self.enemybig_ship.texture = rendering.Texture(pygame.image.load('art/ships/evilbird.png'))
    # self.ships.append(self.enemybig_ship)

    # self.kraken = ships.Kraken(-0.1, -0.8, 0.5)
    # self.kraken.faction = 20  # attacks Jellyfish as well
    # self.ships.append(self.kraken)

    # Track in-progress shapes.
    # Shape being drawn right now:
    self.shape_being_drawn = None

  def AddEnemy(self, enemy, with_small_ship=False, final_battle=False):
    enemy.faction = 2
    enemy.path_func = ships.ShipPathFromWaypoints(
              (enemy.x, enemy.y), (enemy.dx, enemy.dy),
              [(enemy.x/2, enemy.y/2)], enemy.max_velocity)
    enemy.path_func_start_time = self.time
    self.ships.append(enemy)
    if with_small_ship:
      small_ship = ships.SmallShip(enemy.x, enemy.y, 0.05)
      small_ship.AI = 'Evil Needle'
      small_ship.owner = enemy
      small_ship.faction = enemy.faction
      small_ship.path_func = ships.ShipPathFromWaypoints(
                (enemy.x, enemy.y), (enemy.dx, enemy.dy),
                [(enemy.x/2, enemy.y/2)], enemy.max_velocity)
      small_ship.path_func_start_time = self.time
      self.ships.append(small_ship)
    if final_battle:
      enemy.max_velocity = 0.25
      enemy.AI_smart = 2

  def AddAlly(self, ally):
    ally.faction = 1
    self.ships.append(ally)

  def TomBetrayal(self):
    for ship in self.ships:
      if ship.faction == 1 and ship is not self.father_ship and ship is not self.needle_ship:
        ship.faction = 2

  def StartTimer(self):
    self.timer_start = self.time

  def GetTimer(self):
    return self.time - self.timer_start

  def Loop(self):
    clock = pygame.time.Clock()
    self.time = 0
    next_fps_print = 0
    while True:
      if self.time > next_fps_print:
        print clock
        next_fps_print = self.time + 2
      dt = 0.001 * clock.tick()
      self.dialog.Update(dt, self)
      if self.dialog.paused:
        self.drawing_in_progress = False
        self.drawing = []
      else:
        self.Update(dt)
      glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
      self.b.Draw(self.time, False)
      glColor(1, 1, 1, 1)
      rendering.DrawPath(self.drawing)
      if self.shape_being_drawn:
        self.shape_being_drawn.Render()
      if self.needle_ship.shape_being_traced:
        self.needle_ship.shape_being_traced.Render()
      for o in self.shapes:
        o.Render()
      self.crystals.Render()
      for o in self.ships:
        o.Render()
      for o in self.projectiles:
        o.Render()
      self.b.Draw(self.time, True)
      self.dialog.Render(self)
      pygame.display.flip()

  def GameSpace(self, x, y):
    return 2 * x / rendering.HEIGHT - rendering.RATIO, 1 - 2 * y / rendering.HEIGHT

  def Distance(self, ship1, ship2):
    return math.hypot(ship1.x - ship2.x, ship1.y - ship2.y)

  def MoveObject(self, ship):
    if ship.path_func:
      (x, y, dx, dy, i) = ship.path_func(
        self.time - ship.path_func_start_time)
      if dx is None:
        ship.path_func = None
        if ship is self.needle_ship:
            self.paths_followed += 1
      else:
        ship.dx = dx
        ship.dy = dy
      ship.x = x
      ship.y = y
      if isinstance(ship, ships.SmallShip) and ship.shape_being_traced:
        ship.shape_being_traced.ShipVisited(i)

  def InRangeOfTarget(self, source, r, target):
    if not target:
      return False
    return self.Distance(source, target) <= r

  def NearestObjectFromList(self, x, y, objects):
    if not objects:
      return None
    nearest = min(objects,
                  key=lambda obj: math.hypot(obj.x - x,
                                             obj.y - y))
    return nearest

  def HealBack(self):
    self.father_ship.health = 10
    self.needle_ship.health = 1


  def Update(self, dt):
    self.time += dt
    self.crystals.Update(dt, self)

    for e in pygame.event.get():
      if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit(0)

      for smallship in self.ships:
        if isinstance(smallship, ships.SmallShip):
          if smallship.health <= 0:
            if smallship.shape_being_traced:
              smallship.shape_being_traced.Cancel()
            smallship.shape_being_traced = None
            smallship.path_func = ships.ShipPathFromWaypoints(
              (smallship.x, smallship.y), (smallship.dx, smallship.dy),
              [(smallship.owner.x, smallship.owner.y)], smallship.max_velocity)
            smallship.path_func_start_time = self.time
            if smallship.AI == 'HumanNeedle':
              self.drawing_in_progress = False
              self.drawing = []
          elif smallship.AI == 'HumanNeedle':
            if self.drawing_in_progress:
              if (e.type == pygame.MOUSEBUTTONUP and e.button == 1) or (e.type == pygame.KEYUP and e.key in [pygame.K_RSHIFT, pygame.K_LSHIFT]):
                self.drawing_in_progress = False
                shape_path = shapes.ShapeFromMouseInput(
                  self.drawing, self.crystals)
                if smallship.shape_being_traced:
                  smallship.shape_being_traced.Cancel()
                if self.shape_being_drawn is not None and self.shape_being_drawn.CompleteWithPath(shape_path):
                  # If it's a valid shape, the ship will now trace the path to
                  # activate the shape.
                  smallship.path_func = ships.ShipPathFromWaypoints(
                    (smallship.x, smallship.y), (smallship.dx, smallship.dy),
                    [(c.x, c.y) for c in shape_path], smallship.max_velocity)
                  smallship.shape_being_traced = self.shape_being_drawn
                else:
                  # Otherwise just follow the path:
                  smallship.path_func = ships.ShipPathFromWaypoints(
                    (smallship.x, smallship.y), (smallship.dx, smallship.dy),
                    self.drawing, smallship.max_velocity)
                  smallship.shape_being_traced = None
                smallship.path_func_start_time = self.time
                self.shape_being_drawn = None
                self.drawing = []

              if e.type == pygame.MOUSEMOTION:
                self.drawing.append(self.GameSpace(*e.pos))
                self.drawing = shapes.FilterMiddlePoints(self.drawing, 50)
                # TODO(alex): Updating while in progress is nice, but too
                # now. Need to incrementally build the path for this to work.
                #shape_path = shapes.ShapeFromMouseInput(
                #  self.drawing, self.crystals)
                #self.shape_being_drawn.UpdateWithPath(shape_path)

            if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or (e.type == pygame.KEYDOWN and e.key in [pygame.K_RSHIFT, pygame.K_LSHIFT]):
              pos = pygame.mouse.get_pos()
              self.drawing = [self.GameSpace(*pos)]
              self.shape_being_drawn = shapes.Shape(self)
              #shape_path = shapes.ShapeFromMouseInput(self.drawing, self.crystals)
              self.drawing_in_progress = True    

      for bigship in self.ships:
        if isinstance(bigship, ships.BigShip) and bigship.AI == 'HumanFather':
          if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            bigship.path_func = ships.ShipPathFromWaypoints(
              (bigship.x, bigship.y), (bigship.dx, bigship.dy),
              [self.GameSpace(*e.pos)], bigship.max_velocity)
            bigship.path_func_start_time = self.time

          if e.type in [pygame.KEYUP, pygame.KEYDOWN] and e.key in BIGSHIP_CONTROL_KEYS:
            pressed_keys = pygame.key.get_pressed()
            up = pressed_keys[BIGSHIP_UP_KEY]
            down = pressed_keys[BIGSHIP_DOWN_KEY]
            left = pressed_keys[BIGSHIP_LEFT_KEY]
            right = pressed_keys[BIGSHIP_RIGHT_KEY]
            if (not up and not down and not left and not right) or (up and down) or (left and right):
              bigship.path_func = None
            else:
              target_x = bigship.x
              target_y = bigship.y
              min_x, max_x, min_y, max_y = -0.9*rendering.RATIO, 0.9*rendering.RATIO, -0.9, 0.9
              if up:
                target_y = max_y
                if left:
                  target_x = bigship.x - (target_y - bigship.y)
                  if target_x < min_x:
                    target_y -= (min_x - target_x)
                    target_x = min_x
                if right:
                  target_x = bigship.x + (target_y - bigship.y)
                  if target_x > max_x:
                    target_y -= (target_x - max_x)
                    target_x = max_x
              elif down:
                target_y = min_y
                if left:
                  target_x = bigship.x - (bigship.y - target_y)
                  if target_x < min_x:
                    target_y += (min_x - target_x)
                    target_x = min_x
                if right:
                  target_x = bigship.x + (bigship.y - target_y)
                  if target_x > max_x:
                    target_y += (target_x - max_x)
                    target_x = max_x
              elif right:
                target_x = max_x
              elif left:
                target_x = min_x
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (bigship.dx, bigship.dy),
                [(target_x, target_y)], bigship.max_velocity)
              bigship.path_func_start_time = self.time

    # TODO: if owner is deleted, projectiles will crash the game
    for projectile in list(self.projectiles):
      self.MoveObject(projectile)
      if self.Distance(projectile, projectile.owner) > projectile.owner.combat_range or projectile.path_func_start_time + projectile.lifetime < self.time:
        self.projectiles.remove(projectile)
        continue
      for enemy in self.ships:
        if enemy.faction != projectile.faction and self.Distance(enemy, projectile) < (enemy.size + projectile.size) / 2:
          enemy.health -= random.gauss(projectile.damage, 0.1)
          self.projectiles.remove(projectile)
          break

    for ship in self.ships:
      if ship.AI == 'Wandering' and not ship.path_func:
          ship.path_func = ships.ShipPathFromWaypoints(
            (ship.x, ship.y), (ship.dx, ship.dy),
            [(random.uniform(-0.9*rendering.RATIO, 0.9*rendering.RATIO), random.uniform(-0.9, 0.9))],
            ship.max_velocity)
          ship.path_func_start_time = self.time
      elif ship.AI == 'Kraken':
        if self.time > ship.target_reevaluation:
          ship.target_reevaluation = self.time + 2.0
          enemies = [enemy for enemy in self.ships if ship.faction != enemy.faction]
          nearest = self.NearestObjectFromList(ship.x, ship.y, enemies)
          ship.target = nearest
          ship.path_func = ships.ShipPathFromWaypoints(
            (ship.x, ship.y), (ship.dx, ship.dy),
            [(nearest.x, nearest.y)], ship.max_velocity)
          ship.path_func_start_time = self.time
      elif ship.AI == 'Evil Needle':
        if ship.shape_being_traced is None and self.time > ship.target_reevaluation:
          ship.target_reevaluation = self.time + random.gauss(10.0, 1.5)
          available_crystals = [c for c in self.crystals if not c.in_shape and c.visible]
          if len(available_crystals) >= 3:
            number_of_tries = 30
            shape_paths = []
            for i in range(number_of_tries):
              n = None
              while not n or len(available_crystals) < n:
                n = random.randint(3, 5)
              shape_path = random.sample(available_crystals, n)
              shape_score = shapes.ShapeScore([(c.x, c.y) for c in shape_path])
              for path in shape_path:
                nearest = self.NearestObjectFromList(path.x, path.y, self.ships)
                if ship.faction != nearest.faction:
                  shape_score *= 0.4 # if enemy is near factor score lower
              shape_path += [shape_path[0]]
              shape_paths.append((shape_score, shape_path))
            shape_path = max(shape_paths)[1]
            ship.path_func = ships.ShipPathFromWaypoints(
              (ship.x, ship.y), (0, 0),
              [(c.x, c.y) for c in shape_path], ship.max_velocity)
            ship.path_func_start_time = self.time
            ship.shape_being_traced = shapes.Shape(self)
            ship.shape_being_traced.CompleteWithPath(shape_path)

      if ship.health <= 0:
        if ship is self.father_ship:
          self.dialog.FatherDestroyed()
        elif not isinstance(ship, ships.SmallShip):
          for smallship in self.ships:
            if isinstance(smallship, ships.SmallShip) and smallship.owner is ship:
              if smallship.shape_being_traced:
                smallship.shape_being_traced.Cancel()
              self.ships.remove(smallship)
          self.ships.remove(ship)
      self.MoveObject(ship)

    mana_of_friends = sum([
      ship.mana for ship in self.ships if isinstance(ship, ships.BigShip) and ship.faction == self.father_ship.faction
    ])
    if self.needle_ship.health < 0 and mana_of_friends <= 0:
      self.dialog.NeedleDestroyed()


    # shoot at nearest enemy in range
    for bigship in self.ships:
      if isinstance(bigship, ships.BigShip):
        if random.gauss(bigship.cooldown, 0.1) - bigship.prev_fire <= 0 and bigship.mana >= bigship.ammo_cost:
          enemies = [ship for ship in self.ships if bigship.faction != ship.faction]
          nearest_enemy = self.NearestObjectFromList(bigship.x, bigship.y, enemies)
          if self.InRangeOfTarget(bigship, bigship.combat_range, nearest_enemy):
            projectile = ships.Projectile(bigship.x, bigship.y, 0.075)
            projectile.owner = bigship
            projectile.faction = bigship.faction
            projectile.path_func = ships.ShipPathFromWaypoints(
              (projectile.x, projectile.y), (projectile.dx, projectile.dy),
              [(nearest_enemy.x, nearest_enemy.y)], projectile.max_velocity)
            projectile.path_func_start_time = self.time
            self.projectiles.append(projectile)
            bigship.prev_fire = 0.0
            bigship.mana = max(bigship.mana - bigship.ammo_cost, 0)
            print '%s\'s mana is now %0.2f' % (bigship.name, bigship.mana)
        else:
          bigship.prev_fire += dt

        nearest_shape = self.NearestObjectFromList(bigship.x, bigship.y, self.shapes)
        if self.InRangeOfTarget(bigship, 0.05, nearest_shape):
          shape = nearest_shape
          if shape in self.shapes:
            self.shapes.remove(shape)
            for c in shape.path:
              # TODO(alex): need to flag crystals earlier so they can't
              # get re-used for other paths, or delete earlier paths if a
              # later path reuses the same crystal
              self.crystals.remove(c)
            # TODO(alex): trigger animation on shape when it's being hauled in
            to_heal = min(max((bigship.max_health - bigship.health), 0), shape.score)
            bigship.health += to_heal
            bigship.mana += 100 * (shape.score - to_heal)
            print '%s\'s mana is now %0.2f' % (bigship.name, bigship.mana)
            print '%s\'s health is now %0.2f' % (bigship.name, bigship.health)
            bigship.target = None
            bigship.target_reevaluation = self.time + 0.5
        for smallship in self.ships:
          if isinstance(smallship, ships.SmallShip):
            if bigship.faction == smallship.faction and self.Distance(bigship, smallship) < 0.01:
              if bigship.mana > 0 and smallship.health < smallship.max_health:
                to_heal = min(max((smallship.max_health - smallship.health), 0), bigship.mana * 10)
                smallship.health += to_heal
                bigship.mana = max(0, bigship.mana - 10 * to_heal)
                print '%s\'s mana is now %0.2f' % (bigship.name, bigship.mana)
                print '%s\'s health is now %0.2f' % (smallship.name, smallship.health)

        if bigship.AI == "Chasing shapes":
          if self.time > bigship.target_reevaluation:
            bigship.target_reevaluation = self.time + 0.5
            nearest = self.NearestObjectFromList(bigship.x, bigship.y, self.shapes)
            if nearest and nearest != bigship.target:
              bigship.target = nearest
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (bigship.dx, bigship.dy),
                [(nearest.x, nearest.y)], bigship.max_velocity)
              bigship.path_func_start_time = self.time

        if bigship.AI == "Moron":
          if self.time > bigship.target_reevaluation:
            bigship.target_reevaluation = self.time + bigship.AI_smart
            if (bigship.mana >= 400 or bigship.mana >= 200 and not self.NearestObjectFromList(bigship.x, bigship.y, self.shapes)) and bigship.health > 1.5:
              enemies = [ship for ship in self.ships if bigship.faction != ship.faction]
              nearest = self.NearestObjectFromList(bigship.x, bigship.y, enemies)
            elif not self.NearestObjectFromList(bigship.x, bigship.y, self.shapes):
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (bigship.dx, bigship.dy),
                [(random.uniform(-0.9*rendering.RATIO, 0.9*rendering.RATIO), random.uniform(-0.9, 0.9))],
                bigship.max_velocity)
              bigship.path_func_start_time = self.time
              nearest = None
            else:
              nearest = self.NearestObjectFromList(bigship.x, bigship.y, self.shapes)
            if nearest:
              bigship.target = nearest
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (bigship.dx, bigship.dy),
                [(nearest.x, nearest.y)], bigship.max_velocity)
              bigship.path_func_start_time = self.time

    for smallship in self.ships:
      if isinstance(smallship, ships.SmallShip):
        if smallship.shape_being_traced:
          if smallship.shape_being_traced.DoneTracing():
            self.shapes.append(smallship.shape_being_traced)
            smallship.shape_being_traced = None

    for ship in self.ships:
      if ship.damage > 0:
        for enemy in self.ships:
          if ship.faction != enemy.faction and self.Distance(enemy, ship) < (enemy.size + ship.size) / 2:
            enemy.health -= ship.damage
            print '%s\'s health is now %0.2f/%0.2f' % (enemy.name, enemy.max_health, enemy.health)


if __name__ == '__main__':
  Game().Start()
