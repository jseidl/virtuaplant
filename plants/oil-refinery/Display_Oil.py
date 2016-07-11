# for logging events
import logging  

# imports the twisted software and uses the reactor function to drive the inferace
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

# Log Information
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# Utility Functions
def PLCSetTag(addr, value):
    context[0x0].setValues(3, addr, [value])

def PLCGetTag(addr):
    return context[0x0].getValues(3, addr, count=1)[0]

# "Constants"
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 350
FPS=50.0

MODBUS_SERVER_PORT=5020

PLC_TAG_LEVEL_SENSOR = 0x1
PLC_TAG_LIMIT_SWITCH = 0x2
PLC_TAG_OIL_BARREL = 0x4
PLC_TAG_RUN = 0x10

#Global Variable
#global boiler

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

def add_oil(space):
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

def draw_oil(screen, ball, color=THECOLORS['brown4']):
    p = int(ball.body.position.x), 600-int(ball.body.position.y)
    pygame.draw.circle(screen, color, p, int(ball.radius), 2)

def oil_barrel(space):
    body = pymunk.Body()
    body.position = (100, 480)
    shape = pymunk.Poly.create_box(body, (80, 100), (0, 0), 0)
    space.add(shape)
    return shape

def boiler(space):
    mass = 100
    inertia = 0xFFFFFFFFF
    body = pymunk.Body(mass, inertia)
    body.position = (130,300)
    l1 = pymunk.Segment(body, (-150, 0), (-100, 0), 2.0)
    l2 = pymunk.Segment(body, (-150, 0), (-150, 100), 2.0)
    l3 = pymunk.Segment(body, (-100, 0), (-100, 100), 2.0)