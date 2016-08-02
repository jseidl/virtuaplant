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

import argparse
import os
import sys
import time

# Override Argument parser to throw error and generate help message
# if undefined args are passed
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)
        
# Create argparser object to add command line args and help option
parser = MyParser(
	description = 'This Python script starts the SCADA/ICS World Server',
	epilog = '',
	add_help = True)
	
# Add a "-i" argument to receive a filename
parser.add_argument("-t", action = "store", dest="server_addr",
					help = "Modbus server IP address to listen on")

# Print help if no args are supplied
if len(sys.argv)==1:
	parser.print_help()
	sys.exit(1)
	
# Split and process arguments into "args"
args = parser.parse_args()

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# Helper function to set PLC values
def PLCSetTag(addr, value):
    context[0x0].setValues(3, addr, [value])

# Helper function that returns PLC values
def PLCGetTag(addr):
    return context[0x0].getValues(3, addr, count=1)[0]

# Display settings
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 550
FPS=50.0

# Port the world will listen on
MODBUS_SERVER_PORT=5020

# Amount of oil spilled/processed
oil_spilled_amount = 0
oil_processed_amount = 0

# PLC Register values for various control functions
PLC_FEED_PUMP = 0x01
PLC_TANK_LEVEL = 0x02
PLC_OUTLET_VALVE = 0x03
PLC_SEP_VESSEL = 0x04
PLC_SEP_FEED = 0x05
PLC_OIL_SPILL = 0x06
PLC_OIL_PROCESSED = 0x07

# Collision types
tank_level_collision = 0x4
ball_collision = 0x5
separator_collision = 0x8
sep_vessel_collision = 0x7
oil_spill_collision = 0x9

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

# Add "oil" to the world space
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
    shape.collision_type = ball_collision #liquid
    space.add(body, shape)
    return shape

# Add a ball to the space
def draw_ball(screen, ball, color=THECOLORS['brown']):
    p = int(ball.body.position.x), 600-int(ball.body.position.y)
    pygame.draw.circle(screen, color, p, int(ball.radius), 2)

# Add the separator vessel feed
def separator_vessel_feed(space):
    body = pymunk.Body()
    body.position = (420, 257)
    radius = 4
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = separator_collision # Collision value for separator
    space.add(shape)
    return shape

# Add the separator vessel release
def separator_vessel_release(space):
    body = pymunk.Body()
    body.position = (387, 225)
    radius = 4
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = sep_vessel_collision
    space.add(shape)
    return shape

# Add the tank level sensor 
def tank_level_sensor(space):
    body = pymunk.Body()
    body.position = (125, 400)
    radius = 3
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = tank_level_collision # tank_level
    space.add(shape)
    return shape
    
def oil_spill_sensor(space):
    body = pymunk.Body()
    body.position = (0, 0)
    radius = 7
    a = (0, 75)
    b = (SCREEN_WIDTH, 75)
    shape = pymunk.Segment(body, a, b, radius)
    shape.collision_type = oil_spill_collision # oil spill sensor
    space.add(shape)
    return shape

# Add the feed pump to the space
def add_pump(space):
    body = pymunk.Body()
    body.position = (179, 585)
    shape = pymunk.Poly.create_box(body, (15, 20), (0, 0), 0)
    space.add(shape)
    return shape

# Draw the various "pipes" that the oil flows through
# TODO: Get rid of magic numbers and add constants + offsets
def add_oil_unit(space):
    body = pymunk.Body()
    body.position = (300,300)
    
    #feed pump
    l1 = pymunk.Segment(body, (-100, 270), (-100, 145), 5)
    l2 = pymunk.Segment(body, (-135, 270), (-135, 145), 5)

    #oil storage unit
    l7 = pymunk.Segment(body, (-185, 130), (-185, 20), 5) 
    l8 = pymunk.Segment(body, (-65, 130), (-65, 20), 5) 
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
    l17 = pymunk.Segment(body, (-40, -75), (75, -75), 5)
    l18 = pymunk.Segment(body, (-40, 5), (120, 5), 5)
    l19 = pymunk.Segment(body, (100, -75), (120, -75), 5)
    l22 = pymunk.Segment(body, (120, -75), (120, -55), 5)
    l23 = pymunk.Segment(body, (120, -30), (120, 5), 5)

    #waste water pipe
    l20 = pymunk.Segment(body, (75, -75), (75, -115), 5)
    l21 = pymunk.Segment(body, (100, -75), (100, -115), 5)
    
    #separator exit pipe
    l24 = pymunk.Segment(body, (120, -30), (600, -30), 5)
    l25 = pymunk.Segment(body, (120, -55), (600, -55), 5)

    #waste water storage
    l26 = pymunk.Segment(body, (75, -115), (20, -115), 5)
    l27 = pymunk.Segment(body, (20, -115), (20, -185), 5)
    l28 = pymunk.Segment(body, (20, -185), (140, -185), 5)
    l29 = pymunk.Segment(body, (140, -185), (140, -170), 5)
    l30 = pymunk.Segment(body, (140, -145), (140, -115), 5)
    l31 = pymunk.Segment(body, (140, -115), (100, -115), 5)
    l32 = pymunk.Segment(body, (140, -145), (600, -145), 5)
    l33 = pymunk.Segment(body, (140, -170), (600, -170), 5)

    space.add(l1, l2, l7, l8, l9, l10, l11, l12, l13, l14, l15, 
                l16, l17, l18, l19, l20, l21, l22, l23, l24, l25, 
                l26, l27, l28, l29, l30, l31, l32, l33) # 3

    return l1,l2,l7,l8,l9,l10,l11,l12,l13,l14,l15,l16,l17,l18,l19,l20,l21,l22,l23,l24,l25,l26,l27,l28,l29,l30,l31,l32,l33

