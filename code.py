import time
import board
from adafruit_neotrellis.neotrellis import NeoTrellis

import math
import random

from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.sequence import AnimationSequence

# create the i2c object for the trellis
i2c_bus = board.I2C()  # uses board.SCL and board.SDA

# create the trellis
trellis = NeoTrellis(i2c_bus)

# Set the brightness value (0 to 1.0)
trellis.brightness = 0.05

# some color definitions
OFF = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)

sequence = (BLUE, RED, GREEN, YELLOW, WHITE, OFF)

time.sleep(1)  # Sleep for a bit to avoid a race condition on some systems

gridmap = [[15, 11, 7, 3], [14, 10, 6, 2], [13, 9, 5, 1], [12, 8, 4, 0]]
spiralmap = [12, 8, 4, 0, 1, 2, 3, 7, 11, 15, 14, 13, 9, 5, 6, 10]

MODE_RESET = 0
MODE_IDLE = 10
MODE_COUNT = 15
MODE_RUNNING = 20
MODE_BREAK = 30
MODE_BIGBREAK = 40

currentMode = MODE_IDLE

cycleCount = 12
cycleLength = 135
breakLength = 300

# comet = Comet(trellis.pixels, speed=0.01, color=RED, tail_length=5, bounce=True)


def fillgrid(delay, color):
    for x in gridmap:
        for y in x:
            trellis.pixels[y] = color
        time.sleep(delay)


# this will be called when button events are received
def blink(event):
    global currentMode
    global cycleStart

    print(f"event {event.number}")
    # turn the LED on when a rising edge is detected
    if event.edge == NeoTrellis.EDGE_RISING:
        trellis.pixels[event.number] = WHITE
    # turn the LED off when a falling edge is detected
    elif event.edge == NeoTrellis.EDGE_FALLING:
        trellis.pixels[event.number] = OFF

        if event.number == 0:
            if currentMode == MODE_IDLE:
                currentMode = MODE_RUNNING
                trellis.brightness = 0.5
                fillgrid(0, OFF)
                cycleStart = time.monotonic()
            else:
                currentMode = MODE_IDLE
                trellis.brightness = 0.05
                fillgrid(0.1, OFF)

            print(f"switching modes to {currentMode}")
        if event.number == 1:
            currentMode = MODE_BREAK

        if event.number == 15:
            currentMode = MODE_RESET
            fillgrid(0, OFF)

    # the trellis can only be read every 17 millisecons or so
    time.sleep(0.02)


def spiral(delay, color):
    for x in spiralmap:
        trellis.pixels[x] = color
        time.sleep(delay)


def init(event):
    global currentMode
    # spiral(WHITE)
    spiral(0, BLUE)
    fillgrid(0.15, OFF)
    currentMode = MODE_IDLE


for i in range(16):
    # activate rising edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_RISING)
    # activate falling edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
    #     # set all keys to trigger the blink callback
    trellis.callbacks[i] = blink


boot_time = time.monotonic()

init(1)

last_clock = time.monotonic()
blink_on = 0
breakStart = time.monotonic()

blinkColor = CYAN

while True:
    # call the sync function call any triggered callbacks
    trellis.sync()

    now = time.monotonic()
    # print(now)
    # for c in sequence:
    #     spiral(c)
    # the trellis can only be read every 17 millisecons or so

    if currentMode == MODE_RUNNING:
        cycleDuration = now - cycleStart
        currentBlink = 15
        squaresLitUp = math.floor(cycleDuration / cycleLength)

        for i in range(0, squaresLitUp):
            trellis.pixels[currentBlink - i] = blinkColor

        currentBlink = currentBlink - squaresLitUp

        if squaresLitUp >= cycleCount:
            currentMode = MODE_BREAK
            breakStart = time.monotonic()

        if now - last_clock > 1:
            print(
                f"Current Mode: {currentMode} Cycle Start: {cycleStart} Squares Lit: {squaresLitUp}"
            )

            if blink_on == 0:
                trellis.pixels[currentBlink] = blinkColor
                blink_on = 1

            else:
                trellis.pixels[currentBlink] = OFF
                blink_on = 0

            last_clock = time.monotonic()

    if currentMode == MODE_BREAK:
        fillgrid(0.1, GREEN)
        now = time.monotonic()

        if now - last_clock > 2:
            fillgrid(0.1, GREEN)

        if now - breakStart > breakLength:
            currentMode = MODE_IDLE

        last_clock = time.monotonic()

    if currentMode == MODE_IDLE:
        if now - last_clock > 10:
            fill = random.choice(sequence)
            spiral(0.05, fill)
            last_clock = now

    # last_clock = time.monotonic()
    time.sleep(0.02)
