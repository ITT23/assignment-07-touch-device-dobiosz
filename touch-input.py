import json
import cv2
import sys
import numpy as np
from numpy.linalg import norm
import socket
from Recognizer.config import CAMWIDTH, CAMHEIGHT
from collections import Counter

IP = '127.0.0.1'
PORT = 5700

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
WINDOW_NAME = "TouchInput"

video_id = 1

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

cap = cv2.VideoCapture(video_id)
cv2.namedWindow(WINDOW_NAME)


class TouchHandler:

    def __init__(self):
        self.thresholdTouch = 80
        self.thresholdTouchEstimations = []
        self.thresholdHoverEstimations = []
        self.thresholdHover = 100
        self.touchCallibrated = False
        self.hoverCallibrated = False
        self.offsetThresholdTouch = 30
        self.offsetThresholdHover = 30
        self.pause = 0

    # returns found touchEvents
    def check_touchEvent(self, img, gray):
        ret, thresh = cv2.threshold(gray, self.thresholdTouch, 255,
                                    cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)
        events = {}

        if len(contours) > 0:
            validContoursCounter = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 20000 > area > 2000:
                    x, y, w, h = cv2.boundingRect(cnt)
                    events[validContoursCounter] = {"type": "touch",
                                                    "x": (x + w / 2) / CAMWIDTH,
                                                    "y": 1 - ((y + h / 2) / CAMHEIGHT),
                                                    }
                    validContoursCounter += 1

            return events

    # returns found hoverEvents
    def check_hoverEvents(self, img, gray, events):
        ret, thresh = cv2.threshold(gray, self.thresholdHover, 255,
                                    cv2.THRESH_BINARY)

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
                        norm_x = (x + w / 2) / CAMWIDTH
                        norm_y = (y + y / 2) / CAMHEIGHT
                        if abs(norm_x - events[key]['x']) < 0.1 and abs(
                                norm_y - events[key]['y']) < 0.1:
                            identicalEvents = True
                            break

                    if not identicalEvents:
                        events[validContoursCounter] = {"type": "hover",
                                                        "x": (x + w / 2) / CAMWIDTH,
                                                        "y": 1 - ((y + h / 2) / CAMHEIGHT)
                                                        }
                        validContoursCounter += 1
            if bool(events):
                for event in events:
                    x = int(events[event]["x"] * CAMWIDTH)
                    y = int(events[event]["y"] * CAMHEIGHT)
                    color = (255, 0, 0) if events[event]["type"] == "touch" else (0, 255, 0)
                    cv2.rectangle(img, (x, CAMHEIGHT - y), (x + 100, CAMHEIGHT - y + 100), color, 2)

                message = json.dumps({"events": events})
                sock.sendto(message.encode(), (IP, PORT))

    # checks how many fingers are found for callibration
    def callibrate(self, gray, threshValue):
        ret, thresh = cv2.threshold(gray, threshValue, 255,
                                    cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            validContoursCounter = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 20000 > area > 2000:
                    validContoursCounter += 1
            return validContoursCounter

    # processing logic for current frame
    def process_image(self, img):
        if self.pause == 0:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if self.touchCallibrated and self.hoverCallibrated:

                touchEvents = self.check_touchEvent(img, gray)
                self.check_hoverEvents(img, gray, touchEvents)

            elif not self.touchCallibrated:
                contoursFound = self.callibrate(gray, self.thresholdTouch)

                if len(self.thresholdTouchEstimations) == 20:
                    best_estimation = Counter(self.thresholdTouchEstimations).most_common(1)[0][0]
                    self.thresholdTouch = best_estimation
                    self.touchCallibrated = True
                    self.pause = 180

                elif contoursFound == 3:
                    self.thresholdTouchEstimations.append(self.thresholdTouch)
                    self.thresholdTouch += 1
                    if self.thresholdTouch == 100:
                        self.thresholdTouch = 70
                else:
                    self.thresholdTouch += 1
                    if self.thresholdTouch == 100:
                        self.thresholdTouch = 70

            else:
                contoursFound = self.callibrate(gray, self.thresholdHover)
                if len(self.thresholdHoverEstimations) == 50:
                    best_estimation = Counter(self.thresholdHoverEstimations).most_common(1)[0][0]
                    self.thresholdHover = best_estimation
                    self.hoverCallibrated = True

                elif contoursFound == 3:
                    self.thresholdHoverEstimations.append(self.thresholdHover)
                    self.thresholdHover += 1
                    if self.thresholdHover == 130:
                        self.thresholdHover = 80
                else:
                    self.thresholdHover += 1
                    if self.thresholdHover == 130:
                        self.thresholdHover = 80
        return img

    # When callibration is not working use default values
    def useDefaultHover(self, img):
        if self.touchCallibrated and not self.hoverCallibrated:
            self.hoverCallibrated = True
            brightness = np.average(norm(img, axis=2)) / np.sqrt(
                3)
            self.thresholdHover = brightness + 15
        elif not self.touchCallibrated and not self.hoverCallibrated:
            self.touchCallibrated = True
            self.hoverCallibrated = True
            brightness = np.average(norm(img, axis=2)) / np.sqrt(
                3)
            self.thresholdHover = brightness + 15
            self.thresholdTouch = 80

    def callibrationText(self, img):
        if self.pause > 0:
            time = 3 if self.pause > 120 else 2 if self.pause > 60 else 1
            cv2.putText(img, str(time),
                        (int(CAMWIDTH / 3), int(CAMHEIGHT / 2)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        3,
                        (0, 255, 0),
                        1,
                        2)
            self.pause -= 1
        elif not self.touchCallibrated:
            cv2.putText(img, 'Touch the sensor with 3 fingers',
                        (50, int(CAMHEIGHT / 3)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2,
                        (0, 255, 0),
                        1,
                        2)
            cv2.putText(img, 'Callibrating...',
                        (int(CAMWIDTH / 3), int(CAMHEIGHT / 2)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2,
                        (0, 255, 0),
                        1,
                        2)
            cv2.putText(img, 'Click e to use defaults',
                        (int(CAMWIDTH / 3), int(CAMHEIGHT -100)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        1,
                        2)
        elif not self.hoverCallibrated:
            cv2.putText(img, 'Now hover over the sensor with 3 fingers',
                        (50, int(CAMHEIGHT / 3)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2,
                        (0, 255, 0),
                        1,
                        2)
            cv2.putText(img, 'Callibrating...',
                        (int(CAMWIDTH / 3), int(CAMHEIGHT / 2)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2,
                        (0, 255, 0),
                        1,
                        2)
            cv2.putText(img, 'Click e to use defaults',
                        (int(CAMWIDTH / 3), int(CAMHEIGHT - 100)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        1,
                        2)


touchHandler = TouchHandler()

while True:
    success, frame = cap.read()

    if success:
        frame = cv2.resize(frame, (CAMWIDTH, CAMHEIGHT))
        frame = cv2.flip(frame, 0)
        if cv2.waitKey(25) & 0xFF == ord('e'):
            touchHandler.useDefaultHover(frame)
        frame = touchHandler.process_image(frame)
        touchHandler.callibrationText(frame)
        cv2.imshow(WINDOW_NAME, frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()