def draw_polygon(screen, shape):
    points = shape.get_vertices()
    fpoints = []
    for p in points:
        fpoints.append(to_pygame(p))
    pygame.draw.polygon(screen, THECOLORS['black'], fpoints)
    
# Draw a single line to the screen
def draw_line(screen, line, color = None):
    body = line.body
    pv1 = body.position + line.a.rotated(body.angle) # 1
    pv2 = body.position + line.b.rotated(body.angle)
    p1 = to_pygame(pv1) # 2
    p2 = to_pygame(pv2)
    if color is None:
        pygame.draw.lines(screen, THECOLORS["black"], False, [p1,p2])
    else:
        pygame.draw.lines(screen, color, False, [p1,p2])
    
# Draw lines from an iterable list
def draw_lines(screen, lines):
    for line in lines:
        body = line.body
        pv1 = body.position + line.a.rotated(body.angle) # 1
        pv2 = body.position + line.b.rotated(body.angle)
        p1 = to_pygame(pv1) # 2
        p2 = to_pygame(pv2)
        pygame.draw.lines(screen, THECOLORS["black"], False, [p1,p2])

# Default collision function for objects
# Returning true makes the two objects collide normally just like "walls/pipes"
def no_collision(space, arbiter, *args, **kwargs):
    return True 

# Called when level sensor in tank is hit
def level_reached(space, arbiter, *args, **kwargs):
    log.debug("Level reached")
    PLCSetTag(PLC_TANK_LEVEL, 1) # Level Sensor Hit, Tank full
    PLCSetTag(PLC_FEED_PUMP, 0) # Turn off the pump
    PLCSetTag(PLC_OUTLET_VALVE, 1) # Set the outlet valve to 1
    return False
    
def oil_spilled(space, arbiter, *args, **kwargs):
    log.debug("Oil Spilled")
    oil_spilled_amount += 1
    PLCSetTag(PLC_OIL_SPILL, oil_spilled_amount) # We lost a unit of oil
    PLCSetTag(PLC_FEED_PUMP, 0) # Attempt to shut off the pump
    return False   
    
# This fires when the separator level is hit    
def sep_on(space, arbiter, *args, **kwargs):
    log.debug("Begin separation")
    PLCSetTag(PLC_SEP_VESSEL, 1) # Sep vessel hit, begin processing
    return False
    
# This fires when the separator is not processing
def sep_off(space, arbiter, *args, **kwargs):
    log.debug("Begin separation")
    PLCSetTag(PLC_SEP_VESSEL, 0) # Sep vessel hit, begin processing
    return False

def sep_feed_on(space, arbiter, *args, **kwargs):
    log.debug("Outlet Feed")
    PLCSetTag(PLC_SEP_FEED, 1)
    return False

