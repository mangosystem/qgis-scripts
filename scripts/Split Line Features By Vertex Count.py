"""
/***************************************************************************
Name                 : Split Line Features By Vertex Count
Description          : Split Line Features By Vertex Count
Date                 : 08/Oct/2014
copyright            : (C) 2014 by Minpa Lee
email                : mapplus@gmail.com
reference:
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
##[GEEPS]=group
##Split Line Features By Vertex Count=name
##Line_Layer=vector line
##Vertex_Count=number 25
##output=output vector

import math
from qgis.core import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


# from MultipartToSingleparts.py
def extractAsSingle(geom):
    multiGeom = QgsGeometry()
    geometries = []
    if geom.type() == QGis.Point:
        if geom.isMultipart():
            multiGeom = geom.asMultiPoint()
            for part in multiGeom:
                geometries.append(QgsGeometry().fromPoint(part))
        else:
            geometries.append(geom)
    elif geom.type() == QGis.Line:
        if geom.isMultipart():
            multiGeom = geom.asMultiPolyline()
            for part in multiGeom:
                geometries.append(QgsGeometry().fromPolyline(part))
        else:
            geometries.append(geom)
    elif geom.type() == QGis.Polygon:
        if geom.isMultipart():
            multiGeom = geom.asMultiPolygon()
            for part in multiGeom:
                geometries.append(QgsGeometry().fromPolygon(part))
        else:
            geometries.append(geom)
    return geometries


def split_line_by_vertex(linestring, count):
    geometries = []
    points = linestring.asPolyline()
    point_count = len(points)
    if count >= point_count:
        geometries.append(linestring)
    else:
        # static QgsGeometry * 	fromPolyline (const QgsPolyline &polyline)
        quotient  = point_count / count
        remainder = point_count % count
        for idx in range(quotient):
            start = 0 if idx == 0 else (idx*count)-1
            if remainder == 1 and quotient == (idx+1):
                # if remainder = 1, cannot build line
                end = point_count
            else:
                end = (idx+1)*count
            geometries.append(QgsGeometry.fromPolyline(points[start:end]))
        
        if remainder > 1:
            geometries.append(QgsGeometry.fromPolyline(points[(quotient*count)-1:len(points)]))
    return geometries

# main
if Vertex_Count < 2: 
    raise GeoAlgorithmExecutionException("The number of vertices must be more than 2.")
    
lineLayer = processing.getObject(Line_Layer)
provider = lineLayer.dataProvider()
if not provider.geometryType() in (QGis.WKBLineString, QGis.WKBMultiLineString, QGis.WKBMultiLineString25D, QGis.WKBLineString25D):
    raise GeoAlgorithmExecutionException("Select line features layer!")
    
writer = VectorWriter(output, None, provider.fields(), QGis.WKBLineString, lineLayer.crs())

current = 0
output_feature = QgsFeature()
line_features = processing.features(lineLayer)
total = 100.0 / float(len(line_features))
for feature in line_features:
    current += 1
    progress.setPercentage(int(current * total))
    
    # first convert to single geometry
    geometries = extractAsSingle(feature.geometry())
    for geometry in geometries:
        # split lines
        linestrings = split_line_by_vertex(geometry, int(Vertex_Count))
        # insert features
        output_feature.setAttributes(feature.attributes())
        for linestring in linestrings:
            output_feature.setGeometry(linestring)
            writer.addFeature(output_feature)

del writer
