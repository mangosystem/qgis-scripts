"""
/***************************************************************************
Name                 : Calculate Point Attribute From Polygon Features
Description          : Calculate Point Attribute From Polygon Features
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
##Calculate Point Attribute From Polygon Features=name
##Point_Layer=vector point
##Target_Fields=string pnu
##Polygon_Layer=vector polygon
##Source_Fields=string pnu
##Result=output string

from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from processing.tools import dataobjects, vector
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


# =============================================================================
# main
# =============================================================================
point_layer   = processing.getObject(Point_Layer)
polygon_layer = processing.getObject(Polygon_Layer)

# prepare fields
target_fields = Target_Fields.strip().split(',')
source_fields = Source_Fields.strip().split(',')
if len(target_fields) != len(source_fields):
    raise GeoAlgorithmExecutionException('Target and Source Fields must be same count!')

field_index = {}  # {target, source}
for idx in xrange(len(target_fields)):
    idx_target = point_layer.fieldNameIndex(target_fields[idx].strip())
    idx_source = polygon_layer.fieldNameIndex(source_fields[idx].strip())
    if idx_target == -1 or idx_source == -1:
        raise GeoAlgorithmExecutionException('target or source field does not exist!')
    field_index[idx_target] = idx_source
    
# create spatial index of polygon layer
spatial_index = QgsSpatialIndex()
polygon_features = processing.features(polygon_layer)
for feature in polygon_features:
    spatial_index.insertFeature(feature)
    
# =============================================================================
# point in polygon
# =============================================================================
point_features = processing.features(point_layer)
point_count = len(point_features)
current = 1
point_layer.startEditing()
for point_feature in point_features:
    progress.setPercentage(int(100 * current / point_count))
    current += 1
    
    id = int(point_feature.id())
    point = point_feature.geometry()
    
    polygon_feature = None
    fids = spatial_index.intersects(point.boundingBox())
    for fid in fids:
        request = QgsFeatureRequest().setFilterFid(int(fid))
        feature = polygon_layer.getFeatures(request).next()
        polygon = feature.geometry()
        if polygon.intersects(point):
            polygon_feature = feature
            break
            
    if polygon_feature:
      for idx_target in field_index.keys():
          value = None
          if polygon_feature:
              value = polygon_feature[field_index[idx_target]]
          point_layer.changeAttributeValue(id, idx_target, value)
point_layer.commitChanges()
Result = str(current)
