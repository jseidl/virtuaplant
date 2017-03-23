#!/usr/bin/env python

#########################################
# Imports
#########################################
# - Logging
import  logging

# - Multithreading
from    twisted.internet    import reactor

# - World Simulator
import  sys, random, time
import  pygame
from    pygame.locals       import *
from    pygame.color        import *
import  pymunk

# - World communication
from    modbus              import ServerModbus as Server
from    modbus              import ClientModbus as Client

#########################################
# Logging
#########################################
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

#########################################
# PLC
#########################################
PLC_SERVER_IP   = "localhost"
PLC_SERVER_PORT = 502

PLC_TAG_RUN     = 0x0
PLC_TAG_LEVEL   = 0x1
PLC_TAG_CONTACT = 0x2
PLC_TAG_MOTOR   = 0x3
PLC_TAG_NOZZLE  = 0x4

#########################################
# MOTOR actuator
#########################################
MOTOR_SERVER_IP     = "localhost"
MOTOR_SERVER_PORT   = 503

MOTOR_TAG_RUN = 0x0

#########################################
# NOZZLE actuator
#########################################
NOZZLE_SERVER_IP    = "localhost"
NOZZLE_SERVER_PORT  = 504

NOZZLE_TAG_RUN = 0x0

#########################################
# LEVEL sensor
#########################################
LEVEL_SERVER_IP     = "localhost"
LEVEL_SERVER_PORT   = 505

LEVEL_TAG_SENSOR = 0x0

#########################################
# CONTACT sensor
#########################################
CONTACT_SERVER_IP   = "localhost"
CONTACT_SERVER_PORT = 506

CONTACT_TAG_SENSOR = 0x0

#########################################
# World code
#########################################
# "Constants"
WORLD_SCREEN_WIDTH  = 600
WORLD_SCREEN_HEIGHT = 350
FPS                 = 50.0

# Global Variables
global bottles
bottles = []
global plc, motor, nozzle, level, contact
plc     = {}
motor   = {}
nozzle  = {}
level   = {}
contact = {}

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

# Shape functions
def add_ball(space):
    mass    = 0.01
    radius  = 3
    inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
    x = random.randint(181,182)

    body = pymunk.Body(mass, inertia)
    body._bodycontents.v_limit = 120
    body._bodycontents.h_limit = 1
    body.position = x, 410

    shape = pymunk.Circle(body, radius, (0,0))
    shape.collision_type = 0x6 #liquid
    space.add(body, shape)

    return shape

def draw_ball(screen, ball, color=THECOLORS['blue']):
    p = int(ball.body.position.x), 600-int(ball.body.position.y)
    pygame.draw.circle(screen, color, p, int(ball.radius), 2)
    
def add_bottle_in_sensor(space):
    radius = 2

    body = pymunk.Body()
    body.position = (40, 300)

    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x8 # 'bottle_in'
    space.add(shape)

    return shape

def add_level_sensor(space):
    radius = 3

    body = pymunk.Body()
    body.position = (155, 380)

    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x5 # level_sensor
    space.add(shape)

    return shape

def add_contact_sensor(space):
    radius = 2

    body = pymunk.Body()
    body.position = (200, 300)

    shape = pymunk.Circle(body, radius, (0, 0))
    shape.collision_type = 0x1 # switch
    space.add(shape)

    return shape

def add_nozzle_actuator(space):
    body = pymunk.Body()
    body.position = (180, 430)

    shape = pymunk.Poly.create_box(body, (15, 20), (0, 0), 0)
    space.add(shape)

    return shape

def add_base(space):
    body = pymunk.Body()
    body.position = (0, 300)

    shape = pymunk.Poly.create_box(body, (WORLD_SCREEN_WIDTH, 20), ((WORLD_SCREEN_WIDTH/2), -10), 0)
    shape.friction = 1.0
    shape.collision_type = 0x7 # base
    space.add(shape)

    return shape

def add_bottle(space):
    mass = 10
    inertia = 0xFFFFFFFFF

    body = pymunk.Body(mass, inertia)
    body.position = (130,300)

    l1 = pymunk.Segment(body, (-150, 0), (-100, 0), 2.0)
    l2 = pymunk.Segment(body, (-150, 0), (-150, 100), 2.0)
    l3 = pymunk.Segment(body, (-100, 0), (-100, 100), 2.0)

    # Glass friction
    l1.friction = 0.94
    l2.friction = 0.94
    l3.friction = 0.94

    # Set collision types for sensors
    l1.collision_type = 0x2 # bottle_bottom
    l2.collision_type = 0x3 # bottle_right_side
    l3.collision_type = 0x4 # bottle_left_side

    space.add(l1, l2, l3, body)

    return l1,l2,l3

