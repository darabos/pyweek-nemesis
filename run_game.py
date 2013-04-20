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

class Game(object):

  def __init__(self):
    self.ships = []
    self.crystals = []
    self.shapes = []
    self.projectiles = []
    self.lines_drawn = 0
    self.drawing_in_progress = False

  def Start(self):
    self.Init()
    self.Loop()

  def Init(self):
    pygame.init()
    pygame.display.set_mode((int(rendering.WIDTH), int(rendering.HEIGHT)), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption('Nemesis')
    glViewport(0, 0, int(rendering.WIDTH), int(rendering.HEIGHT))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-rendering.RATIO, rendering.RATIO, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(0.0, 0.3, 0.6, 1)

    assets.Init()
    self.b = background.BackGround((-rendering.RATIO, rendering.RATIO), (-1, 1), (0.9, 0.3, 0.6))

    self.dialog = dialog.Dialog()
    self.crystals = crystals.Crystals(max_crystals=20, total_crystals=100)

    self.father_ship = ships.BigShip(0, 0, 0.2)
    self.father_ship.AI = 'HumanFather'
    self.needle_ship = ships.SmallShip(0, 0, 0.05)
    self.needle_ship.AI = 'HumanNeedle'
    self.needle_ship.owner = self.father_ship
    self.ships.append(self.needle_ship)
    self.ships.append(self.father_ship)

    self.big_ship = ships.BigShip(0.6, 0.6, 0.3)
    self.big_ship.AI = 'Chasing shapes'
    self.ships.append(self.big_ship)
    
    self.enemybig_ship = ships.BigShip(0.6, -0.6, 0.3)
    self.enemybig_ship.AI = 'Moron'
    self.enemybig_ship.faction = 2
    self.enemybig_ship.texture = rendering.Texture(pygame.image.load('art/ships/evilbird.png'))
    self.ships.append(self.enemybig_ship)
    
    self.kraken = ships.Kraken(-0.1, -0.8, 0.5)
    self.kraken.faction = 20  # attacks Jellyfish as well
    self.ships.append(self.kraken)

    for i in range(2):
      while True:
        x = random.uniform(-1.5, 1.5)
        y = random.uniform(-1.5, 1.5)
        if not (abs(x) < 1.2 and abs(y) < 1.2):
          break
      jellyship = ships.JellyFish(x, y, random.gauss(0.15, 0.03))
      jellyship.faction = 0
      self.ships.append(jellyship)

    # Track in-progress shapes.
    # Shape being drawn right now:
    self.shape_being_drawn = None
    # Shape being traced by the small ship:
    self.shape_being_traced = None

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
      if not self.dialog.paused:
        self.Update(dt)
      glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
      self.b.Draw()
      glColor(1, 1, 1, 1)
      rendering.DrawPath(self.needle_ship.drawing)
      if self.shape_being_drawn:
        self.shape_being_drawn.Render()
      if self.shape_being_traced:
        self.shape_being_traced.Render()
      for o in self.shapes:
        o.Render()
      self.crystals.Render()
      for o in self.ships:
        o.Render()
      for o in self.projectiles:
        o.Render()
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
      if dx == 0 and dy == 0:
        ship.path_func = None
      ship.x = x
      ship.y = y
      if ship == self.needle_ship and self.shape_being_traced:
        self.shape_being_traced.ShipVisited(i)

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

  def Update(self, dt):
    self.time += dt
    self.crystals.Update(dt, self)

    for e in pygame.event.get():
      if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit(0)

      for smallship in self.ships:
        if isinstance(smallship, ships.SmallShip) and smallship.AI == 'HumanNeedle':
          if smallship.health <= 0:
            smallship.drawing = []
            self.shape_being_drawn = None
            self.shape_being_traced = None
            smallship.path_func = ships.ShipPathFromWaypoints(
              (smallship.x, smallship.y), (0, 0),
              [(smallship.owner.x, smallship.owner.y)], smallship.max_velocity)
            smallship.path_func_start_time = self.time
          else:
            if self.drawing_in_progress:
              if (e.type == pygame.MOUSEBUTTONUP and e.button == 1) or (e.type == pygame.KEYUP and e.key in [pygame.K_RSHIFT, pygame.K_LSHIFT]):
                self.drawing_in_progress = False
                shape_path = shapes.ShapeFromMouseInput(
                  smallship.drawing, self.crystals)
                if self.shape_being_drawn is not None and self.shape_being_drawn.CompleteWithPath(shape_path):
                  # If it's a valid shape, the ship will now trace the path to
                  # activate the shape.
                  smallship.path_func = ships.ShipPathFromWaypoints(
                    (smallship.x, smallship.y), (0, 0),
                    [(c.x, c.y) for c in shape_path], smallship.max_velocity)
                  self.shape_being_traced = self.shape_being_drawn
                else:
                  # Otherwise just go to the starting point of the path
                  smallship.path_func = ships.ShipPathFromWaypoints(
                    (smallship.x, smallship.y), (0, 0),
                    smallship.drawing[0:1], smallship.max_velocity)
                  self.shape_being_traced = None
                smallship.path_func_start_time = self.time
                self.shape_being_drawn = None
                smallship.drawing = []
                self.lines_drawn += 1
    
              if e.type == pygame.MOUSEMOTION:
                smallship.drawing.append(self.GameSpace(*e.pos))
                smallship.drawing = shapes.FilterMiddlePoints(smallship.drawing, 50)
                # TODO(alex): Updating while in progress is nice, but too
                # now. Need to incrementally build the path for this to work.
                #shape_path = shapes.ShapeFromMouseInput(
                #  smallship.drawing, self.crystals)
                #self.shape_being_drawn.UpdateWithPath(shape_path)
    
            if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or (e.type == pygame.KEYDOWN and e.key in [pygame.K_RSHIFT, pygame.K_LSHIFT]):
              pos = pygame.mouse.get_pos()
              smallship.drawing = [self.GameSpace(*pos)]
              self.shape_being_drawn = shapes.Shape(self)
              shape_path = shapes.ShapeFromMouseInput(smallship.drawing, self.crystals)
              self.drawing_in_progress = True

      for bigship in self.ships:
        if isinstance(bigship, ships.BigShip) and bigship.AI == 'HumanFather':
          if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            target_x = self.GameSpace(*e.pos)[0]
            target_y = self.GameSpace(*e.pos)[1]
            nearest = self.NearestObjectFromList(target_x, target_y, self.shapes)
            if nearest:
              dist = math.hypot(nearest.x - target_x, nearest.y - target_y)
              if dist < 0.05:
                bigship.target = nearest
                bigship.path_func = ships.ShipPathFromWaypoints(
                  (bigship.x, bigship.y), (0, 0),
                  [(nearest.x, nearest.y)], bigship.max_velocity)
              else:
                nearest = False
            if not nearest:
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (0, 0),
                [(target_x, target_y)], bigship.max_velocity)
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
              min_x, max_x, min_y, max_y = -0.9, 0.9, -0.9, 0.9
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
                (bigship.x, bigship.y), (0, 0),
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
            (ship.x, ship.y), (0, 0),
            [(random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9))],
            ship.max_velocity)
          ship.path_func_start_time = self.time
      elif ship.AI == 'Kraken':
        if self.time > ship.target_reevaluation:
          ship.target_reevaluation = self.time + 2.0
          enemies = [enemy for enemy in self.ships if ship.faction != enemy.faction]
          nearest = self.NearestObjectFromList(ship.x, ship.y, enemies)
          if nearest and nearest != ship.target:
            ship.target = nearest
            ship.path_func = ships.ShipPathFromWaypoints(
              (ship.x, ship.y), (0, 0),
              [(nearest.x, nearest.y)], ship.max_velocity)
            ship.path_func_start_time = self.time

      if ship.health <= 0:
        if ship is self.father_ship:
          self.dialog.JumpTo('health-zero')
        elif ship is not self.needle_ship:
          self.ships.remove(ship)
      self.MoveObject(ship)

    mana_of_friends = sum([
      ship.mana for ship in self.ships if isinstance(ship, ships.BigShip) and ship.faction == self.father_ship.faction
    ])
    if self.needle_ship.health < 0 and mana_of_friends <= 0:
      self.dialog.JumpTo('needle-cannot-heal')


    # shoot at nearest enemy in range
    for bigship in self.ships:
      if isinstance(bigship, ships.BigShip):
        if bigship.cooldown - bigship.prev_fire <= 0 and bigship.mana >= bigship.ammo_cost:
          enemies = [ship for ship in self.ships if bigship.faction != ship.faction]
          nearest_enemy = self.NearestObjectFromList(bigship.x, bigship.y, enemies)
          if self.InRangeOfTarget(bigship, bigship.combat_range, nearest_enemy):
            projectile = ships.Projectile(bigship.x, bigship.y, 0.075)
            projectile.owner = bigship
            projectile.faction = bigship.faction
            projectile.path_func = ships.ShipPathFromWaypoints(
              (projectile.x, projectile.y), (0, 0),
              [(nearest_enemy.x, nearest_enemy.y)], projectile.max_velocity)
            projectile.path_func_start_time = self.time
            self.projectiles.append(projectile)
            bigship.prev_fire = 0.0
            bigship.mana -= bigship.ammo_cost
            print '%s\'s mana is now %0.2f' % (bigship.name, bigship.mana)
        else:
          bigship.prev_fire += dt

        if self.InRangeOfTarget(bigship, 0.002, bigship.target):
          shape = bigship.target
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
                bigship.mana -= 10 * to_heal
                print '%s\'s mana is now %0.2f' % (bigship.name, bigship.mana)
                print '%s\'s health is now %0.2f' % (smallship.name, smallship.health)

        if bigship.AI == "Chasing shapes":
          if self.time > bigship.target_reevaluation:
            bigship.target_reevaluation = self.time + 0.5
            nearest = self.NearestObjectFromList(bigship.x, bigship.y, self.shapes)
            if nearest and nearest != bigship.target:
              bigship.target = nearest
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (0, 0),
                [(nearest.x, nearest.y)], bigship.max_velocity)
              bigship.path_func_start_time = self.time

        if bigship.AI == "Moron":
          if self.time > bigship.target_reevaluation:
            bigship.target_reevaluation = self.time + 2.0
            if (bigship.mana >= 400 or bigship.mana >= 200 and not self.NearestObjectFromList(bigship.x, bigship.y, self.shapes)) and bigship.health > 1.5:
              enemies = [ship for ship in self.ships if bigship.faction != ship.faction]
              nearest = self.NearestObjectFromList(bigship.x, bigship.y, enemies)
            elif not self.NearestObjectFromList(bigship.x, bigship.y, self.shapes):
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (0, 0),
                [(random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9))],
                bigship.max_velocity)
              bigship.path_func_start_time = self.time
              nearest = None
            else:
              nearest = self.NearestObjectFromList(bigship.x, bigship.y, self.shapes)
            if nearest and nearest != bigship.target:
              bigship.target = nearest
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (0, 0),
                [(nearest.x, nearest.y)], bigship.max_velocity)
              bigship.path_func_start_time = self.time

    for ship in self.ships:
      if ship.damage > 0:
        for enemy in self.ships:
          if ship.faction != enemy.faction and self.Distance(enemy, ship) < (enemy.size + ship.size) / 2:
            enemy.health -= ship.damage
            print '%s\'s health is now %0.2f/%0.2f' % (enemy.name, enemy.max_health, enemy.health)

    if self.shape_being_traced:
      if self.shape_being_traced.DoneTracing():
        self.shapes.append(self.shape_being_traced)
        self.shape_being_traced = None


if __name__ == '__main__':
  Game().Start()
