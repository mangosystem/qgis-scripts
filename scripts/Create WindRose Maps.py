"""
/***************************************************************************
Name                 : Create WindRose Maps
Description          : Create WindRose Maps
Date                 : 14/Feb/2014
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
##[My Scripts]=group 
##Input_Point_Layer=vector
##Use_Weight_Field=boolean
##Weight_Field=field Input_Point_Layer
##Center_of_WindRose=selection Layer Extent;Current Extent;Full Extetnt
##Output_layer=output vector
##Output_Anchor=output vector

import os, sys, math
from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import iface
from processing.core.VectorWriter import VectorWriter
from processing.core.ProcessingLog import ProcessingLog
from processing.tools import vector

class StatisticsVisitor:
    def __init__(self):
        self.init()
    
    def init(self):
        self.count = 0
        self.mean = 0
        self.minVal = sys.float_info.max
        self.maxVal = sys.float_info.min
        self.sumOfVals = 0.0
        self.sumOfSqrs = 0.0
        self.variance = 0.0
        self.std_dev = 0.0

    def visit(self, value):
        self.sumOfVals += value;
        self.sumOfSqrs += value * value;

        self.maxVal = max(self.maxVal, value);
        self.minVal = min(self.minVal, value);

        self.count += 1

    def result(self):
        if self.count > 0:
            self.mean = self.sumOfVals / self.count
            self.variance = (self.sumOfSqrs - math.pow(self.sumOfVals, 2.0) / self.count) / self.count;
            self.std_dev = math.sqrt(self.variance)
        
        return [self.count, self.minVal, self.maxVal, self.sumOfVals, self.mean, self.std_dev, self.variance]

# global environment
DEFAULT_SEGS = 32

# create_point
def create_point(centroid, radian, radius):
    dx = math.cos(radian) * radius
    dy = math.sin(radian) * radius
    return QgsPoint(centroid.x() + dx, centroid.y() + dy)

# create_cell
def create_cell(centroid, from_deg, to_deg, radius):
    step = abs(to_deg - from_deg) / DEFAULT_SEGS
    
    outer_ring = []
    outer_ring.append(centroid)
        
    # second outer
    for index in xrange(DEFAULT_SEGS, -1, -1):
        radian = math.radians(from_deg + (index * step))
        outer_ring.append(create_point(centroid, radian, radius))
        
    return QgsGeometry.fromPolygon([outer_ring])

# create_line
def create_line(centroid, degree, radius):    
    outer_ring = []

    outer_ring.append(centroid)
    outer_ring.append(create_point(centroid, math.radians(degree), radius))
        
    return QgsGeometry.fromPolyline(outer_ring)

#. select point layer
input_layer = processing.getobject(Input_Point_Layer)
provider = input_layer.dataProvider()

#. value field , if not provided, feature count will be used
idx_field = -1
if Use_Weight_Field:
    idx_field = provider.fields().indexFromName(Weight_Field)

#. Center : X, Center Y. if not provided, the center of point layer will be used
extent = input_layer.extent()
if Center_of_WindRose == 1:
    extent = iface.mapCanvas().extent()
elif Center_of_WindRose == 2:
    extent = iface.mapCanvas().fullExtent()

center_point = extent.center(); # QgsPoint

minx = extent.xMinimum()
miny = extent.yMinimum()
maxx = extent.xMaximum()
maxy = extent.yMaximum()

radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0

# output fields
cell_fields = QgsFields()
cell_fields.append(QgsField("count", QVariant.Int))

cell_field_list = ["min", "max", "sum", "mean", "std_dev", "var"]
for field_name in cell_field_list:
    cell_fields.append(QgsField(field_name, QVariant.Double))

#. create spatial index
spatial_index = vector.spatialindex(input_layer)

step_angle = 360.0 / DEFAULT_SEGS
half_step = step_angle / 2.0

minVal = sys.float_info.max
maxVal = sys.float_info.min
centroid_features = {}
for idx_side in xrange(DEFAULT_SEGS):
    from_deg = (idx_side * step_angle) - half_step
    to_deg = ((idx_side + 1) * step_angle) - half_step
    progress.setPercentage(int(100 * idx_side / DEFAULT_SEGS))

    cell = create_cell(center_point, from_deg, to_deg, radius)

    # sptial query
    hasIntersections = False
    points = spatial_index.intersects(cell.boundingBox())
    if len(points) > 0:
        hasIntersections = True

    visitor = StatisticsVisitor()
    if hasIntersections:
        for fid in points:
            request = QgsFeatureRequest().setFilterFid(fid)
            point_feature = input_layer.getFeatures(request).next()
            if cell.contains(point_feature.geometry()):
                if idx_field >= 0 :
                    weight = str(point_feature.attributes()[idx_field])
                    try:
                        visitor.visit(float(weight))
                    except:
                        # Ignore fields with non-numeric values
                        pass
                else:
                    visitor.visit(1)

    # create and write ring feature
    cell_feature = QgsFeature(cell_fields)
    cell_feature.setGeometry(cell)
    ret = visitor.result()
    minVal = min(minVal, ret[3]);
    maxVal = max(maxVal, ret[3]);
    cell_feature.setAttributes(ret)
    centroid_features[idx_side] = cell_feature

#. write features
cell_writer = VectorWriter(Output_layer, None, cell_fields, QGis.WKBPolygon, input_layer.crs())
for idx_side in xrange(DEFAULT_SEGS):
    cell_feature = centroid_features[idx_side]
    value = cell_feature.attributes()[3]
    linear_trans_value = (value - minVal) / (maxVal - minVal);
    adjusted_radius = linear_trans_value * radius
    if adjusted_radius > 0:
        from_deg = (idx_side * step_angle) - half_step
        to_deg = ((idx_side + 1) * step_angle) - half_step
        cell = create_cell(center_point, from_deg, to_deg, adjusted_radius)
        cell_feature.setGeometry(cell)
        cell_writer.addFeature(cell_feature)

del cell_writer

#. write anchor      
cell_fields = QgsFields()
cell_fields.append(QgsField("distance", QVariant.Double))
cell_fields.append(QgsField("direction", QVariant.String))
anchor_writer = VectorWriter(Output_Anchor, None, cell_fields, QGis.WKBLineString, input_layer.crs())

radius_step = radius / 5
center =  QgsGeometry.fromPoint(center_point)
for idx_side in xrange(5):
    buffer_radius = radius_step * (idx_side + 1)
    anchor_feature = QgsFeature(cell_fields)
    anchor_feature.setGeometry(center.buffer(buffer_radius, 32))
    anchor_feature.setAttributes([buffer_radius, None])
    anchor_writer.addFeature(anchor_feature)

north = ['E', 'ENE', 'NE', 'NNE', 'N', 'NNW', 'NW', 'WNW', 'W',  'WSW', 'SW', 'SSW', 'S', 'SSE', 'SE', 'ESE']
for idx_side in range(16):
    degree = 22.5 * idx_side
    anchor_line = create_line(center_point, degree, radius)
    anchor_feature = QgsFeature(cell_fields)
    anchor_feature.setGeometry(anchor_line)
    anchor_feature.setAttributes([None, north[idx_side]])
    anchor_writer.addFeature(anchor_feature)

del anchor_writer