def add_new_bottle(space, arbiter, *args, **kwargs):
    global bottles

    bottles.append(add_bottle(space))

    log.debug("Adding new bottle")

    return False

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
    global level

    log.debug("Level reached")

    level['server'].write(LEVEL_TAG_SENSOR, 1)  # Level Sensor Hit, Bottle Filled

    return False

def no_level(space, arbiter, *args, **kwargs):
    global level

    log.debug("No level")

    level['server'].write(LEVEL_TAG_SENSOR, 0)

    return False

def bottle_in_place(space, arbiter, *args, **kwargs):
    global contact

    log.debug("Bottle in place")

    contact['server'].write(CONTACT_TAG_SENSOR, 1)

    return False

def no_bottle(space, arbiter, *args, **kwargs):
    global contact

    log.debug("No Bottle")

    contact['server'].write(CONTACT_TAG_SENSOR, 0)
    
    return False

def runWorld():
    pygame.init()

    screen = pygame.display.set_mode((WORLD_SCREEN_WIDTH, WORLD_SCREEN_HEIGHT))

    pygame.display.set_caption("Bottle-Filling Factory - World View - VirtuaPlant")
    clock = pygame.time.Clock()

    running = True

    space = pymunk.Space()
    space.gravity = (0.0, -900.0)

    # Contact sensor with bottle bottom
    space.add_collision_handler(0x1, 0x2, begin=no_collision)

    # Contact sensor with bottle left side
    space.add_collision_handler(0x1, 0x3, begin=no_bottle)

    # Contact sensor with bottle right side
    space.add_collision_handler(0x1, 0x4, begin=bottle_in_place)

    # Contact sensor with ground
    space.add_collision_handler(0x1, 0x7, begin=no_collision)

    # Level sensor with bottle left side
    space.add_collision_handler(0x5, 0x3, begin=no_level)

    # Level sensor with bottle right side
    space.add_collision_handler(0x5, 0x4, begin=no_collision)

    # Level sensor with water
    space.add_collision_handler(0x5, 0x6, begin=level_ok)

    # Level sensor with ground
    space.add_collision_handler(0x5, 0x7, begin=no_collision)

    # Bottle in with bottle sides and bottom
    space.add_collision_handler(0x8, 0x2, begin=no_collision, separate=add_new_bottle)
    space.add_collision_handler(0x8, 0x3, begin=no_collision)
    space.add_collision_handler(0x8, 0x4, begin=no_collision)

    base            = add_base(space)
    nozzle_actuator = add_nozzle_actuator(space)
    contact_sensor  = add_contact_sensor(space)
    level_sensor    = add_level_sensor(space)
    bottle_in       = add_bottle_in_sensor(space)
    
    global bottles
    bottles.append(add_bottle(space))

    balls = []

    ticks_to_next_ball = 1

    fontBig     = pygame.font.SysFont(None, 40)
    fontMedium  = pygame.font.SysFont(None, 26)
    fontSmall   = pygame.font.SysFont(None, 18)

    while running:
        global plc, motor, nozzle

        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        screen.fill(THECOLORS["white"])
        
        # Manage plc
        # Read remote variables and store in local
        plc['server'].write(PLC_TAG_LEVEL, plc['level'].read(LEVEL_TAG_SENSOR))
        plc['server'].write(PLC_TAG_CONTACT, plc['contact'].read(CONTACT_TAG_SENSOR))

        # Manage PLC programm
        # Motor Logic
        if plc['server'].read(PLC_TAG_RUN) and ((plc['server'].read(PLC_TAG_CONTACT) == 0) or (plc['server'].read(PLC_TAG_LEVEL) == 1)):
            plc['server'].write(PLC_TAG_MOTOR, 1)
        else:
            plc['server'].write(PLC_TAG_MOTOR, 0)

        # Nozzle Logic 
        if plc['server'].read(PLC_TAG_RUN) and (plc['server'].read(PLC_TAG_CONTACT) == 1) and (plc['server'].read(PLC_TAG_LEVEL) == 0):
            plc['server'].write(PLC_TAG_NOZZLE, 1)
        else:
            plc['server'].write(PLC_TAG_NOZZLE, 0)

        # Read local variables and store in remote
        plc['motor'].write(MOTOR_TAG_RUN, plc['server'].read(PLC_TAG_MOTOR))
        plc['nozzle'].write(NOZZLE_TAG_RUN, plc['server'].read(PLC_TAG_NOZZLE))

        # Manage nozzle actuator : filling bottle
        if nozzle['server'].read(NOZZLE_TAG_RUN) == 1:
            ball_shape = add_ball(space)
            balls.append(ball_shape)

        # Manage motor : move the bottles
        if motor['server'].read(MOTOR_TAG_RUN) == 1:
            for bottle in bottles:
                bottle[0].body.position.x += 0.25

        # Draw water balls
        # Remove off-screen balls
        balls_to_remove = []
        for ball in balls:
            if ball.body.position.y < 150 or ball.body.position.x > WORLD_SCREEN_WIDTH+150:
                balls_to_remove.append(ball)

            draw_ball(screen, ball)

        for ball in balls_to_remove:
            space.remove(ball, ball.body)

            balls.remove(ball)

        # Draw bottles
        for bottle in bottles:
            if bottle[0].body.position.x > WORLD_SCREEN_WIDTH+150 or bottle[0].body.position.y < 150:
                space.remove(bottle, bottle[0].body)

                bottles.remove(bottle)

                continue
            draw_lines(screen, bottle)

        # Draw the base and nozzle actuator
        draw_polygon(screen, base)
        draw_polygon(screen, nozzle_actuator)

        # Draw the contact sensor 
        draw_ball(screen, contact_sensor, THECOLORS['green'])

        # Draw the level sensor
        draw_ball(screen, level_sensor, THECOLORS['red'])

        title           = fontMedium.render(str("Bottle-filling factory"), 1, THECOLORS['deepskyblue'])
        name            = fontBig.render(str("VirtuaPlant"), 1, THECOLORS['gray20'])
        instructions    = fontSmall.render(str("(press ESC to quit)"), 1, THECOLORS['gray'])

        screen.blit(title, (10, 40))
        screen.blit(name, (10, 10))
        screen.blit(instructions, (WORLD_SCREEN_WIDTH-115, 10))

        space.step(1/FPS)
        pygame.display.flip()

    # Stop reactor if running
    if reactor.running:
        reactor.callFromThread(reactor.stop)

