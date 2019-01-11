#!/usr/bin/env python3
# coding: utf-8

########################
# gCode calc functions #
########################

"""Theory (and quite some code) behind the bezier 2 arc approximation
   comes from https://pomax.github.io/bezierinfo/#arcapproximation"""

### Modules
from collections import namedtuple
from fontTools.misc.bezierTools import calcCubicParameters
from math import cos, sin, atan2, pi, sqrt

### Constants
Point = namedtuple('Point', ['x', 'y'])
ERROR_THRESHOLD = .05

### Functions & Procedures
def distance(p1, p2):
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return sqrt(dx**2 + dy**2)

def lli8(x1, y1, x2, y2, x3, y3, x4, y4):
    nx = (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4)
    ny = (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4)
    d = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    if d == 0:
        return False
    return Point(nx/d, ny/d)

def getCCenter(p1, p2, p3):
    # deltas
    dx1 = (p2.x - p1.x)
    dy1 = (p2.y - p1.y)
    dx2 = (p3.x - p2.x)
    dy2 = (p3.y - p2.y)

    # perpendiculars (quarter circle turned)
    dx1p = dx1 * cos(pi/2) - dy1 * sin(pi/2)
    dy1p = dx1 * sin(pi/2) + dy1 * cos(pi/2)
    dx2p = dx2 * cos(pi/2) - dy2 * sin(pi/2)
    dy2p = dx2 * sin(pi/2) + dy2 * cos(pi/2)

    # chord midpoints
    mx1 = (p1.x + p2.x)/2
    my1 = (p1.y + p2.y)/2
    mx2 = (p2.x + p3.x)/2
    my2 = (p2.y + p3.y)/2

    # midpoint offsets
    mx1n = mx1 + dx1p
    my1n = my1 + dy1p
    mx2n = mx2 + dx2p
    my2n = my2 + dy2p

    # intersection of these lines:
    center = lli8(mx1, my1, mx1n, my1n, mx2, my2, mx2n, my2n)
    radius = distance(center, p1)

    # arc start/end values, over mid point
    start = atan2(p1.y - center.y, p1.x - center.x)
    end = atan2(p3.y - center.y, p3.x - center.x)

    return center, start, end, radius

def calcPointOnBezier(aa, bb, cc, dd, tValue):
    ax, ay = aa
    bx, by = bb
    cx, cy = cc
    dx, dy = dd
    return Point(ax*tValue**3 + bx*tValue**2 + cx*tValue + dx,
                 ay*tValue**3 + by*tValue**2 + cy*tValue + dy)

def isGoodArc(center, radius, belowMidPt, aboveMidPt):
    radiusBelowMid = distance(center, belowMidPt)
    radiusAboveMid = distance(center, aboveMidPt)

    errorBelow = abs(radius - radiusBelowMid)
    errorAbove = abs(radius - radiusAboveMid)

    if errorBelow > ERROR_THRESHOLD:
        return False, (errorBelow, errorAbove)

    if errorAbove > ERROR_THRESHOLD:
        return False, (errorBelow, errorAbove)

    # inferior than error threshold
    return True, (errorBelow, errorAbove)

def lerp(a, b, factor):
    return a + (b - a) * factor

def binaryArcApprox(pt1, pt2, pt3, pt4, startT, endT, prevStatus=False):
    assert endT <= 1, f'startT {startT}, endT {endT}'

    """ as soon as isGoodArc() returns True and then False,
    we stop and pick the True arc :) """

    midT = lerp(startT, endT, .5)

    # curve parameters
    aa, bb, cc, dd = calcCubicParameters((pt1.x, pt1.y),
                                         (pt2.x, pt2.y),
                                         (pt3.x, pt3.y),
                                         (pt4.x, pt4.y))

    # hypothetical arc points
    startPt = calcPointOnBezier(aa, bb, cc, dd, startT)
    midPt = calcPointOnBezier(aa, bb, cc, dd, midT)
    endPt = calcPointOnBezier(aa, bb, cc, dd, endT)

    # test points
    belowT = startT+(endT-startT)*.25
    belowMidPt = calcPointOnBezier(aa, bb, cc, dd, belowT)

    aboveT = startT+(endT-startT)*.75
    aboveMidPt = calcPointOnBezier(aa, bb, cc, dd, aboveT)

    center, startAngle, endAngle, radius = getCCenter(startPt, midPt, endPt)
    arcStatus, errors = isGoodArc(center, radius, belowMidPt, aboveMidPt)

    if arcStatus is True:
        if endT == 1:    # the curve is finished, it is time to stop recursion
            return center, startAngle, endAngle, radius, endT
        else:
            # to the top!
            return binaryArcApprox(pt1, pt2, pt3, pt4,
                                   startT, endT+(endT-startT)*.25, arcStatus)
    else:
        # to the bottom!
        if prevStatus is True:
            return center, startAngle, endAngle, radius, endT

        else:
            return binaryArcApprox(pt1, pt2, pt3, pt4,
                                   startT, midT, arcStatus)

def isClockwise(centerPt, startPt, endPt):
    """assuming smaller arc"""
    # from https://math.stackexchange.com/questions/1525961/determine-direction-of-an-arc-cw-ccw
    c = (startPt.x - centerPt.x) * (endPt.y - centerPt.y) - (startPt.y - centerPt.y) * (endPt.x - centerPt.x)
    if c == 0:
        # points are aligned!
        return None
    elif c > 0:
        return False
    else:
        return True

def convertCurveToArcs(pt1, pt2, pt3, pt4):
    aa, bb, cc, dd = calcCubicParameters((pt1.x, pt1.y),
                                         (pt2.x, pt2.y),
                                         (pt3.x, pt3.y),
                                         (pt4.x, pt4.y))

    startT = 0
    endT = 1
    arcs = []
    while startT != 1:
        center, startAngle, endAngle, radius, approxT = binaryArcApprox(pt1, pt2, pt3, pt4,
                                                                        startT, endT)
        startT = approxT
        arcs.append((center, startAngle, endAngle, radius, endT))
    return arcs
