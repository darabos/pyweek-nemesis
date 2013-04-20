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
import dialog

class Game(object):

  def __init__(self):
    self.ships = []
    self.crystals = []
    self.shapes = []
    self.enemies = []
    self.projectiles = []
    self.lines_drawn = 0
    self.mana = 0

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

    self.dialog = dialog.Dialog()
    self.crystals = crystals.Crystals(max_crystals=20, total_crystals=100)

    self.small_ship = ships.SmallShip(0, 0, 0.05)
    self.ships.append(self.small_ship)

    self.big_ship = ships.BigShip(0, 0, 0.2)
    self.ships.append(self.big_ship)

    for i in range(10):
      while True:
        x = random.uniform(-1.5, 1.5)
        y = random.uniform(-1.5, 1.5)
        if not (abs(x) < 1.2 and abs(y) < 1.2):
          break
      jellyship = ships.JellyFish(x, y, random.gauss(0.15, 0.03))
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
      for o in self.ships:
        o.Render()
      for o in self.enemies:
        o.Render()
      for o in self.projectiles:
        o.Render()
      self.dialog.Render()
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
      if ship == self.small_ship and self.shape_being_traced:
        self.shape_being_traced.ShipVisited(i)

  def InRangeOfTarget(self, source, r, target):
    if not target:
      return False
    return self.Distance(source, target) <= r

  def NearestObjectOfType(self, x, y, objects):
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
      
      if self.small_ship.health <= 0:
        self.small_ship.drawing = []
        self.shape_being_drawn = None
        self.shape_being_traced = None
        self.small_ship.path_func = ships.ShipPathFromWaypoints(
          (self.small_ship.x, self.small_ship.y), (0, 0),
          [(self.big_ship.x, self.big_ship.y)], self.small_ship.max_velocity)
        self.small_ship.path_func_start_time = self.time        
      else:
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
          shape_path = shapes.ShapeFromMouseInput(
            self.small_ship.drawing, self.crystals)
          if self.shape_being_drawn.CompleteWithPath(shape_path):
            # If it's a valid shape, the ship will now trace the path to
            # activate the shape.
            self.small_ship.path_func = ships.ShipPathFromWaypoints(
              (self.small_ship.x, self.small_ship.y), (0, 0),
              [(c.x, c.y) for c in shape_path], self.small_ship.max_velocity)
            self.shape_being_traced = self.shape_being_drawn
          else:
            # Otherwise just follow the mouse path.
            self.small_ship.path_func = ships.ShipPathFromWaypoints(
              (self.small_ship.x, self.small_ship.y), (0, 0),
              self.small_ship.drawing, self.small_ship.max_velocity)
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
          target_x = self.GameSpace(*e.pos)[0]
          target_y = self.GameSpace(*e.pos)[1]
          nearest = self.NearestObjectOfType(target_x, target_y, self.shapes)
          if nearest:
            dist = math.hypot(nearest.x - target_x, nearest.y - target_y)
            if dist < 0.05:
              self.big_ship.target = nearest
              self.big_ship.path_func = ships.ShipPathFromWaypoints(
                (self.big_ship.x, self.big_ship.y), (0, 0),
                [(nearest.x, nearest.y)], self.big_ship.max_velocity)
            else:
              nearest = False
          if not nearest:
            self.big_ship.path_func = ships.ShipPathFromWaypoints(
              (self.big_ship.x, self.big_ship.y), (0, 0),
              [(target_x, target_y)], self.big_ship.max_velocity)
          self.big_ship.path_func_start_time = self.time

    for ship in self.ships:
      self.MoveObject(ship)
      
    for projectile in list(self.projectiles):
      self.MoveObject(projectile)
      if self.Distance(projectile, self.big_ship) > self.big_ship.combat_range:
        self.projectiles.remove(projectile)
        continue
      for enemy in self.enemies:      
        if self.Distance(enemy, projectile) < (enemy.size + projectile.size) / 2:
          enemy.health -= random.gauss(projectile.damage, 0.1)
          self.projectiles.remove(projectile)
          break      
            
    for enemy in list(self.enemies):
      if isinstance(enemy, ships.JellyFish):
        if not enemy.path_func:
          enemy.path_func = ships.ShipPathFromWaypoints(
            (enemy.x, enemy.y), (0, 0),
            [(random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9))],
            enemy.max_velocity)
          enemy.path_func_start_time = self.time
      if enemy.health <= 0:
        self.enemies.remove(enemy)
      self.MoveObject(enemy)

    # shoot at nearest enemy in range
    if self.big_ship.cooldown - self.big_ship.prev_fire <= 0 and self.mana >= self.big_ship.ammo_cost: 
      nearest_enemy = self.NearestObjectOfType(self.big_ship.x, self.big_ship.y, self.enemies)
      if self.InRangeOfTarget(self.big_ship, self.big_ship.combat_range, nearest_enemy):
        self.projectile = ships.Projectile(self.big_ship.x, self.big_ship.y, 0.075)
        self.projectiles.append(self.projectile)
        self.projectile.path_func = ships.ShipPathFromWaypoints(
          (self.projectile.x, self.projectile.y), (0, 0),
          [(nearest_enemy.x, nearest_enemy.y)], self.projectile.max_velocity)
        self.projectile.path_func_start_time = self.time
        self.big_ship.prev_fire = 0.0
        self.mana -= self.big_ship.ammo_cost
        print 'mana is now %0.2f' % self.mana
    else:
      self.big_ship.prev_fire += dt

    if self.InRangeOfTarget(self.big_ship, 0.002, self.big_ship.target):
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
      print 'mana is now %0.2f' % self.mana
      print 'health is now %0.2f' % self.big_ship.health
      self.big_ship.target = None
      self.big_ship.target_reevaluation = self.time + 0.5
      
    if self.Distance(self.big_ship, self.small_ship) < 0.01:
      if self.mana > 0 and self.small_ship.health < self.small_ship.max_health:
        to_heal = min(max((self.small_ship.max_health - self.small_ship.health), 0), self.mana * 10)
        self.small_ship.health += to_heal
        self.mana -= 10 * to_heal
        print 'mana is now %0.2f' % self.mana
        print 'Needle\'s health is now %0.2f' % self.small_ship.health
        
    if self.big_ship.chasing_shapes:
      if self.time > self.big_ship.target_reevaluation:
        self.big_ship.target_reevaluation = self.time + 0.5
        nearest = self.NearestObjectOfType(self.big_ship.x, self.big_ship.y, self.shapes)
        if nearest and nearest != self.big_ship.target:
          self.big_ship.target = nearest
          self.big_ship.path_func = ships.ShipPathFromWaypoints(
            (self.big_ship.x, self.big_ship.y), (0, 0),
            [(nearest.x, nearest.y)], self.big_ship.max_velocity)
          self.big_ship.path_func_start_time = self.time
    
    for enemy in self.enemies:      
      for ship in self.ships:
        if self.Distance(enemy, ship) < (enemy.size + ship.size) / 2:
          ship.health -= enemy.damage
          print 'Ouch, this hurts! %s\'s health is now %0.2f/%0.2f' % (ship.name, ship.max_health, ship.health)

    if self.big_ship.health <= 0:
      self.dialog.JumpTo('health-zero')
    
    if self.shape_being_traced:
      if self.shape_being_traced.DoneTracing():
        self.shapes.append(self.shape_being_traced)
        self.shape_being_traced = None      


if __name__ == '__main__':
  Game().Start()
