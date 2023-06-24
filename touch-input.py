import cv2
import sys
import numpy as np
from numpy.linalg import norm

video_id = 1

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

cap = cv2.VideoCapture('2023-06-19 17-48-27.mkv')
cv2.namedWindow('testwind')


# https://stackoverflow.com/questions/14243472/estimate-brightness-of-an-image-opencv
def brightness(img):
    if len(img.shape) == 3:
        # Colored RGB or BGR (*Do Not* use HSV images with this function)
        # create brightness with euclidean norm
        return np.average(norm(img, axis=2)) / np.sqrt(3)
    else:
        # Grayscale
        return np.average(img)


def process_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        # contours = max(contours, key=lambda x: cv2.contourArea(x))
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000 and area < 10000:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # cv2.drawContours(img, [contours], -1, (255, 255, 0), 2)
        #hull = cv2.convexHull(contours, returnPoints=False)
        #defects = cv2.convexityDefects(contours, hull)
        #if defects is not None:
            #for i in range(defects.shape[0]):
                #s, e, f, d = defects[i, 0]
                #start = tuple(contours[s][0])
                #end = tuple(contours[e][0])
                #far = tuple(contours[f][0])
                #cv2.line(img, start, end, [0, 255, 0], 2)
                #cv2.circle(img, far, 5, [0, 0, 255], -1)

    return thresh


while True:
    success, frame = cap.read()
    if success:
        print(brightness(frame))
        frame = process_image(frame)
        cv2.imshow('testwind', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()
