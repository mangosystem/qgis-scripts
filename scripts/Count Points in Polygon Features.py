"""
/***************************************************************************
Name                 : Count Points in Polygon Features
Description          : Count Points in Polygon Features
Date                 : 25/March/2015
copyright            : (C) 2015 by Minpa Lee, Mango System inc.
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
##[KOCER]=group
##Count Points in Polygon Features=name
##Polygon_Layer=vector polygon
##Polygon_Count_Field=field Polygon_Layer
##Point_Layer=vector point
##Point_Filter_Expresesion=string
##Result=output string

from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from processing.tools import dataobjects, vector
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


# =============================================================================
# main
# =============================================================================
polygon_layer = processing.getObject(Polygon_Layer)
count_field = polygon_layer.fieldNameIndex(Polygon_Count_Field)

point_layer = processing.getObject(Point_Layer)

expression = QgsExpression('1=1')
if len(Point_Filter_Expresesion.strip()) > 0:
    expression = QgsExpression(Point_Filter_Expresesion)
expression.prepare(point_layer.pendingFields())

# =============================================================================
# count point in polygon
# =============================================================================
polygon_features = processing.features(polygon_layer)
polygon_count = len(polygon_features)
current = 1
polygon_layer.startEditing()
for polygon_feature in polygon_features:
    progress.setPercentage(int(100 * current / polygon_count))
    current += 1
    polygon = polygon_feature.geometry()
    fid = int(polygon_feature.id())
    
    point_count = 0
    request = QgsFeatureRequest().setFilterRect(polygon.boundingBox())
    point_features = point_layer.getFeatures(request)
    for point_feature in point_features:
        if polygon.intersects(point_feature.geometry()):
            if bool(expression.evaluate(point_feature)):
                point_count += 1
    polygon_layer.changeAttributeValue(fid, count_field, point_count)
polygon_layer.commitChanges()
Result = str(current)
