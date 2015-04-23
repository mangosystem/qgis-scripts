"""
/***************************************************************************
Name                 : Thiessen Polygons
Description          : Thiessen Polygons
Date                 : 23/Apr/2015
copyright            : (C) 2015 by Minpa Lee
email                : mapplus@gmail.com
reference            : processing\algs\qgisVoronoiPolygons.py
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
##[My Scripts]=group
##Thiessen Polygons=name
##Point_Layer=vector point
##Buffer_Region=number 0.00
##Extent=extent
##output=output vector

import math
from sets import Set

from PyQt4.QtCore import *
from qgis.core import *
from processing.tools.vector import VectorWriter
from processing.algs.qgis import voronoi
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException



def clip_voronoi(edges, c, width, height, extent, exX, exY):
    """Clip voronoi function based on code written for Inkscape.
    Copyright (C) 2010 Alvin Penner, penner@vaxxine.com
    """

    def clip_line(x1, y1, x2, y2, w, h, x, y):
        if x1 < 0 - x and x2 < 0 - x:
            return [0, 0, 0, 0]
        if x1 > w + x and x2 > w + x:
            return [0, 0, 0, 0]
        if x1 < 0 - x:
            y1 = (y1 * x2 - y2 * x1) / (x2 - x1)
            x1 = 0 - x
        if x2 < 0 - x:
            y2 = (y1 * x2 - y2 * x1) / (x2 - x1)
            x2 = 0 - x
        if x1 > w + x:
            y1 = y1 + (w + x - x1) * (y2 - y1) / (x2 - x1)
            x1 = w + x
        if x2 > w + x:
            y2 = y1 + (w + x - x1) * (y2 - y1) / (x2 - x1)
            x2 = w + x
        if y1 < 0 - y and y2 < 0 - y:
            return [0, 0, 0, 0]
        if y1 > h + y and y2 > h + y:
            return [0, 0, 0, 0]
        if x1 == x2 and y1 == y2:
            return [0, 0, 0, 0]
        if y1 < 0 - y:
            x1 = (x1 * y2 - x2 * y1) / (y2 - y1)
            y1 = 0 - y
        if y2 < 0 - y:
            x2 = (x1 * y2 - x2 * y1) / (y2 - y1)
            y2 = 0 - y
        if y1 > h + y:
            x1 = x1 + (h + y - y1) * (x2 - x1) / (y2 - y1)
            y1 = h + y
        if y2 > h + y:
            x2 = x1 + (h + y - y1) * (x2 - x1) / (y2 - y1)
            y2 = h + y
        return [x1, y1, x2, y2]

    lines = []
    hasXMin = False
    hasYMin = False
    hasXMax = False
    hasYMax = False
    for edge in edges:
        if edge[1] >= 0 and edge[2] >= 0:
            # Two vertices
            [x1, y1, x2, y2] = clip_line(
                c.vertices[edge[1]][0],
                c.vertices[edge[1]][1],
                c.vertices[edge[2]][0],
                c.vertices[edge[2]][1],
                width,
                height,
                exX,
                exY,
                )
        elif edge[1] >= 0:
            # Only one vertex
            if c.lines[edge[0]][1] == 0:
                # Vertical line
                xtemp = c.lines[edge[0]][2] / c.lines[edge[0]][0]
                if c.vertices[edge[1]][1] > (height + exY) / 2:
                    ytemp = height + exY
                else:
                    ytemp = 0 - exX
            else:
                xtemp = width + exX
                ytemp = (c.lines[edge[0]][2] - (width + exX)
                         * c.lines[edge[0]][0]) / c.lines[edge[0]][1]
            [x1, y1, x2, y2] = clip_line(
                c.vertices[edge[1]][0],
                c.vertices[edge[1]][1],
                xtemp,
                ytemp,
                width,
                height,
                exX,
                exY,
                )
        elif edge[2] >= 0:
            # Only one vertex
            if c.lines[edge[0]][1] == 0:
                # Vertical line
                xtemp = c.lines[edge[0]][2] / c.lines[edge[0]][0]
                if c.vertices[edge[2]][1] > (height + exY) / 2:
                    ytemp = height + exY
                else:
                    ytemp = 0.0 - exY
            else:
                xtemp = 0.0 - exX
                ytemp = c.lines[edge[0]][2] / c.lines[edge[0]][1]
            [x1, y1, x2, y2] = clip_line(
                xtemp,
                ytemp,
                c.vertices[edge[2]][0],
                c.vertices[edge[2]][1],
                width,
                height,
                exX,
                exY,
                )
        if x1 or x2 or y1 or y2:
            lines.append(QgsPoint(x1 + extent.xMinimum(), y1
                         + extent.yMinimum()))
            lines.append(QgsPoint(x2 + extent.xMinimum(), y2
                         + extent.yMinimum()))
            if 0 - exX in (x1, x2):
                hasXMin = True
            if 0 - exY in (y1, y2):
                hasYMin = True
            if height + exY in (y1, y2):
                hasYMax = True
            if width + exX in (x1, x2):
                hasXMax = True
    if hasXMin:
        if hasYMax:
            lines.append(QgsPoint(extent.xMinimum() - exX, height
                         + extent.yMinimum() + exY))
        if hasYMin:
            lines.append(QgsPoint(extent.xMinimum() - exX,
                         extent.yMinimum() - exY))
    if hasXMax:
        if hasYMax:
            lines.append(QgsPoint(width + extent.xMinimum() + exX, height
                         + extent.yMinimum() + exY))
        if hasYMin:
            lines.append(QgsPoint(width + extent.xMinimum() + exX,
                         extent.yMinimum() - exY))
    return lines


# =============================================================================
# 1. prepare variables
# =============================================================================
point_layer = processing.getObject(Point_Layer)
buf = Buffer_Region
extent = point_layer.extent()
if Extent:
    tokens = Extent.split(',')
    extent = QgsRectangle(float(tokens[0]), float(tokens[2]), float(tokens[1]), float(tokens[3]))

writer = VectorWriter(output, None, point_layer.pendingFields(), QGis.WKBPolygon, point_layer.crs())

extraX = extent.height() * (buf / 100.0)
extraY = extent.width() * (buf / 100.0)
height = extent.height()
width = extent.width()
c = voronoi.Context()
pts = []
ptDict = {}
ptNdx = -1

features = processing.features(point_layer)
for feature in features:
    geom = feature.geometry()
    point = geom.asPoint()
    x = point.x() - extent.xMinimum()
    y = point.y() - extent.yMinimum()
    pts.append((x, y))
    ptNdx += 1
    ptDict[ptNdx] = feature.id()

if len(pts) < 3:
    raise GeoAlgorithmExecutionException(
            'Input file should contain at least 3 points. Choose \
            another file and try again.')

uniqueSet = Set(item for item in pts)
ids = [pts.index(item) for item in uniqueSet]
sl = voronoi.SiteList([voronoi.Site(i[0], i[1], sitenum=j) for (j,
                      i) in enumerate(uniqueSet)])
voronoi.voronoi(sl, c)

current = 0
total = 100.0 / float(len(c.polygons))

outFeat = QgsFeature()
for (site, edges) in c.polygons.iteritems():
    request = QgsFeatureRequest().setFilterFid(ptDict[ids[site]])
    feature = point_layer.getFeatures(request).next()
    lines = clip_voronoi(edges, c, width, height, extent, extraX, extraY)

    geom = QgsGeometry.fromMultiPoint(lines)
    geom = QgsGeometry(geom.convexHull())
    outFeat.setGeometry(geom)
    outFeat.setAttributes(feature.attributes())
    writer.addFeature(outFeat)

    current += 1
    progress.setPercentage(int(current * total))
del writer