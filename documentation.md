# Documentation

## Design decisions

To detect hands on the touch sensor, a threshold-based approach was used, since it seemed like the most efficient method and can also be easily callibrated while leading to good results.
A simple threshold and blur is used to first find the contours of the hand. After that, only contours with a specific size (finger) are taken into account and then included in the event-message. To differentiate hovering and touching gestures, the idea was to use two different thresholds, since hovering is less easy to detect, so a harder threshold is used for it.
When both thresholds find a contour a the same spot, it is then detected only as a hover-input to avoid duplicate events.

## Building process

To easily place the camera directly in the center, a hole was drilled into the side of the box to lay out the cable. The camera itself was then tapped to the bottom of the box, as the holding-surface of the camera is flat and can be taped on the ground while being relatively stable.

## Usage guide

1. Place the acryl-glass and a centered piece of paper on top of it on the box. Make sure that the end of the cable is not inside the box beforehand.
2. Turn the box, so that you face it with the cable going out in the upper left side in front of you.
3. Plug in the usb-cable
4. Run the touch-input.py File
5. Callibration:
   1. First, you should put 3 fingers on the paper. When the callibration is finished a countdown will start
   2. A) When the countdown is finished, you should hover over the paper with 3 fingers. <br/>
    B) Alternatively, in the hover-callibration step, if for example the text doesn't disappear, you can use the key 'e' to stop the callibration and use a default value for the hover. This is the case, because when testing, under certain lightning conditions, the callibration for the hover will take very long or won't work at all.
   3. When the text disappear, the program is callibrated and can be used.
   
