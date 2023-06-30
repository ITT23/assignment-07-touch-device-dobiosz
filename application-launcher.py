import subprocess
import pyglet
from pyglet import shapes, clock
import os
from DIPPID import SensorUDP
from Recognizer.helpers import resample, IndicativeAngle, RotateBy, ScaleTo, \
    TranslateTo
from Recognizer.config import NUMPOINTS, ORIGIN, SQUARESIZE, WIDTH, HEIGHT
from Recognizer.recognizer import Recgonizer
from templates import Templates

window = pyglet.window.Window(WIDTH, HEIGHT)

# use UPD (via WiFi) for communication
PORT = 5700
sensor = SensorUDP(PORT)

# array of application paths
applications = []

# https://stackoverflow.com/questions/3277503/how-to-read-a-file-line-by-line-into-a-list
with open('applications.txt') as f:
    while line := f.readline():
        applications.append(os.path.normpath((line.rstrip())))

# save inputs
inputs = []


class ApplicationLauncher:

    def __init__(self):
        self.isDrawingWithMouse = False

        self.isDrawingWithTouchInput = False
        self.endTimer = 0

        self.shape = shapes.Circle(x=0, y=0, radius=1, segments=20,
                                   color=(255, 255, 255))
        self.shapes = []

        self.points = []
        self.creation = False
        self.recognizer = Recgonizer(Templates, False)

    # Function to create template and save
    def create_template(self, name, points):
        points = resample(points, NUMPOINTS)
        radians = IndicativeAngle(points)
        points = RotateBy(points, -radians)
        points = ScaleTo(points, SQUARESIZE)
        points = TranslateTo(points, ORIGIN)

        with open('templates.py', 'a') as f:
            template = {"name": name, "points": points}
            f.write("\n")
            f.write(str(template))
            f.close()

    def add(self, x, y):
        if not ((x, y) in self.points):
            self.points.append((x, y))

    def draw(self):
        batch = pyglet.graphics.Batch()
        for point in self.points:
            shape = shapes.Circle(x=point[0], y=point[1], radius=1,
                                  color=(255, 0, 0), batch=batch)
            self.shapes.append(shape)
        batch.draw()
        self.shapes = []

    def eventlisten(self, dx):
        if self.endTimer >= 10:
            self.eval_events()
        elif self.isDrawingWithTouchInput:
            self.endTimer += 0.1

    def receive_events(self, data):
        if bool(data):
            for event in data:
                if data[event]["type"] == "touch":
                    self.isDrawingWithTouchInput = True
                    self.points.append(
                        (data[event]["x"]*WIDTH, data[event]["y"]*HEIGHT))
                    self.endTimer = 0

    def eval_events(self):
        if self.creation:
            self.create_template("square", self.points)
        else:
            prediction = self.recognizer.recognize(self.points)

            if prediction == "circle":
                subprocess.call([applications[0]])
            elif prediction == "triangle":
                subprocess.call([applications[1]])
            elif prediction == "square":
                subprocess.call([applications[2]])

        self.isDrawingWithTouchInput = False
        self.isDrawingWithMouse = False
        self.points = []
        self.endTimer = 0


launcher = ApplicationLauncher()
sensor.register_callback('events', launcher.receive_events)


@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        launcher.isDrawingWithMouse = True

    pass


@window.event
def on_mouse_release(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        launcher.eval_events()
    pass


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if launcher.isDrawingWithMouse:
        launcher.add(x, y)
    pass


@window.event
def on_draw():
    window.clear()
    launcher.draw()


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key._3:
        pyglet.exit()


clock.schedule_interval(launcher.eventlisten, 0.001)

pyglet.app.run()
