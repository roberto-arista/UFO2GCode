#!/usr/bin/env python3
# coding: utf-8

####################################
# Basic Glyph to gCode translation #
####################################

### Modules
import io
import fontParts.world as fp
from UFO2GCode.gCodePen import GCodePen

if __name__ == '__main__':
    testFont = fp.OpenFont('PlotterTest.ufo')

    glyphPen = GCodePen(testFont)
    testFont['A4'].draw(glyphPen)
    gCode = glyphPen.getCommands()

    with io.open('A4.gcode', mode='w', encoding='utf-8') as gCodeFile:
        gCodeFile.write(gCode)
