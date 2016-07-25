#!/usr/bin/env python
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

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

def PLCSetTag(addr, value):
    context[0x0].setValues(3, addr, [value])

def PLCGetTag(addr):
    return context[0x0].getValues(3, addr, count=1)[0]

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 550
FPS=50.0

MODBUS_SERVER_PORT=5020

PLC_TANK_LEVEL = 0x1
PLC_INLET_VALVE = 0x2
PLC_OUTLET_VALVE = 0x2
PLC_FEED_PUMP = 0x3
PLC_DISCHARGE_PUMP = 0x3
PLC_TAG_NOZZLE = 0x4
PLC_TAG_RUN = 0x10

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

def add_ball(space):
    mass = 0.01
    radius = 3
    inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
    body = pymunk.Body(mass, inertia)
    body._bodycontents.v_limit = 120
    body._bodycontents.h_limit = 1
    x = random.randint(180, 181)
    body.position = x, 565
    shape = pymunk.Circle(body, radius, (0,0))
    shape.collision_type = 0x5 #liquid
    space.add(body, shape)
    return shape

def draw_ball(screen, ball, color=THECOLORS['black']):
    p = int(ball.body.position.x), 600-int(ball.body.position.y)
    pygame.draw.circle(screen, color, p, int(ball.radius), 2)

def outlet_valve_sensor(space):

    body = pymunk.Body()
    body.position = (185, 320)
    radius = 2
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x7 # 'bottle_in'
    space.add(shape)
    return shape

def separator_vessel_release(space):
    body = pymunk.Body()
    body.position = (380, 225)
    radius = 2
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x7
    space.add(shape)
    return shape

def tank_level_sensor(space):

    body = pymunk.Body()
    body.position = (125, 400)
    radius = 3
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x4 # tank_level
    space.add(shape)
    return shape


#def inlet_valve_sensor(space):
#
#    body = pymunk.Body()
#    body.position = (165, 415)
#    radius = 2
#    shape = pymunk.Circle(body, radius, (0, 0))
#    shape.collision_type = 0x1 # switch
#    space.add(shape)
#    return shape

def add_nozzle(space):

    body = pymunk.Body()
    body.position = (179, 585)
    shape = pymunk.Poly.create_box(body, (15, 20), (0, 0), 0)
    space.add(shape)
    return shape

