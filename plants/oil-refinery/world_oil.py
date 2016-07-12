#!/usr/bin/env python

#########################################
# Imports
#########################################
# - Logging
import logging

# - Multithreading
from twisted.internet import reactor

# - Modbus
from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

# - World Simulator
import sys, random
import pygame
from pygame.locals import *
from pygame.color import *
import pymunk

import socket

#########################################
# Logging
#########################################
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

#########################################
# Util Functions
#########################################
def PLCSetTag(addr, value):
    context[0x0].setValues(3, addr, [value])

def PLCGetTag(addr):
    return context[0x0].getValues(3, addr, count=1)[0]

#########################################
# World Code
#########################################

# "Constants"
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 350
FPS=50.0

MODBUS_SERVER_PORT=5020

PLC_TAG_LEVEL_SENSOR = 0x1
PLC_TAG_LIMIT_SWITCH = 0x2
PLC_TAG_MOTOR = 0x3
PLC_TAG_NOZZLE = 0x4
PLC_TAG_RUN = 0x10

# Global Variables
global bottles
bottles = []

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

# Shape functions

def add_ball(space):
    mass = 0.01
    radius = 3
    inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
    body = pymunk.Body(mass, inertia)
    body._bodycontents.v_limit = 120
    body._bodycontents.h_limit = 1
    x = random.randint(181,182)
    body.position = x, 410
    shape = pymunk.Circle(body, radius, (0,0))
    shape.collision_type = 0x5 #liquid
    space.add(body, shape)
    return shape

def draw_ball(screen, ball, color=THECOLORS['blue']):
    p = int(ball.body.position.x), 600-int(ball.body.position.y)
    pygame.draw.circle(screen, color, p, int(ball.radius), 2)
    
def add_bottle_in_sensor(space):

    body = pymunk.Body()
    body.position = (40, 300)
    radius = 2
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x7 # 'bottle_in'
    space.add(shape)
    return shape

def add_level_sensor(space):

    body = pymunk.Body()
    body.position = (155, 380)
    radius = 3
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x4 # level_sensor
    space.add(shape)
    return shape

def add_limit_switch(space):

    body = pymunk.Body()
    body.position = (200, 300)
    radius = 2
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x1 # switch
    space.add(shape)
    return shape

def add_nozzle(space):

    body = pymunk.Body()
    body.position = (180, 430)
    shape = pymunk.Poly.create_box(body, (15, 20), (0, 0), 0)
    space.add(shape)
    return shape

def add_base(space):

    body = pymunk.Body()
    body.position = (0, 300)
    shape = pymunk.Poly.create_box(body, (SCREEN_WIDTH, 20), ((SCREEN_WIDTH/2), -10), 0)
    shape.friction = 1.0
    shape.collision_type = 0x6 # base
    space.add(shape)
    return shape

def add_bottle(space):
    mass = 10
    inertia = 0xFFFFFFFFF
    body = pymunk.Body(mass, inertia)
    body.position = (130,300)
    l1 = pymunk.Segment(body, (-80, 0), (-30, 0), 2.0)
    l2 = pymunk.Segment(body, (-80, 0), (-80, 100), 2.0)
    l3 = pymunk.Segment(body, (-30, 0), (-30, 100), 2.0)

    # Glass friction
    l1.friction = 0.94
    l2.friction = 0.94
    l3.friction = 0.94

    # Set collision types for sensors
    l1.collision_type = 0x2 # bottle_bottom
    l2.collision_type = 0x3 # bottle_side
    l3.collision_type = 0x3 # bottle_side

    space.add(l1, l2, l3, body)
    return l1,l2,l3

def draw_polygon(screen, shape):

    points = shape.get_vertices()
    fpoints = []
    for p in points:
        fpoints.append(to_pygame(p))
    pygame.draw.polygon(screen, THECOLORS['black'], fpoints)


def draw_lines(screen, lines, color=THECOLORS['dodgerblue4']):
    """Draw the lines"""
    for line in lines:
        body = line.body
        pv1 = body.position + line.a.rotated(body.angle)
        pv2 = body.position + line.b.rotated(body.angle)
        p1 = to_pygame(pv1)
        p2 = to_pygame(pv2)
        pygame.draw.lines(screen, color, False, [p1,p2])

# Collision handlers
def no_collision(space, arbiter, *args, **kwargs):
    return False

def level_ok(space, arbiter, *args, **kwargs):

    log.debug("Level reached")
    PLCSetTag(PLC_TAG_LIMIT_SWITCH, 0) # Limit Switch Release, Fill Bottle
    PLCSetTag(PLC_TAG_LEVEL_SENSOR, 1) # Level Sensor Hit, Bottle Filled
    PLCSetTag(PLC_TAG_NOZZLE, 0) # Close nozzle
    return False

def bottle_in_place(space, arbiter, *args, **kwargs):

    log.debug("Bottle in place")
    PLCSetTag(PLC_TAG_LIMIT_SWITCH, 1) 
    PLCSetTag(PLC_TAG_LEVEL_SENSOR, 0)
    PLCSetTag(PLC_TAG_NOZZLE, 1) # Open nozzle
    return False

def add_new_bottle(space, arbiter, *args, **kwargs):
    global bottles
    bottles.append(add_bottle(space))
    log.debug("Adding new bottle")
    return False

