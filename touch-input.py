import json

import cv2
import sys
import numpy as np
from numpy.linalg import norm
import socket

IP = '127.0.0.1'
PORT = 5700

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
WINDOW_NAME = "TouchInput"

video_id = 1

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

cap = cv2.VideoCapture(video_id)
camHeight = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
camWidth = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
cv2.namedWindow(WINDOW_NAME)


def min(img):
    if len(img.shape) == 3:
        # Colored RGB or BGR (*Do Not* use HSV images with this function)
        # create brightness with euclidean norm
        return np.min(norm(img, axis=2)) / np.sqrt(3)
    else:
        # Grayscale
        return np.array(np.min(img))


def max(img):
    if len(img.shape) == 3:
        # Colored RGB or BGR (*Do Not* use HSV images with this function)
        # create brightness with euclidean norm
        return np.max(norm(img, axis=2)) / np.sqrt(3)
    else:
        # Grayscale
        return np.array(np.max(img))


class TouchHandler:

    def __init__(self):
        self.thresholdTouch = 90
        self.thresholdHover = 70
        self.lowestBright = None
        self.highestBright = None
        self.callibrated = False
        self.offsetThresholdTouch = 50
        self.offsetThresholdHover = 30

    # https://stackoverflow.com/questions/14243472/estimate-brightness-of-an-image-opencv
    def callibrate(self, img):
        if len(img.shape) == 3:
            # Colored RGB or BGR (*Do Not* use HSV images with this function)
            # create brightness with euclidean norm
            self.callibrated = True
            self.thresholdTouch = (np.average(norm(img, axis=2)) / np.sqrt(
                3)) - self.offsetThresholdTouch
            self.thresholdHover = (np.average(norm(img, axis=2)) / np.sqrt(
                3)) - self.offsetThresholdHover
        else:
            # Grayscale
            self.callibrated = True
            self.thresholdTouch = np.average(img) - self.offsetThresholdTouch
            self.thresholdHover = np.average(img) - self.offsetThresholdHover

    def check_touchEvent(self, img, gray):

        # gray_filtered = cv2.inRange(gray, lowestBright, highestBright)
        ret, thresh = cv2.threshold(gray, self.thresholdTouch, 255, cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)
        events = {}

        if len(contours) > 0:
            validContoursCounter = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 20000 > area > 2000:
                    x, y, w, h = cv2.boundingRect(cnt)
                    # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    #cv2.rectangle(img, (int(x + w / 2), int(y + h / 2)), (
                       # int((x + w / 2) + 10), int((y + h / 2) + 10)), (0, 255, 0),
                      #            2)
                    events[validContoursCounter] = {"type": "touch",
                                                    "x": (
                                                                 x + w / 2) / camWidth,
                                                    "y": (
                                                                 y + h / 2) / camHeight}
                    validContoursCounter += 1
                    # cropped = img[y:y + h, x:x + w]
            if bool(events):
                message = json.dumps({"events": events})
                # sock.sendto(message.encode(), (IP, PORT))
            return events

    def check_hoverEvents(self, img, gray, events):

        # gray_filtered = cv2.inRange(gray, lowestBright, highestBright)
        ret, thresh = cv2.threshold(gray, self.thresholdHover, 255, cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            validContoursCounter = len(events)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 20000 > area > 2000:
                    x, y, w, h = cv2.boundingRect(cnt)

                    identicalEvents = False
                    for key in events:
                        norm_x = (x + w / 2) / camWidth
                        norm_y = (y + y/2) / camHeight
                        print(abs(norm_x - events[key]['x']))
                        print(abs(norm_y - events[key]['y']))
                        if abs(norm_x - events[key]['x']) < 0.1 and abs(norm_y - events[key]['y']) < 0.1:
                            identicalEvents = True
                            break

                    if not identicalEvents:
                        # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        #cv2.rectangle(img, (int(x + w / 2), int(y + h / 2)), (
                           # int((x + w / 2) + 10), int((y + h / 2) + 10)), (255, 0, 0),
                                   #   2)
                        events[validContoursCounter] = {"type": "hover",
                                                        "x": (
                                                                     x + w / 2) / camWidth,
                                                        "y": (
                                                                     y + h / 2) / camHeight}
                        validContoursCounter += 1
                    # cropped = img[y:y + h, x:x + w]
            if bool(events):
                message = json.dumps({"events": events})
                print(message)
                sock.sendto(message.encode(), (IP, PORT))

    def process_image(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if not self.lowestBright and not self.highestBright:
            self.lowestBright = min(gray)
            self.highestBright = max(gray)

        touchEvents = self.check_touchEvent(img, gray)
        self.check_hoverEvents(img, gray, touchEvents)

        # cv2.drawContours(img, [contours], -1, (255, 255, 0), 2)
        # hull = cv2.convexHull(contours, returnPoints=False)
        # defects = cv2.convexityDefects(contours, hull)
        # if defects is not None:
        # for i in range(defects.shape[0]):
        # s, e, f, d = defects[i, 0]
        # start = tuple(contours[s][0])
        # end = tuple(contours[e][0])
        # far = tuple(contours[f][0])
        # cv2.line(img, start, end, [0, 255, 0], 2)
        # cv2.circle(img, far, 5, [0, 0, 255], -1)

        return img


touchHandler = TouchHandler()

while True:
    success, frame = cap.read()
    if success:
        if not touchHandler.callibrated:
            touchHandler.callibrate(frame)
        # print(brightness(frame))
        frame = touchHandler.process_image(frame)
        cv2.imshow(WINDOW_NAME, frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()