def run_world():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Crude Oil Pretreatment Unit")
    clock = pygame.time.Clock()
    running = True

    # Create game space (world) and set gravity to normal
    space = pymunk.Space() #2
    space.gravity = (0.0, -900.0)
    
    # When oil collides with tank_level, call level_reached
    space.add_collision_handler(tank_level_collision, ball_collision, begin=level_reached)
    space.add_collision_handler(oil_spill_collision, ball_collision, begin=oil_spilled)

    pump = add_pump(space)
    lines = add_oil_unit(space)
    tank_level = tank_level_sensor(space)
    separator_vessel = separator_vessel_release(space)
    separator_feed = separator_vessel_feed(space)
    separator_feed = separator_vessel_feed(space)
    oil_spill = oil_spill_sensor(space)
    

    balls = []

    ticks_to_next_ball = 1

    # Set font settings
    fontBig = pygame.font.SysFont(None, 40)
    fontMedium = pygame.font.SysFont(None, 26)
    fontSmall = pygame.font.SysFont(None, 18)

    while running:
        # Advance the game clock
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        screen.fill(THECOLORS["grey"])

        # If the feed pump is on
        if PLCGetTag(PLC_FEED_PUMP) == 1:
            # Draw the valve if the pump is on
            # If the oil reaches the level sensor at the top of the tank
            if (PLCGetTag(PLC_TANK_LEVEL) == 1):
                PLCSetTag(PLC_FEED_PUMP, 0)
                space.add_collision_handler(sep_vessel_collision, ball_collision, begin=sep_on)
                space.add_collision_handler(separator_collision, ball_collision, begin=sep_feed_on)
                
            
        # If the separator process is turned on
        if PLCGetTag(PLC_SEP_VESSEL) == 1:
            space.add_collision_handler(sep_vessel_collision, ball_collision, begin=sep_on)
            space.add_collision_handler(separator_collision, ball_collision, begin=sep_feed_on)
        else:
            space.add_collision_handler(sep_vessel_collision, ball_collision, begin=no_collision)
            space.add_collision_handler(separator_collision, ball_collision, begin=no_collision)
            
            
        ticks_to_next_ball -= 1

        if ticks_to_next_ball <= 0 and PLCGetTag(PLC_FEED_PUMP) == 1:
            ticks_to_next_ball = 1
            ball_shape = add_ball(space)
            balls.append(ball_shape)
            
        balls_to_remove = []
        for ball in balls:
            if ball.body.position.y < 0 or ball.body.position.x > SCREEN_WIDTH+150:
                balls_to_remove.append(ball)

            draw_ball(screen, ball)

        for ball in balls_to_remove:
            space.remove(ball, ball.body)
            balls.remove(ball)

        draw_polygon(screen, pump)
        draw_lines(screen, lines)
        draw_ball(screen, tank_level, THECOLORS['black'])
        draw_ball(screen, separator_vessel, THECOLORS['black'])
        draw_ball(screen, separator_feed, THECOLORS['black'])
        draw_line(screen, oil_spill, THECOLORS['red'])

        #draw_ball(screen, separator_feed, THECOLORS['red'])
        title = fontMedium.render(str("Crude Oil Pretreatment Unit"), 1, THECOLORS['blue'])
        name = fontBig.render(str("VirtuaPlant"), 1, THECOLORS['gray20'])
        instructions = fontSmall.render(str("(press ESC to quit)"), 1, THECOLORS['gray'])
        feed_pump_label = fontMedium.render(str("Feed Pump"), 1, THECOLORS['blue'])
        oil_storage_label = fontMedium.render(str("Oil Storage Unit"), 1, THECOLORS['blue'])
        separator_label = fontMedium.render(str("Separator Vessel"), 1, THECOLORS['blue'])
        waste_water_label = fontMedium.render(str("Waste Water Treatment Unit"), 1, THECOLORS['blue'])
        tank_sensor = fontSmall.render(str("Tank Level Sensor"), 1, THECOLORS['blue'])
        separator_release = fontSmall.render(str("Separator Vessel Release Sensor"), 1, THECOLORS['blue'])
        waste_sensor = fontSmall.render(str("Waste Water Sensor"), 1, THECOLORS['blue'])
        
        screen.blit(title, (300, 40))
        screen.blit(name, (347, 10))
        screen.blit(instructions, (SCREEN_WIDTH-115, 10))
        screen.blit(feed_pump_label, (65, 80))
        screen.blit(oil_storage_label, (240, 190))
        screen.blit(separator_label, (270,275))
        screen.blit(waste_water_label, (265, 490))
        screen.blit(tank_sensor, (10, 187))
        screen.blit(separator_release, (425, 315))
        screen.blit(waste_sensor, (402, 375))

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

# Modbus PLC server information
identity = ModbusDeviceIdentification()
identity.VendorName  = 'Siemens Oil Refining Platform'
identity.ProductCode = 'SORP'
identity.VendorUrl   = 'http://w3.siemens.com/markets/global/en/oil-gas/pages/refining-petrochemical-industry.aspx'
identity.ProductName = 'SORP 3850'
identity.ModelName   = 'Siemens ORP 3850'
identity.MajorMinorRevision = '2.09.01'

def startModbusServer():
    # Run a modbus server on specified address and modbus port (5020)
    StartTcpServer(context, identity=identity, address=(args.server_addr, MODBUS_SERVER_PORT))

def main():
    reactor.callInThread(run_world)
    startModbusServer()

if __name__ == '__main__':
    sys.exit(main())
