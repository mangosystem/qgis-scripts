"""
/***************************************************************************
Name                 : Polygon To Point
Description          : Polygon To Point
Date                 : 18/Oct/2015
copyright            : (C) 2015 by Minpa Lee
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
##Polygon To Point=name
##Polygon_Layer=vector polygon
##Point_On_Surface=boolean False
##Output=output vector

from qgis.core import *
from processing.tools.vector import VectorWriter
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


polygon_layer = processing.getObject(Polygon_Layer)
provider = polygon_layer.dataProvider()

# write features
writer = VectorWriter(Output, None, provider.fields(), QGis.WKBPoint, polygon_layer.crs())

point_feature = QgsFeature()
features = processing.features(polygon_layer)
total = 100.0 / float(len(features))
current = 0

for feature in features:
    geometry = feature.geometry()
    attributes = feature.attributes()
    
    point = geometry.centroid()
    if Point_On_Surface and not geometry.contains(point):
        point = geometry.pointOnSurface()
    
    if point is None:
        raise GeoAlgorithmExecutionException('Error calculating point')

    point_feature.setGeometry(point)
    point_feature.setAttributes(attributes)
    writer.addFeature(point_feature)
    
    current += 1
    progress.setPercentage(int(current * total))
del writer
