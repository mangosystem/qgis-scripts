"""
/***************************************************************************
Name                 : Calculate Nearest Neighbor Index
Description          : Calculate Nearest Neighbor Index
Date                 : 20/March/2015
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
##Calculate Nearest Neighbor Index=name
##Polygon_Layer=vector polygon
##Point_Layer=vector point
##Output_Layer=output vector

import sys, math
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from processing.tools.vector import VectorWriter


# =============================================================================
# get minimum distance from point features
# =============================================================================
def get_minimum_distance(point_features, source):
    min_distance = sys.float_info.max
    for dest in point_features:
        if source.id() == dest.id():
            continue
        min_distance = min(min_distance, source.geometry().distance(dest.geometry()))
        if min_distance == 0:
            return min_distance
    return min_distance


# =============================================================================
# prepare required field
# =============================================================================
point_layer = processing.getObject(Point_Layer)

polygon_layer = processing.getObject(Polygon_Layer)
output_fields = polygon_layer.dataProvider().fields()
output_fields.append(QgsField('point_cnt', QVariant.Int))
output_fields.append(QgsField('area', QVariant.Double))
output_fields.append(QgsField('obsavgdist', QVariant.Double))
output_fields.append(QgsField('expavgdist', QVariant.Double))
output_fields.append(QgsField('nni', QVariant.Double))
output_fields.append(QgsField('zscore', QVariant.Double))
output_fields.append(QgsField('stderr', QVariant.Double))

# =============================================================================
# calculate nearest neighbor index
# =============================================================================
writer = VectorWriter(Output_Layer, None, output_fields, QGis.WKBPolygon, polygon_layer.crs())
polygon_features = processing.features(polygon_layer)
polygon_count = len(polygon_features)
step = 1
for polygon_feature in polygon_features:
    progress.setPercentage(int(100 * step / polygon_count))
    step += 1
    polygon_geom = polygon_feature.geometry()
    
    # search intersected point features
    intersects_points = []
    request = QgsFeatureRequest().setFilterRect(polygon_geom.boundingBox())
    point_features = point_layer.getFeatures(request)
    for point_feature in point_features:
        if polygon_geom.intersects(point_feature.geometry()):
            intersects_points.append(point_feature)
    
    # calculate nearest distance & nearest neighbor index
    sum_nearest_dist = 0.0;
    for point_feature in intersects_points:
        min_distance = get_minimum_distance(intersects_points, point_feature)
        sum_nearest_dist += min_distance;
        
    area = polygon_geom.area()
    N = len(intersects_points)
    observed_mean_dist = sum_nearest_dist / float(N);
    expected_mean_dist = 0.5 * math.sqrt(area / float(N));
    nearest_neighbor_index = observed_mean_dist / expected_mean_dist;
    standard_error = math.sqrt(((4.0 - math.pi) * area) / (4.0 * math.pi * N * N));
    z_score = (observed_mean_dist - expected_mean_dist) / standard_error;
    del intersects_points
    
    # create feature
    new_feature = QgsFeature(output_fields)
    new_feature.setGeometry(polygon_geom)
    for idx, val in enumerate(polygon_feature.attributes()):
        new_feature.setAttribute(idx, val)
    
    # set attributes
    new_feature.setAttribute('point_cnt', N)
    new_feature.setAttribute('area', area)
    new_feature.setAttribute('obsavgdist', observed_mean_dist)
    new_feature.setAttribute('expavgdist', expected_mean_dist)
    new_feature.setAttribute('nni', nearest_neighbor_index)
    new_feature.setAttribute('zscore', z_score)
    new_feature.setAttribute('stderr', standard_error)
    
    writer.addFeature(new_feature)
del writer
