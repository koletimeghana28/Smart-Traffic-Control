import random
import time
import threading
import pygame
import sys
import os

# Default signal timings
defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
defaultRed = 150
defaultYellow = 5

signals = []
noOfSignals = 4
currentGreen = 0
nextGreen = 1
currentYellow = 0

speeds = {
    'car': 2.25,
    'bus': 1.8,
    'truck': 1.8,
    'bike': 2.5
}

# Vehicle starting positions
x = {
    'right': [0, 0, 0],
    'down': [755, 727, 697],
    'left': [1400, 1400, 1400],
    'up': [602, 627, 657]
}

y = {
    'right': [348, 370, 398],
    'down': [0, 0, 0],
    'left': [498, 466, 436],
    'up': [800, 800, 800]
}

vehicles = {
    'right': {0: [], 1: [], 2: [], 'crossed': 0},
    'down': {0: [], 1: [], 2: [], 'crossed': 0},
    'left': {0: [], 1: [], 2: [], 'crossed': 0},
    'up': {0: [], 1: [], 2: [], 'crossed': 0}
}

vehicleTypes = {
    0: 'car',
    1: 'bus',
    2: 'truck',
    3: 'bike'
}

directionNumbers = {
    0: 'right',
    1: 'down',
    2: 'left',
    3: 'up'
}

signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

stopLines = {
    'right': 590,
    'down': 330,
    'left': 800,
    'up': 535
}

defaultStop = {
    'right': 580,
    'down': 320,
    'left': 810,
    'up': 545
}

stoppingGap = 15
movingGap = 15

pygame.init()
simulation = pygame.sprite.Group()


class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction):
        super().__init__()

        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0

        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1

        image_path = f"images/{direction}/{vehicleClass}.png"

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing image: {image_path}")

        self.image = pygame.image.load(image_path)

        if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
            previous = vehicles[direction][lane][self.index - 1]

            if direction == 'right':
                self.stop = previous.stop - previous.image.get_rect().width - stoppingGap
            elif direction == 'left':
                self.stop = previous.stop + previous.image.get_rect().width + stoppingGap
            elif direction == 'down':
                self.stop = previous.stop - previous.image.get_rect().height - stoppingGap
            else:
                self.stop = previous.stop + previous.image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]

        if direction == 'right':
            x[direction][lane] -= self.image.get_rect().width + stoppingGap
        elif direction == 'left':
            x[direction][lane] += self.image.get_rect().width + stoppingGap
        elif direction == 'down':
            y[direction][lane] -= self.image.get_rect().height + stoppingGap
        elif direction == 'up':
            y[direction][lane] += self.image.get_rect().height + stoppingGap

        simulation.add(self)

    def move(self):
        if self.direction == 'right':
            if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = 1

            if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or
                 (currentGreen == 0 and currentYellow == 0)) and
                    (self.index == 0 or
                     self.x + self.image.get_rect().width <
                     vehicles[self.direction][self.lane][self.index - 1].x - movingGap)):
                self.x += self.speed

        elif self.direction == 'down':
            if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                self.crossed = 1

            if ((self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or
                 (currentGreen == 1 and currentYellow == 0)) and
                    (self.index == 0 or
                     self.y + self.image.get_rect().height <
                     vehicles[self.direction][self.lane][self.index - 1].y - movingGap)):
                self.y += self.speed

        elif self.direction == 'left':
            if self.crossed == 0 and self.x < stopLines[self.direction]:
                self.crossed = 1

            if ((self.x >= self.stop or self.crossed == 1 or
                 (currentGreen == 2 and currentYellow == 0)) and
                    (self.index == 0 or
                     self.x >
                     vehicles[self.direction][self.lane][self.index - 1].x +
                     vehicles[self.direction][self.lane][self.index - 1].image.get_rect().width + movingGap)):
                self.x -= self.speed

        elif self.direction == 'up':
            if self.crossed == 0 and self.y < stopLines[self.direction]:
                self.crossed = 1

            if ((self.y >= self.stop or self.crossed == 1 or
                 (currentGreen == 3 and currentYellow == 0)) and
                    (self.index == 0 or
                     self.y >
                     vehicles[self.direction][self.lane][self.index - 1].y +
                     vehicles[self.direction][self.lane][self.index - 1].image.get_rect().height + movingGap)):
                self.y -= self.speed


def initialize():
    signals.clear()

    ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, defaultGreen[1])
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])

    signals.extend([ts1, ts2, ts3, ts4])


def updateValues():
    global currentGreen, currentYellow

    for i in range(noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1


def signalController():
    global currentGreen, nextGreen, currentYellow

    while True:
        while signals[currentGreen].green > 0:
            updateValues()
            time.sleep(1)

        currentYellow = 1

        for i in range(3):
            for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen]]

        while signals[currentGreen].yellow > 0:
            updateValues()
            time.sleep(1)

        currentYellow = 0

        signals[currentGreen].green = defaultGreen[currentGreen]
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed

        currentGreen = nextGreen
        nextGreen = (currentGreen + 1) % noOfSignals
        signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green


def generateVehicles():
    while True:
        vehicle_type = random.randint(0, 3)
        lane_number = random.randint(1, 2)
        temp = random.randint(0, 99)

        if temp < 25:
            direction_number = 0
        elif temp < 50:
            direction_number = 1
        elif temp < 75:
            direction_number = 2
        else:
            direction_number = 3

        Vehicle(
            lane_number,
            vehicleTypes[vehicle_type],
            direction_number,
            directionNumbers[direction_number]
        )

        time.sleep(1)


class Simulation:
    def runSimulation(self):
        initialize()

        threading.Thread(target=signalController, daemon=True).start()
        threading.Thread(target=generateVehicles, daemon=True).start()

        screenWidth = 1400
        screenHeight = 800

        screen = pygame.display.set_mode((screenWidth, screenHeight))
        pygame.display.set_caption("Traffic Simulation")

        background = pygame.image.load('images/intersection.png')
        redSignal = pygame.image.load('images/signals/red.png')
        yellowSignal = pygame.image.load('images/signals/yellow.png')
        greenSignal = pygame.image.load('images/signals/green.png')

        font = pygame.font.Font(None, 30)

        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            screen.blit(background, (0, 0))

            for i in range(noOfSignals):
                if i == currentGreen:
                    if currentYellow:
                        signals[i].signalText = signals[i].yellow
                        screen.blit(yellowSignal, signalCoods[i])
                    else:
                        signals[i].signalText = signals[i].green
                        screen.blit(greenSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].red if signals[i].red <= 10 else "---"
                    screen.blit(redSignal, signalCoods[i])

            for i in range(noOfSignals):
                signalText = font.render(str(signals[i].signalText), True, (255, 255, 255), (0, 0, 0))
                screen.blit(signalText, signalTimerCoods[i])

            for vehicle in simulation:
                screen.blit(vehicle.image, [vehicle.x, vehicle.y])
                vehicle.move()

            pygame.display.update()

        pygame.quit()