def main():
    global plc, motor, nozzle, level, contact

    # Initialise simulator
    reactor.callInThread(runWorld)

    # Initialise motor, nozzle, level and contact components
    motor['server'] = Server(MOTOR_SERVER_IP, port=MOTOR_SERVER_PORT)
    reactor.listenTCP(MOTOR_SERVER_PORT, motor['server'], interface = MOTOR_SERVER_IP,)

    nozzle['server'] = Server(NOZZLE_SERVER_IP, port=NOZZLE_SERVER_PORT)
    reactor.listenTCP(NOZZLE_SERVER_PORT, nozzle['server'], interface = NOZZLE_SERVER_IP,)

    level['server'] = Server(LEVEL_SERVER_IP, port=LEVEL_SERVER_PORT)
    reactor.listenTCP(LEVEL_SERVER_PORT, level['server'], interface = LEVEL_SERVER_IP,)

    contact['server'] = Server(CONTACT_SERVER_IP, port=CONTACT_SERVER_PORT)
    reactor.listenTCP(CONTACT_SERVER_PORT, contact['server'], interface = CONTACT_SERVER_IP)

    # Initialise plc component
    plc['server'] = Server(PLC_SERVER_IP, port=PLC_SERVER_PORT)
    reactor.listenTCP(PLC_SERVER_PORT, plc['server'], interface = PLC_SERVER_IP)

    plc['motor']    = Client(MOTOR_SERVER_IP, port=MOTOR_SERVER_PORT)
    plc['nozzle']   = Client(NOZZLE_SERVER_IP, port=NOZZLE_SERVER_PORT)
    plc['level']    = Client(LEVEL_SERVER_IP, port=LEVEL_SERVER_PORT)
    plc['contact']  = Client(CONTACT_SERVER_IP, port=CONTACT_SERVER_PORT)

    # Run World
    reactor.run()

if __name__ == '__main__':
    sys.exit(main())
