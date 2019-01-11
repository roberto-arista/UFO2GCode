#!/usr/bin/env python3
# coding: utf-8

#####################################
# Visualize conversion with Drawbot #
#####################################

### Modules
import re
from math import atan2, degrees
from fontTools.pens.cocoaPen import CocoaPen
from UFO2GCode.gCodePen import GCodePen
from UFO2GCode.calcFunctions import Point, distance
import fontParts.world as fp

from drawBot import newDrawing, endDrawing, saveImage
from drawBot import newPage, translate, newPath, stroke, strokeWidth
from drawBot import fill, arc, line, drawPath, BezierPath

### Constants
BLACK = (0, 0, 0)
ALTERNATE_COLORS = {
    True: (1, 0, 0),
    False: (0, 0, 1)
}

### Functions & Procedures
def calcAngle(pt1, pt2):
    return atan2((pt2.y - pt1.y), (pt2.x - pt1.x))

def drawGlyph(glyph):
    pen = CocoaPen(glyph.getParent())
    glyph.draw(pen)
    path = pen.path
    glyphPath = BezierPath(path=path)
    drawPath(glyphPath)

def extractValue(flag, cmd):
    pattern = re.compile(f'{flag}' + r"(-{0,1}[0-9]+\.{0,1}[0-9]*)")
    return float(re.search(pattern, cmd).group(1))


### Instructions
if __name__ == '__main__':
    testFont = fp.OpenFont('PlotterTest.ufo')
    testGlyph = testFont['ampersand']

    newDrawing()
    newPage(1200, 1200)
    translate(200, 200)
    strokeWidth(1)

    # reference black glyph
    stroke(*BLACK)
    drawGlyph(testGlyph)

    # glyph drawn from GCode parsing
    pen = GCodePen(testFont)
    testFont['ampersand'].draw(pen)
    gCode = pen.getCommands()

    fill(None)
    strokeWidth(2)

    prevPt = None
    colorSwitch = True
    for cmd in gCode.split('\n'):

        # explicitly to be skipped
        if cmd.startswith('G21') or cmd.startswith('G4') or cmd.startswith('M') or cmd.startswith('G92'):
            continue

        # rapid move
        elif cmd.startswith('G0'):
            thisPt = Point(extractValue('X', cmd), extractValue('Y', cmd))
            prevPt = thisPt

        # straight line
        elif cmd.startswith('G1'):
            thisPt = Point(extractValue('X', cmd), extractValue('Y', cmd))
            stroke(*ALTERNATE_COLORS[colorSwitch])
            line(prevPt, thisPt)
            colorSwitch = not colorSwitch
            prevPt = thisPt

        # clockwise arc
        elif cmd.startswith('G2') or cmd.startswith('G3'):
            stroke(*ALTERNATE_COLORS[colorSwitch])
            endPt = Point(extractValue('X', cmd), extractValue('Y', cmd))
            ii = extractValue('I', cmd)
            jj = extractValue('J', cmd)
            centerPt = Point(prevPt.x + ii, prevPt.y + jj)
            radius = distance(centerPt, endPt)

            if cmd.startswith('G2'):
                isClockwise = True
            else:
                isClockwise = False

            newPath()
            arc(centerPt,
                radius,
                degrees(calcAngle(centerPt, prevPt)),
                degrees(calcAngle(centerPt, endPt)),
                clockwise=isClockwise)
            drawPath()

            colorSwitch = not colorSwitch
            prevPt = endPt

    saveImage('visualizeConversion.pdf')
    endDrawing()
