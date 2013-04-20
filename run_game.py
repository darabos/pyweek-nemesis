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
    self.projectiles = []
    self.lines_drawn = 0

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

    self.father_ship = ships.BigShip(0, 0, 0.2)
    self.father_ship.AI = 'Human'
    self.ships.append(self.father_ship)
    self.big_ship = ships.BigShip(0.6, 0.6, 0.3)
    self.big_ship.AI = 'Chasing shapes'
    self.ships.append(self.big_ship)
    self.big_ship = ships.BigShip(0.6, -0.6, 0.3)
    self.big_ship.AI = 'Moron'
    self.big_ship.faction = 2
    self.big_ship.texture = rendering.Texture(pygame.image.load('art/ships/evilbird.png'))
    self.ships.append(self.big_ship)

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
    
    # control by mouse STARTS here
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
          [(self.father_ship.x, self.father_ship.y)], self.small_ship.max_velocity)
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
            # Otherwise just go to the starting point of the path
            self.small_ship.path_func = ships.ShipPathFromWaypoints(
              (self.small_ship.x, self.small_ship.y), (0, 0),
              self.small_ship.drawing[0:1], self.small_ship.max_velocity)
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
          self.small_ship.drawing = shapes.FilterMiddlePoints(self.small_ship.drawing, 50)
          # TODO(alex): Updating while in progress is nice, but too
          # now. Need to incrementally build the path for this to work.
          #shape_path = shapes.ShapeFromMouseInput(
          #  self.small_ship.drawing, self.crystals)
          #self.shape_being_drawn.UpdateWithPath(shape_path)

      for bigship in self.ships:
        if isinstance(bigship, ships.BigShip) and bigship.AI == 'Human':
          if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            target_x = self.GameSpace(*e.pos)[0]
            target_y = self.GameSpace(*e.pos)[1]
            nearest = self.NearestObjectOfType(target_x, target_y, self.shapes)
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
    # controlled by mouse ENDS here
      
    # TODO: if owner is deleted, projectiles will crash the game
    for projectile in list(self.projectiles):
      self.MoveObject(projectile)
      if self.Distance(projectile, projectile.owner) > projectile.owner.combat_range:
        self.projectiles.remove(projectile)
        continue
      for enemy in self.ships:      
        if enemy.faction != projectile.faction and self.Distance(enemy, projectile) < (enemy.size + projectile.size) / 2:
          enemy.health -= random.gauss(projectile.damage, 0.1)
          self.projectiles.remove(projectile)
          break      
            
    for wandering in list(self.ships):
      if isinstance(wandering, ships.JellyFish):
        if not wandering.path_func:
          wandering.path_func = ships.ShipPathFromWaypoints(
            (wandering.x, wandering.y), (0, 0),
            [(random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9))],
            wandering.max_velocity)
          wandering.path_func_start_time = self.time

    for ship in self.ships:
      if ship.health <= 0:
        if ship is self.father_ship:
          self.dialog.JumpTo('health-zero')
        elif ship is not self.small_ship:
          self.ships.remove(ship)
      self.MoveObject(ship)
      
    mana_of_friends = sum([
      ship.mana for ship in self.ships if isinstance(ship, ships.BigShip) and ship.faction == self.father_ship.faction
    ])
    if self.small_ship.health < 0 and mana_of_friends <= 0:
      self.dialog.JumpTo('needle-cannot-heal')
      

    # shoot at nearest enemy in range
    for bigship in self.ships:
      if isinstance(bigship, ships.BigShip):
        if bigship.cooldown - bigship.prev_fire <= 0 and bigship.mana >= bigship.ammo_cost: 
          enemies = [ship for ship in self.ships if bigship.faction != ship.faction]
          nearest_enemy = self.NearestObjectOfType(bigship.x, bigship.y, enemies)
          if self.InRangeOfTarget(bigship, bigship.combat_range, nearest_enemy):
            self.projectile = ships.Projectile(bigship.x, bigship.y, 0.075)
            self.projectile.owner = bigship
            self.projectile.faction = bigship.faction
            self.projectiles.append(self.projectile)
            self.projectile.path_func = ships.ShipPathFromWaypoints(
              (self.projectile.x, self.projectile.y), (0, 0),
              [(nearest_enemy.x, nearest_enemy.y)], self.projectile.max_velocity)
            self.projectile.path_func_start_time = self.time
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
      
        if bigship.faction == self.small_ship.faction and self.Distance(bigship, self.small_ship) < 0.01:
          if bigship.mana > 0 and self.small_ship.health < self.small_ship.max_health:
            to_heal = min(max((self.small_ship.max_health - self.small_ship.health), 0), bigship.mana * 10)
            self.small_ship.health += to_heal
            bigship.mana -= 10 * to_heal
            print '%s\'s mana is now %0.2f' % (bigship.name, bigship.mana)
            print 'Needle\'s health is now %0.2f' % self.small_ship.health
        
        if bigship.AI == "Chasing shapes":
          if self.time > bigship.target_reevaluation:
            bigship.target_reevaluation = self.time + 0.5
            nearest = self.NearestObjectOfType(bigship.x, bigship.y, self.shapes)
            if nearest and nearest != bigship.target:
              bigship.target = nearest
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (0, 0),
                [(nearest.x, nearest.y)], bigship.max_velocity)
              bigship.path_func_start_time = self.time
              
        if bigship.AI == "Moron":
          if self.time > bigship.target_reevaluation:
            bigship.target_reevaluation = self.time + 2.0
            if (bigship.mana >= 400 or bigship.mana >= 200 and not self.NearestObjectOfType(bigship.x, bigship.y, self.shapes)) and bigship.health > 1.5:
              enemies = [ship for ship in self.ships if bigship.faction != ship.faction]
              nearest = self.NearestObjectOfType(bigship.x, bigship.y, enemies)
            elif not self.NearestObjectOfType(bigship.x, bigship.y, self.shapes):
              bigship.path_func = ships.ShipPathFromWaypoints(
                (bigship.x, bigship.y), (0, 0),
                [(random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9))],
                bigship.max_velocity)
              nearest = None
            else:
              nearest = self.NearestObjectOfType(bigship.x, bigship.y, self.shapes)
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