def add_oil_unit(space):
    #rotation_limit_body = pymunk.Body()
    #rotation_limit_body.position = (200,300)

    #rotation_center_body = pymunk.Body()
    #rotation_center_body.position = (300,300)

    body = pymunk.Body()
    body.position = (300,300)
    #feed pump
    l1 = pymunk.Segment(body, (-100, 270), (-100, 115), 5)
    l2 = pymunk.Segment(body, (-135, 270), (-135, 115), 5)
    #l3 = pymunk.Segment(body, (-135, 115), (-100, 115), 5)
    #l3 = pymunk.Segment(body, (-250, 180), (-135, 180), 5) 
    #l4 = pymunk.Segment(body, (-215, 200), (-115, 200), 5) 
    #l5 = pymunk.Segment(body, (-135, 180), (-135, 120), 5) 
    #l6 = pymunk.Segment(body, (-115, 200), (-115, 120), 5)

    #oil storage unit
    l7 = pymunk.Segment(body, (-185, 115), (-185, 20), 5) 
    l8 = pymunk.Segment(body, (-65, 115), (-65, 20), 5) 
    l9 = pymunk.Segment(body, (-185,20), (-115, 20), 5) 
    l10 = pymunk.Segment(body, (-90, 20), (-65, 20), 5) 

    #pipe to separator vessel
    l11 = pymunk.Segment(body, (-115, 20), (-115, -45), 5)
    l12 = pymunk.Segment(body, (-90, 20), (-90, -25), 5) 
    l13 = pymunk.Segment(body, (-115, -45), (-40, -45), 5)
    l14 = pymunk.Segment(body, (-90, -25), (-40, -25), 5)

    #separator vessel
    l15 = pymunk.Segment(body, (-40, -45), (-40, -75), 5)
    l16 = pymunk.Segment(body, (-40, -25), (-40, 5), 5)
    l17 = pymunk.Segment(body, (-40, -75), (80, -75), 5)
    l18 = pymunk.Segment(body, (-40, 5), (120, 5), 5)
    l19 = pymunk.Segment(body, (100, -75), (120, -75), 5)
    l22 = pymunk.Segment(body, (120, -75), (120, -55), 5)
    l23 = pymunk.Segment(body, (120, -30), (120, 5), 5)

    #waste water pipe
    l20 = pymunk.Segment(body, (80, -75), (80, -115), 5)
    l21 = pymunk.Segment(body, (100, -75), (100, -115), 5)
    
    #separator exit pipe
    l24 = pymunk.Segment(body, (120, -30), (600, -30), 5)
    l25 = pymunk.Segment(body, (120, -55), (600, -55), 5)

    #waste water storage
    l26 = pymunk.Segment(body, (80, -115), (20, -115), 5)
    l27 = pymunk.Segment(body, (20, -115), (20, -185), 5)
    l28 = pymunk.Segment(body, (20, -185), (140, -185), 5)
    l29 = pymunk.Segment(body, (140, -185), (140, -170), 5)
    l30 = pymunk.Segment(body, (140, -145), (140, -115), 5)
    l31 = pymunk.Segment(body, (140, -115), (100, -115), 5)
    l32 = pymunk.Segment(body, (140, -145), (600, -145), 5)
    l33 = pymunk.Segment(body, (140, -170), (600, -170), 5)


    #rotation_center_joint = pymunk.PinJoint(body, rotation_center_body, (-135,115), (-100, 115))
    #joint_limit = 25
    #rotation_limit_joint = pymunk.SlideJoint(body, rotation_limit_body, (-135,115), (-100,115), 5, joint_limit)

    space.add(l1, l2, l7, l8, l9, l10, l11, l12, l13, l14, l15, 
                l16, l17, l18, l19, l20, l21, l22, l23, l24, l25, 
                l26, l27, l28, l29, l30, l31, l32, l33) # 3

    return l1,l2,l7,l8,l9,l10,l11,l12,l13,l14,l15,l16,l17,l18,l19,l20,l21,l22,l23,l24,l25,l26,l27,l28,l29,l30,l31,l32,l33

def draw_polygon(screen, shape):

    points = shape.get_vertices()
    fpoints = []
    for p in points:
        fpoints.append(to_pygame(p))
    pygame.draw.polygon(screen, THECOLORS['darkgreen'], fpoints)

def draw_lines(screen, lines):

    for line in lines:
        body = line.body
        pv1 = body.position + line.a.rotated(body.angle) # 1
        pv2 = body.position + line.b.rotated(body.angle)
        p1 = to_pygame(pv1) # 2
        p2 = to_pygame(pv2)
        pygame.draw.lines(screen, THECOLORS["black"], False, [p1,p2])

def no_collision(space, arbiter, *args, **kwargs):
    return False

def level_ok(space, arbiter, *args, **kwargs):

    log.debug("Level reached")
    PLCSetTag(PLC_INLET_VALVE, 0) # Limit Switch Release, Fill Bottle
    PLCSetTag(PLC_TANK_LEVEL, 1) # Level Sensor Hit, Bottle Filled
    PLCSetTag(PLC_TAG_NOZZLE, 0) # Close nozzle
    PLCSetTag(PLC_OUTLET_VALVE, 1)
    PLCSetTag(PLC_DISCHARGE_PUMP, 1)
    return False

def oil_storage_ready(space, arbiter, *args, **kwargs):

    log.debug("Storage bin ready")
    PLCSetTag(PLC_INLET_VALVE, 1) 
    PLCSetTag(PLC_TANK_LEVEL, 0)
    PLCSetTag(PLC_TAG_NOZZLE, 1) # Open nozzle
    PLCSetTag(PLC_OUTLET_VALVE, 0)
    PLCSetTag(PLC_DISCHARGE_PUMP, 0)
    return False

def run_world():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Crude Oil Pretreatment Unit")
    clock = pygame.time.Clock()
    running = True

    space = pymunk.Space() #2
    space.gravity = (0.0, -900.0)

    space.add_collision_handler(0x1, 0x2, begin=oil_storage_ready)
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

    space.add_collision_handler(0x7, 0x2, begin=no_collision)
    space.add_collision_handler(0x7, 0x3, begin=no_collision)   

    nozzle = add_nozzle(space)
    lines = add_oil_unit(space)
