#!/usr/bin/env python3
# coding: utf-8

###############################
# Robofont > GCode translator #
###############################

### Modules
from math import cos, sin
from fontTools.pens.basePen import BasePen
from UFO2GCode.calcFunctions import convertCurveToArcs, Point, isClockwise

### Constants
RAPID_MOVE = 'G0'
DRAWING_MOVE = 'G1'

LIFT_PEN = 'M03 S0'

### Functions & Procedures
def dropPen(start, end, step):
    dropCommands = []
    for ii in range(start, end, step):
        dropCommands.append(f'M03 S{ii}')
        dropCommands.append('G4 P0.0005')
    return dropCommands

class GCodePen(BasePen):

    def __init__(self, glyphSet,
                 freeMoveFeed, drawingFeed):

        BasePen.__init__(self, glyphSet)

        self.freeMoveFeed = freeMoveFeed
        self.drawingFeed  = drawingFeed

        self._commands = [
            'G21',         # set units to mm
            'M03 S0',      # lift the pen
            # 'G92 X0 Y0'    # set the relative zero
        ]
        self.lastPt = None

    def _moveTo(self, pt):
        self._commands.append('; _moveTo()')
        self.firstPt = Point(*pt)
        cmd = [f'{RAPID_MOVE}',
               f'X{self.firstPt.x:.4f}',
               f'Y{self.firstPt.y:.4f}',
               f'F{self.freeMoveFeed}']
        self._commands.append(' '.join(cmd))
        self._commands.extend(dropPen(10, 90, 10))
        self.lastPt = self.firstPt

    def _lineTo(self, pt):
        self._commands.append('; _lineTo()')
        linePt = Point(*pt)
        cmd = [f'{DRAWING_MOVE}',
               f'X{linePt.x:.4f}',
               f'Y{linePt.y:.4f}',
               f'F{self.drawingFeed}']
        self._commands.append(' '.join(cmd))
        self.lastPt = linePt

    def _curveToOne(self, pt1, pt2, pt3):
        self._commands.append('; _curveToOne()')
        cmds = []
        arcs = convertCurveToArcs(self.lastPt,
                                  Point(*pt1),
                                  Point(*pt2),
                                  Point(*pt3))
        for eachArc in arcs:
            center, startAngle, endAngle, radius, _ = eachArc

            arcStart = Point(
                center.x+cos(startAngle)*radius,
                center.y+sin(startAngle)*radius)

            arcEnd = Point(
                center.x+cos(endAngle)*radius,
                center.y+sin(endAngle)*radius)

            if isClockwise(center, arcStart, arcEnd) is True:
                # G2 Xnnn Ynnn Innn Jnnn Ennn Fnnn (Clockwise Arc)
                drawingCommand = 'G2'
            else:
                # G3 Xnnn Ynnn Innn Jnnn Ennn Fnnn (Counter-Clockwise Arc)
                drawingCommand = 'G3'

            # from https://www.instructables.com/id/How-to-program-arcs-and-linear-movement-in-G-Code-/
            thisCmd = [
                f'{drawingCommand}',
                f'X{arcEnd.x:.4f}',
                f'Y{arcEnd.y:.4f}',
                f'I{(center.x-cos(startAngle)*radius)-center.x:.4f}',
                f'J{(center.y-sin(startAngle)*radius)-center.y:.4f}',
                f'F{self.drawingFeed}']
            cmds.append(' '.join(thisCmd))

        self._commands.append('\n'.join(cmds))
        self.lastPt = Point(*pt3)

    def _closePath(self):
        self._commands.append('; _closePath()')
        if self.firstPt != self.lastPt:
            cmd = [f'{DRAWING_MOVE}',
                   f'X{self.firstPt.x:.4f}',
                   f'Y{self.firstPt.y:.4f}',
                   f'F{self.drawingFeed}']
            self._commands.append(' '.join(cmd))
        self._commands.append(LIFT_PEN)

    def _endPath(self):
        self._commands.append('; _endPath()')
        self._commands.append(LIFT_PEN)

    def getCommands(self):
        # back to origin point
        cmd = [f'{RAPID_MOVE}', 'X0 Y0', f'F{self.freeMoveFeed}']
        self._commands.append(' '.join(cmd))
        return '\n'.join(self._commands)
