import cv2
import sys

video_id = 1

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

cap = cv2.VideoCapture(video_id)
cv2.namedWindow('testwind')


def process_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        contours = max(contours, key=lambda x: cv2.contourArea(x))
        for cnt in contours:
            area = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # cv2.drawContours(img, [contours], -1, (255, 255, 0), 2)

    return img


while True:
    success, frame = cap.read()
    if success:
        # frame = process_image(frame)
        cv2.imshow('testwind', frame)
        #height, width, channels = frame.shape
        #out = cv2.VideoWriter('test.mp4', cv2.VideoWriter_fourcc(*'MP4V'), 20.0, (width, height))

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()
