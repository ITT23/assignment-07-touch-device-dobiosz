import pyglet
from pyglet import shapes
from PIL import Image
import random
from DIPPID import SensorUDP

# use UPD (via WiFi) for communication
PORT = 5700
sensor = SensorUDP(PORT)

# Load images
stairs = pyglet.image.load('./img/stairs.jpg')
tables = pyglet.image.load('./img/tables.jpg')
windows = pyglet.image.load('./img/windows.jpg')
images = [stairs, tables, windows]

display = pyglet.canvas.get_display()
screens = display.get_screens()
window = pyglet.window.Window(fullscreen=True, screen=screens[0])


class ChangeableImage:

    def __init__(self, originalImage, x, y):
        self.currentImage = originalImage
        self.width = originalImage.width
        self.height = originalImage.height
        self.rotation = 0
        self.x = x
        self.y = y

    def rescale(self, factor):
        self.width = int(self.width * factor)
        self.height = int(self.height * factor)
        self.currentImage.width = self.width
        self.currentImage.height = self.height

    def rotate(self):
        print("test")
        # TODO: Rotate image


class ImageManipulator:

    def __init__(self):
        self.minSize = 0.1
        self.maxSize = 0.5
        self.changeableImages = []
        self.init_images_randomly()
        self.windowWidth = window.get_size()[0]
        self.windowHeight = window.get_size()[1]
        self.currentShapes = None

    def init_images_randomly(self):
        for image in images:
            changeableImage = ChangeableImage(image, 0, 0)
            scale = random.randint(1, 10)
            changeableImage.rescale(1 / scale)
            self.changeableImages.append(changeableImage)
            changeableImage.currentImage.blit(0, 0)

    def display_images(self):
        for image in self.changeableImages:
            image.currentImage.blit(0, 0)
        if self.currentShapes:
            self.currentShapes.draw()

    def receive_events(self, data):
        self.currentShapes = None
        if bool(data):
            self.eval_events(data)

    def eval_events(self, events):
        for event in events:
            x = int(events[event]['x'] * self.windowWidth)
            y = int(events[event]['y'] * self.windowHeight)
            print(x)
            print(y)
            shape = shapes.Circle(500, 500, 10, color=(255, 0, 0))
            self.currentShapes = shape
        print(events)


imageMan = ImageManipulator()
sensor.register_callback('events', imageMan.receive_events)


@window.event
def on_draw():
    window.clear()
    imageMan.display_images()


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key._3:
        pyglet.app.exit()


pyglet.app.run()
