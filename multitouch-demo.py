import pyglet
from pyglet import shapes
from PIL import Image
import random
from DIPPID import SensorUDP
import math

# use UPD (via WiFi) for communication
PORT = 5700
sensor = SensorUDP(PORT)

# Load images
stairs = pyglet.image.load('./img/stairs.jpg')
tables = pyglet.image.load('./img/tables.jpg')
windows = pyglet.image.load('./img/windows.jpg')
images = [tables]

display = pyglet.canvas.get_display()
screens = display.get_screens()
window = pyglet.window.Window(fullscreen=True, screen=screens[0])


# generated with chatgpt - asked how to check if a point is within a rect
def is_point_inside_image(x, y, img):
    # Calculate the coordinates of the four corners of the rectangle
    corners = []
    angle_rad = math.radians(img.rotation)
    cos_val = math.cos(angle_rad)
    sin_val = math.sin(angle_rad)

    corners.append((img.x, img.y))
    corners.append((img.x + img.width, img.y))
    corners.append((img.x, img.y + img.height))
    corners.append((img.x + img.width, img.y + img.height))

    # Apply rotation transformation to the point
    transformed_x = (x - img.x) * cos_val - (y - img.y) * sin_val + img.x
    transformed_y = (x - img.x) * sin_val + (y - img.y) * cos_val + img.y

    # Determine if the transformed point lies within the bounds of the aligned rectangle
    if (transformed_x >= corners[0][0] and transformed_x <= corners[3][0] and
            transformed_y >= corners[0][1] and transformed_y <= corners[3][1]):
        return True

    return False


def calculate_distance(p1, p2):
    # Calculate the Euclidean distance between two points
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def calculate_angle(x1, y1, x2, y2):
    # Calculate the angle between two points with respect to the positive x-axis
    return math.atan2(y2 - y1, x2 - x1)


class ChangeableImage:

    def __init__(self, originalImage, x, y):
        # self.currentImage = originalImage
        self.imageSprite = pyglet.sprite.Sprite(originalImage, x, y)
        self.width = originalImage.width
        self.height = originalImage.height
        self.rotation = 0
        self.x = x
        self.y = y
        self.dragging = False
        self.dragOffsetX = 0
        self.dragOffsetY = 0

        self.rotating = False
        self.rotatePoint1X = 0
        self.rotatePoint1Y = 0
        self.rotatePoint2X = 0
        self.rotatePoint2Y = 0
        self.angle = 0

        self.resizing = False
        self.resizePoint1X = 0
        self.resizePoint1Y = 0
        self.resizePoint2X = 0
        self.resizePoint2Y = 0
        self.distance = 0

    def reset_states(self):
        self.dragging = False
        self.rotating = False
        self.resizing = False

    def rescale(self, factor):
        # self.width = int(self.width * factor)
        # self.height = int(self.height * factor)
        # self.currentImage.width = self.width
        # self.currentImage.height = self.height
        self.imageSprite.scale = self.imageSprite.scale * factor
        self.width = self.width * factor
        self.height = self.height * factor
        self.x = self.imageSprite.x
        self.y = self.imageSprite.y

    def drag(self, x, y):
        diff_x = x - self.dragOffsetX
        diff_y = y - self.dragOffsetY

        self.dragOffsetX = x
        self.dragOffsetY = y

        self.imageSprite.x = self.imageSprite.x + diff_x
        self.imageSprite.y = self.imageSprite.y + diff_y
        self.x = self.imageSprite.x
        self.y = self.imageSprite.y

    def rotate(self, p1_x, p1_y, p2_x, p2_y):
        initial_angle = calculate_angle(self.rotatePoint1X, self.rotatePoint1Y, self.rotatePoint2X, self.rotatePoint2Y)
        new_angle = calculate_angle(p1_x, p1_y, p2_x, p2_y)

        rotation_factor = new_angle-initial_angle

        self.imageSprite.rotation += 1

        self.x = self.imageSprite.x
        self.y = self.imageSprite.y

        self.rotatePoint1X = p1_x
        self.rotatePoint1Y = p1_y
        self.rotatePoint2X = p2_x
        self.rotatePoint2Y = p2_y

    def resize(self, p1_x, p1_y, p2_x, p2_y):
        new_distance = calculate_distance((p1_x, p1_y), (p2_x, p2_y))
        factor = new_distance / self.distance
        self.rescale(factor)

        self.resizePoint1X = p1_x
        self.resizePoint1Y = p1_y
        self.resizePoint2X = p2_x
        self.resizePoint2Y = p2_y
        self.distance = new_distance