#    inlet_valve = inlet_valve_sensor(space)
    tank_level = tank_level_sensor(space)
    tank_in = outlet_valve_sensor(space)
    separator_vessel = separator_vessel_release(space)
    outlet_valve = outlet_valve_sensor(space)
    
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

        screen.fill(THECOLORS["grey"])

        if PLCGetTag(PLC_TAG_RUN):

                # Motor Logic
                if (PLCGetTag(PLC_FEED_PUMP) == 1):
                    PLCSetTag(PLC_INLET_VALVE, 1)
                    PLCSetTag(PLC_TAG_NOZZLE, 1)

                if (PLCGetTag(PLC_INLET_VALVE) == 1):
                    PLCSetTag(PLC_OUTLET_VALVE, 0)
                    PLCSetTag(PLC_DISCHARGE_PUMP, 0)

                if (PLCGetTag(PLC_TANK_LEVEL) == 1):
                    
                    PLCSetTag(PLC_OUTLET_VALVE, 1)
                    PLCSetTag(PLC_DISCHARGE_PUMP, 1)
                
                if (PLCGetTag(PLC_OUTLET_VALVE) == 1):
                    PLCSetTag(PLC_FEED_PUMP, 0)
                    PLCSetTag(PLC_INLET_VALVE, 0)
                    PLCSetTag(PLC_TAG_NOZZLE, 0)
                ticks_to_next_ball -= 1
                
                if not PLCGetTag(PLC_INLET_VALVE):
                    PLCSetTag(PLC_FEED_PUMP, 1)

                if ticks_to_next_ball <= 0 and PLCGetTag(PLC_TAG_NOZZLE):
                    ticks_to_next_ball = 1
                    ball_shape = add_ball(space)
                    balls.append(ball_shape)
        else:
            PLCSetTag(PLC_TAG_NOZZLE, 0)


        balls_to_remove = []
        for ball in balls:
            if ball.body.position.y < 0 or ball.body.position.x > SCREEN_WIDTH+150:
                balls_to_remove.append(ball)

            draw_ball(screen, ball)

        for ball in balls_to_remove:
            space.remove(ball, ball.body)
            balls.remove(ball)

        draw_polygon(screen, nozzle)
        draw_lines(screen, lines)
        draw_ball(screen, inlet_valve, THECOLORS['red'])
        draw_ball(screen, tank_level, THECOLORS['red'])
        draw_ball(screen, separator_vessel, THECOLORS['red'])
        draw_ball(screen, outlet_valve, THECOLORS['red'])

        title = fontMedium.render(str("Crude Oil Pretreatment Unit"), 1, THECOLORS['blue'])
        name = fontBig.render(str("VirtuaPlant"), 1, THECOLORS['gray20'])
        instructions = fontSmall.render(str("(press ESC to quit)"), 1, THECOLORS['gray'])
        feed_pump_label = fontMedium.render(str("Feed Pump"), 1, THECOLORS['blue'])
        oil_storage_label = fontMedium.render(str("Oil Storage Unit"), 1, THECOLORS['blue'])
        separator_label = fontMedium.render(str("Separator Vessel"), 1, THECOLORS['blue'])
        waste_water_label = fontMedium.render(str("Waste Water Treatment Unit"), 1, THECOLORS['blue'])
        screen.blit(title, (300, 40))
        screen.blit(name, (347, 10))
        screen.blit(instructions, (SCREEN_WIDTH-115, 10))
        screen.blit(feed_pump_label, (65, 80))
        screen.blit(oil_storage_label, (240, 190))
        screen.blit(separator_label, (270,275))
        screen.blit(waste_water_label, (265, 490))

        space.step(1/FPS) 
        pygame.display.flip()

    if reactor.running:
        reactor.callFromThread(reactor.stop)

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
identity.ProductName = 'MockPLC 4000'
identity.ModelName   = 'MockPLC Platinum'
identity.MajorMinorRevision = '1.0'

def startModbusServer():

    StartTcpServer(context, identity=identity, address=("localhost", MODBUS_SERVER_PORT))

def main():
    reactor.callInThread(run_world)
    startModbusServer()

if __name__ == '__main__':
    sys.exit(main())
