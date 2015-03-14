"""
/***************************************************************************
Name                 : Create Ring Maps
Description          : Create Ring Maps
Date                 : 31/Dec/2013
copyright            : (C) 2013 by Minpa Lee
email                : mapplus@gmail.com
reference:
    http://gis.stackexchange.com/questions/6682/how-to-implement-ringmaps-in-arcgis
    http://www.esri.com/esri-news/arcuser/fall-2013/looking-at-temporal-changes
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
##Create Ring Maps=name
##Input_Vector_Layer=vector
##Comma_separated__fields_or_Ring_number=string a3_2000, a3_2001, a3_2002, a3_2003, a3_2004, a3_2005
##Output_Ring_Value_Field=string ring_val
##Ring_Gap=number 1
##Output_ring_anchor=output vector
##Output_ring_maps=output vector

from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from processing.tools.vector import VectorWriter
import math

# global environment
DEFAULT_SEGS = 10
GAPS = Ring_Gap
if (GAPS >= DEFAULT_SEGS):
    raise ValueError('Ring_Gap must be smaller than %s' % DEFAULT_SEGS)

# lambda functions
# math.radians(x)
to_radian = lambda degree: math.pi / 180.0 * degree
# math.degrees(x)
to_degree = lambda radian: radian * (180.0 / math.pi)

# is_number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# create_point
def create_point(centroid, radian, radius):
    dx = math.cos(radian) * radius
    dy = math.sin(radian) * radius
    return QgsPoint(centroid.x() + dx, centroid.y() + dy)

# calculate_layer_extent
def calculate_layer_extent(input_layer):
    extent = QgsRectangle()
    
    features = input_layer.getFeatures()
    for feature in features:
        geometry = feature.geometry()
        if extent.isEmpty() :
            extent = geometry.boundingBox()
        else:
            extent.unionRect(geometry.boundingBox())
            
    if extent.isEmpty() :
        extent = input_layer.extent()
        
    return extent

# create_ring_cell
def create_ring_cell(centroid, from_deg, to_deg, from_radius, to_radius):
    step = abs(to_deg - from_deg) / DEFAULT_SEGS
    radian = 0.0
    
    outer_ring = []
    
    # first interior
    for index in xrange(DEFAULT_SEGS  + 1 - GAPS):
        radian = to_radian(from_deg + (index * step))
        outer_ring.append(create_point(centroid, radian, from_radius))
    
    # second outer
    for index in xrange(DEFAULT_SEGS - GAPS, -1, -1):
        radian = to_radian(from_deg + (index * step))
        outer_ring.append(create_point(centroid, radian, to_radius))
        
    return QgsGeometry.fromPolygon([outer_ring])

# create_spatial_index
def create_spatial_index(input_layer):
    spatial_index = QgsSpatialIndex()
    
    # features dictionary
    centroid_features = {}
    
    features = input_layer.dataProvider().getFeatures()
    for feature in features:
        # convert to point feature
        point_feature = QgsFeature(input_layer.dataProvider().fields())
        point_feature.setFeatureId(feature.id())
        point_feature.setAttributes(feature.attributes())
        point_feature.setGeometry(feature.geometry().centroid())
        centroid_features[point_feature.id()] = point_feature
        
        spatial_index.insertFeature(point_feature)
    
    return (spatial_index, centroid_features)


#===============================================================
# run algorithm
#===============================================================
input_layer = processing.getObject(Input_Vector_Layer)

# Comma_separated__fields_or_Ring_number
ring_num = 0
use_ring_count = False;

if (is_number(Comma_separated__fields_or_Ring_number)):
    ring_num = int(Comma_separated__fields_or_Ring_number)
    use_ring_count = True
else:
    input_fields = Comma_separated__fields_or_Ring_number.strip().split(',')
    ring_num = len(input_fields)
    for idx in xrange(ring_num):
        input_fields[idx] = input_fields[idx].strip()
if (ring_num == 0):
    raise ValueError('Ring number must be greater than zero')

# calculate layer's extent & feature count
extent = calculate_layer_extent(input_layer) # input_layer.extent()
feature_count = input_layer.featureCount()

# create spatial index & convert to points
(spatial_index, centroid_features) = create_spatial_index(input_layer)

center_point = extent.center(); # QgsPoint

minx = extent.xMinimum()
miny = extent.yMinimum()
maxx = extent.xMaximum()
maxy = extent.yMaximum()

radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0
radius_interval = radius / ring_num

# Output_Ring_Value_Field
provider = input_layer.dataProvider()
ring_fields = provider.fields()
ring_fields.append(QgsField("ring_num", QVariant.Int))
ring_fields.append(QgsField(Output_Ring_Value_Field, QVariant.Double))

idx_fields = []
for idx in xrange(ring_num):
    if (use_ring_count):
        idx_fields.append(-1)
    else:
        idx_fields.append(ring_fields.indexFromName(input_fields[idx]))

# create vector writer
ring_writer = VectorWriter(Output_ring_maps, None, ring_fields, QGis.WKBPolygon, input_layer.crs())
anchor_writer = VectorWriter(Output_ring_anchor, None, provider.fields(), QGis.WKBLineString, input_layer.crs())

step_angle = 360.0 / feature_count
half_step = step_angle / 2.0

for idx_side in xrange(feature_count):
    from_deg = half_step + (idx_side * step_angle)
    to_deg = half_step + ((idx_side + 1) * step_angle)
    default_radius = radius
    progress.setPercentage(int(100 * idx_side / feature_count))
    
    for idx_radius in xrange(ring_num):
        cell = create_ring_cell(center_point, from_deg, to_deg, default_radius,  default_radius + radius_interval)
        cell_centroid_point = cell.centroid().asPoint()
        
        # find nearest feature & create anchor line
        if (idx_radius == 0):
            fids = spatial_index.nearestNeighbor(cell_centroid_point, 1)
            for fid in fids:
                nearest_feature = centroid_features[fid]
                nearest_point = nearest_feature.geometry().asPoint()
                
                anchor_feature = QgsFeature()
                anchor_feature.setGeometry(QgsGeometry.fromPolyline([nearest_point, cell_centroid_point]))
                anchor_feature.setAttributes(nearest_feature.attributes())
                anchor_writer.addFeature(anchor_feature)
                
                spatial_index.deleteFeature(nearest_feature)
        
        # create and write ring feature
        ring_feature = QgsFeature(ring_fields)
        ring_feature.setGeometry(cell)
        
        ring_attributes = nearest_feature.attributes()
        ring_attributes.append(idx_radius + 1)                           # ring_num
        if (idx_fields[idx_radius] == -1):
            ring_attributes.append(0)  # default value = 0
        else:
            ring_attributes.append(ring_attributes[idx_fields[idx_radius]])  # ring_val
        ring_feature.setAttributes(ring_attributes)
        ring_writer.addFeature(ring_feature)
        
        default_radius += radius_interval

# cleanup
del ring_writer
del anchor_writer
del centroid_features