def runWorld():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bottle-Filling Factory - World View - VirtuaPlant")
    clock = pygame.time.Clock()
    running = True

    space = pymunk.Space()
    space.gravity = (0.0, -900.0)

    # Limit switch with bottle bottom
    space.add_collision_handler(0x1, 0x2, begin=bottle_in_place)
    # Level sensor with water
    space.add_collision_handler(0x4, 0x5, begin=level_ok)
    # Level sensor with ground
    space.add_collision_handler(0x4, 0x6, begin=no_collision)
    # Limit switch with ground
    space.add_collision_handler(0x1, 0x6, begin=no_collision)
    # Limit switch with bottle side
    space.add_collision_handler(0x1, 0x3, begin=no_collision)
    # Level sensor with bottle side
    space.add_collision_handler(0x4, 0x3, begin=no_collision)
    # Bottle in with bottle sides and bottom
    space.add_collision_handler(0x7, 0x2, begin=no_collision, separate=add_new_bottle)
    space.add_collision_handler(0x7, 0x3, begin=no_collision)

    base = add_base(space)
    nozzle = add_nozzle(space)
    limit_switch = add_limit_switch(space)
    level_sensor = add_level_sensor(space)
    bottle_in = add_bottle_in_sensor(space)
    
    global bottles
    bottles.append(add_bottle(space))

    balls = []

    ticks_to_next_ball = 1

    fontBig = pygame.font.SysFont(None, 40)
    fontMedium = pygame.font.SysFont(None, 26)
    fontSmall = pygame.font.SysFont(None, 18)

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        screen.fill(THECOLORS["white"])
        
        if PLCGetTag(PLC_TAG_RUN):

                # Motor Logic
                if (PLCGetTag(PLC_TAG_LIMIT_SWITCH) == 1):
                    PLCSetTag(PLC_TAG_MOTOR, 0)
                
                if (PLCGetTag(PLC_TAG_LEVEL_SENSOR) == 1):
                    PLCSetTag(PLC_TAG_MOTOR, 1)
                    
                ticks_to_next_ball -= 1
                
                if not PLCGetTag(PLC_TAG_LIMIT_SWITCH):
                    PLCSetTag(PLC_TAG_MOTOR, 1)

                if ticks_to_next_ball <= 0 and PLCGetTag(PLC_TAG_NOZZLE):
                    ticks_to_next_ball = 1
                    ball_shape = add_ball(space)
                    balls.append(ball_shape)

                # Move the bottles
                if PLCGetTag(PLC_TAG_MOTOR) == 1:
                    for bottle in bottles:
                        bottle[0].body.position.x += 0.25
        else:
            PLCSetTag(PLC_TAG_MOTOR, 0)

        # Draw water balls
        # Remove off-screen balls
        balls_to_remove = []
        for ball in balls:
            if ball.body.position.y < 150 or ball.body.position.x > SCREEN_WIDTH+150:
                balls_to_remove.append(ball)

            draw_ball(screen, ball)

        for ball in balls_to_remove:
            space.remove(ball, ball.body)
            balls.remove(ball)

        # Draw bottles
        for bottle in bottles:
            if bottle[0].body.position.x > SCREEN_WIDTH+150 or bottle[0].body.position.y < 150:
                space.remove(bottle, bottle[0].body)
                bottles.remove(bottle)
                continue
            draw_lines(screen, bottle)

        # Draw the base and nozzle
        draw_polygon(screen, base)
        draw_polygon(screen, nozzle)
        # Draw the limit switch
        draw_ball(screen, limit_switch, THECOLORS['green'])
        # Draw the level sensor
        draw_ball(screen, level_sensor, THECOLORS['red'])

        title = fontMedium.render(str("Bottle-filling factory"), 1, THECOLORS['deepskyblue'])
        name = fontBig.render(str("VirtuaPlant"), 1, THECOLORS['gray20'])
        instructions = fontSmall.render(str("(press ESC to quit)"), 1, THECOLORS['gray'])
        screen.blit(title, (10, 40))
        screen.blit(name, (10, 10))
        screen.blit(instructions, (SCREEN_WIDTH-115, 10))

        space.step(1/FPS)
        pygame.display.flip()

    # Stop reactor if running
    if reactor.running:
        reactor.callFromThread(reactor.stop)

#########################################
# Modbus Server Code
#########################################

store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [0]*100),
    co = ModbusSequentialDataBlock(0, [0]*100),
    hr = ModbusSequentialDataBlock(0, [0]*100),
    ir = ModbusSequentialDataBlock(0, [0]*100))

context = ModbusServerContext(slaves=store, single=True)

identity = ModbusDeviceIdentification()
identity.VendorName  = 'MockPLCs'
identity.ProductCode = 'MP'
identity.VendorUrl   = 'http://github.com/bashwork/pymodbus/'
identity.ProductName = 'MockPLC 3000'
identity.ModelName   = 'MockPLC Ultimate'
identity.MajorMinorRevision = '1.0'

def startModbusServer():

    StartTcpServer(context, identity=identity, address=("localhost", MODBUS_SERVER_PORT))

def main():
    reactor.callInThread(runWorld)
    startModbusServer()

if __name__ == '__main__':
    sys.exit(main())
