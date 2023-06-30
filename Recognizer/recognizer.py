# $1 gesture recognizer
import time
from Recognizer.helpers import resample, IndicativeAngle, RotateBy, ScaleTo, TranslateTo
from Recognizer.config import NUMPOINTS, ORIGIN, SQUARESIZE
import math
import numpy as np

ANGLERANGE = np.deg2rad(45.0)
ANGLEPRECISION = np.deg2rad(2.0)
PHI = 0.5 * (-1.0 + math.sqrt(5.0))


def Distance(p1, p2):
    p1x, p1y = p1
    p2x, p2y = p2
    dx = p2x - p1x
    dy = p2y - p1y

    return math.sqrt(dx * dx + dy * dy)


def PathDistance(pts1, pts2):
    d = 0.0
    for i in range(0, len(pts1)):
        d += Distance(pts1[i], pts2[i])
    return d / len(pts1)


def DistanceAtAngle(points, T, radians):
    newpoints = RotateBy(points, radians)
    return PathDistance(newpoints, T["points"])


def DistanceAtBestAngle(points, T, a, b, threshold):
    x1 = PHI * a + (1.0 - PHI) * b
    f1 = DistanceAtAngle(points, T, x1)
    x2 = (1.0 - PHI) * a + PHI * b
    f2 = DistanceAtAngle(points, T, x2)

    while abs(b - a) > threshold:
        if f1 < f2:
            b = x2
            x2 = x1
            f2 = f1
            x1 = PHI * a + (1.0 - PHI) * b
            f1 = DistanceAtAngle(points, T, x1)
        else:
            a = x1
            x1 = x2
            f1 = f2
            x2 = (1.0 - PHI) * a + PHI * b
            f2 = DistanceAtAngle(points, T, x2)

    return min(f1, f2)


class Unistroke:
    def __init__(self, name, points):
        self.name = name
        self.points = resample(points, NUMPOINTS)
        radians = IndicativeAngle(points)
        self.points = RotateBy(self.points, -radians)
        self.points = ScaleTo(self.points, SQUARESIZE)
        self.points = TranslateTo(self.points, ORIGIN)


class Recgonizer:

    def __init__(self, templates, shouldConvert):
        if shouldConvert:
            unistrokes = []
            for template in templates:
                unistroked = Unistroke(template["name"], template["points"])
                unistrokedTemp = {"name": unistroked.name,
                                  "points": unistroked.points}
                unistrokes.append(unistrokedTemp)
            self.templates = unistrokes
        else:
            self.templates = templates
        self.candidate = None

    def recognize(self, points):
        t0 = time.time()
        candidate = Unistroke("", points)
        u = -1
        b = +float('inf')

        for i in range(0, len(self.templates)):
            d = DistanceAtBestAngle(candidate.points, self.templates[i],
                                    -ANGLERANGE, +ANGLERANGE, ANGLEPRECISION)

            if d < b:
                b = d
                u = i

        t1 = time.time()
        if u == -1:
            return "no match", None
        else:
            return self.templates[u]["name"]
