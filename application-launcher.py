import subprocess
from pynput.mouse import Listener, Button

# array of application paths
applications = []

# https://stackoverflow.com/questions/3277503/how-to-read-a-file-line-by-line-into-a-list
with open('applications.txt') as f:
    while line := f.readline():
        applications.append((line.rstrip()))

# save inputs
inputs = []


# onClick callback for pynput listener
def on_click(x, y, button, pressed):
    global inputs

    if button == Button.left:
        if pressed:
            inputs.append(0)
        else:
            inputs.append(1)
    elif button == Button.right:
        if pressed:
            inputs.append(2)
        else:
            inputs.append(3)

    if len(inputs) == 8:
        if inputs == [0, 1, 2, 3, 0, 1, 2, 3]:
            subprocess.call([applications[0]])
        elif inputs == [0, 1, 0, 1, 2, 3, 0, 1]:
            subprocess.call([applications[1]])
        elif inputs == [2, 3, 2, 3, 2, 3, 0, 1]:
            subprocess.call([applications[2]])

        inputs = []
    pass


# init the listener
with Listener(on_click=on_click) as listener:
    listener.join()