class ImageManipulator:

    def __init__(self):
        self.minSize = 0.1
        self.maxSize = 0.5
        self.changeableImages = []
        self.windowWidth = window.get_size()[0]
        self.windowHeight = window.get_size()[1]
        self.currentEvents = []
        self.currentShapes = []
        self.hoverEvents = []
        self.initialized = False

        self.init_images_randomly()

    def init_images_randomly(self):
        for i, image in enumerate(images):
            changeableImage = ChangeableImage(image, (i * 600) + 400,
                                              ((i + 1) * 400))
            # scale = random.randint(1, 10)
            changeableImage.rescale(0.3)
            self.changeableImages.append(changeableImage)
            changeableImage.imageSprite.draw()

    def display_images(self):
        if not self.initialized:
            self.initialized = True
        self.hoverEvents = []
        self.eval_events()
        for image in self.changeableImages:
            image.imageSprite.draw()
        for event in self.hoverEvents:
            shape = shapes.Circle(int(event["x"] * self.windowWidth),
                                  int(event["y"] * self.windowHeight), 10,
                                  color=(0, 255, 0))
            shape.draw()
        for event in self.touchEvents:
            shape = shapes.Circle(int(event["x"] * self.windowWidth),
                                  int(event["y"] * self.windowHeight), 30,
                                  color=(255, 0, 0))
            shape.draw()

    def receive_events(self, data):
        self.currentEvents = []
        self.currentShapes = []
        if bool(data) and self.initialized:
            for event in data:
                self.currentEvents.append(data[event])

    def eval_events(self):
        touchEvents = []
        for event in self.currentEvents:
            if event["type"] == "hover":
                self.hoverEvents.append(event)
            else:
                touchEvents.append(event)
        self.touchEvents = touchEvents
        self.handle_events(touchEvents)

    # generated with chatgpt - asked how to check overlap of rectangle
    # corners with point
    def isCornerEvent(self, img, x, y):
        angle_rad = math.radians(img.rotation)
        cos_theta = math.cos(angle_rad)
        sin_theta = math.sin(angle_rad)

        # Calculate the coordinates of the corners based on rotation
        x_center = img.x + img.width / 2
        y_center = img.y + img.height / 2

        corners = {
            'bottom_left': (
                x_center + (img.x - x_center) * cos_theta - (
                        img.y - y_center) * sin_theta,
                y_center + (img.x - x_center) * sin_theta + (
                        img.y - y_center) * cos_theta
            ),
            'bottom_right': (
                x_center + (img.x + img.width - x_center) * cos_theta - (
                        img.y - y_center) * sin_theta,
                y_center + (img.x + img.width - x_center) * sin_theta + (
                        img.y - y_center) * cos_theta
            ),
            'top_left': (
                x_center + (img.x - x_center) * cos_theta - (
                        img.y + img.height - y_center) * sin_theta,
                y_center + (img.x - x_center) * sin_theta + (
                        img.y + img.height - y_center) * cos_theta
            ),
            'top_right': (
                x_center + (img.x + img.width - x_center) * cos_theta - (
                        img.y + img.height - y_center) * sin_theta,
                y_center + (img.x + img.width - x_center) * sin_theta + (
                        img.y + img.height - y_center) * cos_theta
            )
        }

        for corner_name, corner_coords in corners.items():
            distance = ((corner_coords[0] - x) ** 2 + (
                    corner_coords[1] - y) ** 2) ** 0.5
            if distance <= 30:
                return corner_name

        return None

    def handle_events(self, events):
        for image in self.changeableImages:
            touchedCorners = {}

            wasMoved = False
            wasRotated = False
            wasResized = False
            for event in events:
                event_x = int(event["x"] * self.windowWidth)
                event_y = int(event["y"] * self.windowHeight)

                overlap_corner = self.isCornerEvent(image, event_x, event_y)

                if overlap_corner is not None:
                    touchedCorners[overlap_corner] = {"corner": overlap_corner, "x": event_x, "y": event_y}
                if is_point_inside_image(event_x, event_y, image):
                        wasMoved = True
                        #if image.dragging:
                            #image.drag(event_x, event_y)
                        #else:
                            #image.dragging = True
                            #image.dragOffsetX = event_x
                            #image.dragOffsetY = event_y
            if not wasMoved:
                image.dragging = False

            firstCorner = ''
            secondCorner = ''

            if len(touchedCorners) == 2:
                adjacent_pairs = [('top_right', 'bottom_right'),
                                  ('bottom_right', 'top_right'),
                                  ('top_left', 'bottom_left'),
                                  ('bottom_left', 'top_left')]
                diagonal_pairs = [('top_right', 'bottom_left'),
                                  ('bottom_left', 'top_right'),
                                  ('top_left', 'bottom_right'),
                                  ('bottom_right', 'top_left')]

                if 'top_left' in touchedCorners:
                    firstCorner = "top_left"
                if 'top_right' in touchedCorners:
                    firstCorner = "top_right"
                if 'bottom_left' in touchedCorners:
                    secondCorner = "bottom_left"
                if 'bottom_right' in touchedCorners:
                    secondCorner = 'bottom_right'

                if (firstCorner, secondCorner) in adjacent_pairs or (
                        secondCorner, firstCorner) in adjacent_pairs:
                    wasRotated = True
                elif (firstCorner, secondCorner) in diagonal_pairs or (
                        secondCorner, firstCorner) in diagonal_pairs:
                    wasResized = True


                '''
                                if firstCorner == "top_right":
                    if secondCorner == "bottom_left":
                        wasResized = True
                        image.resizing = True
                    elif secondCorner == "top_left":
                        wasRotated = True
                        image.rotating = True
                    elif secondCorner == "bottom_right":
                        wasRotated = True
                        image.rotating = True
                elif secondCorner == "top_right":
                    if firstCorner == "bottom_left":
                        wasResized = True
                        image.resizing = True
                        touchedCorners = [touchedCorners[1], touchedCorners[0]]
                    elif firstCorner == "bottom_right":
                        wasRotated = True
                        image.rotating = True
                        touchedCorners = [touchedCorners[1], touchedCorners[0]]
                '''

            if wasRotated:
                if image.rotating:
                    image.rotate(touchedCorners[firstCorner]["x"], touchedCorners[firstCorner]["y"], touchedCorners[secondCorner]["x"], touchedCorners[secondCorner]["y"])
                else:
                    image.rotating = True
                    image.rotatePoint1X = touchedCorners[firstCorner]["x"]
                    image.rotatePoint1Y = touchedCorners[firstCorner]["y"]
                    image.rotatePoint2X = touchedCorners[secondCorner]["x"]
                    image.rotatePoint2Y = touchedCorners[secondCorner]["y"]
            else:
                image.rotating = False

            if wasResized:
                if image.resizing:
                    image.resize(touchedCorners[firstCorner]["x"], touchedCorners[firstCorner]["y"], touchedCorners[secondCorner]["x"], touchedCorners[secondCorner]["y"])
                else:
                    image.resizing = True
                    image.resizePoint1X = touchedCorners[firstCorner]["x"]
                    image.resizePoint1Y = touchedCorners[firstCorner]["y"]
                    image.resizePoint2X = touchedCorners[secondCorner]["x"]
                    image.resizePoint2Y = touchedCorners[secondCorner]["y"]
                    image.distance = calculate_distance(
                        (touchedCorners[firstCorner]["x"], touchedCorners[firstCorner]["y"]),
                        (touchedCorners[secondCorner]["x"], touchedCorners[secondCorner]["y"]))
            else:
                image.resizing = False


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
