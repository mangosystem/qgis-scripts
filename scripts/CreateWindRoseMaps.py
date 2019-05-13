# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Create WindRose Maps
Description          : Create WindRose Maps
Date                 : 10/May/2019
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

from PyQt5.QtCore import (QCoreApplication,
                          QVariant)
from qgis.utils import (iface)
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsFeatureRequest,
                       QgsFeatureSink,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes,
                       QgsProject,
                       QgsCoordinateTransform,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterField,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsSpatialIndex)

import processing
import math, sys


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


class CreateWindRoseMapsAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    USE_WEIGHT_FIELD = 'USE_WEIGHT_FIELD'
    WEIGHT_FIELD = 'WEIGHT_FIELD'
    CENTER = 'CENTER'

    OUTPUT = 'OUTPUT'
    OUTPUT_ANCHOR = 'OUTPUT_ANCHOR'

    EXTENTS = ['Layer Extent', 'Current Extent', 'Full Extetnt']
    DEFAULT_SEGS = 32

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreateWindRoseMapsAlgorithm()

    def name(self):
        return 'CreateWindRoseMapsAlgorithm'.lower()

    def displayName(self):
        return self.tr('Create WindRose Maps')

    def group(self):
        return self.tr('MangoSystem')

    def groupId(self):
        return 'mangoscripts'

    def shortHelpString(self):
        return self.tr('Create thiessen polygons from points.')

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Input Point Layer'),
                                                           [QgsProcessing.TypeVectorPoint]))

        self.addParameter(QgsProcessingParameterBoolean(self.USE_WEIGHT_FIELD, self.tr('Use Weight Field'), False, optional=True))
        self.addParameter(QgsProcessingParameterField(self.WEIGHT_FIELD, self.tr('Weight Field'),
                                                      type=QgsProcessingParameterField.Numeric,
                                                      parentLayerParameterName=self.INPUT, optional=True))

        self.addParameter(QgsProcessingParameterEnum(self.CENTER, self.tr('Center of WindRose'),
                                                     self.EXTENTS, 0, optional=True))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('WindRoseMap'), QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_ANCHOR, self.tr('Anchor'), QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        use_weight_field = self.parameterAsBool(parameters, self.USE_WEIGHT_FIELD, context)
        idx_field = -1
        if use_weight_field:
            weight_field = self.parameterAsString(parameters, self.WEIGHT_FIELD, context)
            idx_field = source.fields().lookupField(weight_field)

        center_type = self.parameterAsEnum(parameters, self.CENTER, context)

        cell_fields = QgsFields()
        cell_fields.append(QgsField("count", QVariant.Int))
        cell_field_list = ["min", "max", "sum", "mean", "std_dev", "var"]
        for field_name in cell_field_list:
            cell_fields.append(QgsField(field_name, QVariant.Double))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                          cell_fields, QgsWkbTypes.Polygon, source.sourceCrs())
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        anchor_fields = QgsFields()
        anchor_fields.append(QgsField("distance", QVariant.Double))
        anchor_fields.append(QgsField("direction", QVariant.String))
        (anchor, anchor_id) = self.parameterAsSink(parameters, self.OUTPUT_ANCHOR, context,
                          anchor_fields, QgsWkbTypes.LineString, source.sourceCrs())
        if anchor is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_ANCHOR))

        # Center : X, Center Y. if not provided, the center of point layer will be used
        source_crs = iface.mapCanvas().mapSettings().destinationCrs()
        target_crs = source.sourceCrs()
        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
        
        extent = source.sourceExtent()
        if center_type == 1:
            extent = iface.mapCanvas().extent()
        elif center_type == 2:
            extent = iface.mapCanvas().fullExtent()
            
        if center_type != 0 and source_crs != target_crs:
           extent = transform.transformBoundingBox(extent);
                
        center_point = extent.center(); # QgsPoint

        minx = extent.xMinimum()
        miny = extent.yMinimum()
        maxx = extent.xMaximum()
        maxy = extent.yMaximum()

        radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0

        #. create spatial index
        spatial_index = QgsSpatialIndex(source)

        step_angle = 360.0 / self.DEFAULT_SEGS
        half_step = step_angle / 2.0

        minVal = sys.float_info.max
        maxVal = sys.float_info.min
        centroid_features = {}
        for idx_side in range(self.DEFAULT_SEGS):
            from_deg = (idx_side * step_angle) - half_step
            to_deg = ((idx_side + 1) * step_angle) - half_step
            feedback.setProgress(int(100 * idx_side / self.DEFAULT_SEGS))

            cell = self.create_cell(center_point, from_deg, to_deg, radius)

            # sptial query
            hasIntersections = False
            points = spatial_index.intersects(cell.boundingBox())
            if len(points) > 0:
                hasIntersections = True

            visitor = StatisticsVisitor()
            if hasIntersections:
                for fid in points:
                    request = QgsFeatureRequest().setFilterFid(fid)
                    point_feature = next(source.getFeatures(request))
                    if cell.contains(point_feature.geometry()):
                        if idx_field >= 0 :
                            weight = str(point_feature.attributes()[idx_field])
                            try:
                                visitor.visit(float(weight))
                            except:
                                pass  # Ignore fields with non-numeric values
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
        for idx_side in range(self.DEFAULT_SEGS):
            cell_feature = centroid_features[idx_side]
            value = cell_feature.attributes()[3]
            linear_trans_value = (value - minVal) / (maxVal - minVal);
            adjusted_radius = linear_trans_value * radius
            if adjusted_radius > 0:
                from_deg = (idx_side * step_angle) - half_step
                to_deg = ((idx_side + 1) * step_angle) - half_step
                cell = self.create_cell(center_point, from_deg, to_deg, adjusted_radius)
                cell_feature.setGeometry(cell)
                sink.addFeature(cell_feature, QgsFeatureSink.FastInsert)

        radius_step = radius / 5
        center =  QgsGeometry.fromPointXY(center_point)
        for idx_side in range(5):
            buffer_radius = radius_step * (idx_side + 1)
            ring_anchor = center.buffer(buffer_radius, 32)
            ring_anchor = QgsGeometry(ring_anchor.constGet().boundary())
            
            anchor_feature = QgsFeature(anchor_fields)
            anchor_feature.setGeometry(ring_anchor)
            anchor_feature.setAttributes([buffer_radius, None])
            anchor.addFeature(anchor_feature, QgsFeatureSink.FastInsert)

        north = ['E', 'ENE', 'NE', 'NNE', 'N', 'NNW', 'NW', 'WNW', 'W',  'WSW', 'SW', 'SSW', 'S', 'SSE', 'SE', 'ESE']
        for idx_side in range(16):
            degree = 22.5 * idx_side
            anchor_line = self.create_line(center_point, degree, radius)
            anchor_feature = QgsFeature(anchor_fields)
            anchor_feature.setGeometry(anchor_line)
            anchor_feature.setAttributes([None, north[idx_side]])
            anchor.addFeature(anchor_feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}


    # create_point
    def create_point(self, centroid, radian, radius):
        dx = math.cos(radian) * radius
        dy = math.sin(radian) * radius

        return QgsPointXY(centroid.x() + dx, centroid.y() + dy)


    # create_cell
    def create_cell(self, centroid, from_deg, to_deg, radius):
        step = abs(to_deg - from_deg) / self.DEFAULT_SEGS

        outer_ring = []
        outer_ring.append(centroid)

        # second outer
        for index in range(self.DEFAULT_SEGS, -1, -1):
            radian = math.radians(from_deg + (index * step))
            outer_ring.append(self.create_point(centroid, radian, radius))

        return QgsGeometry.fromPolygonXY([outer_ring])

    # create_line
    def create_line(self, centroid, degree, radius):
        outer_ring = []

        outer_ring.append(centroid)
        outer_ring.append(self.create_point(centroid, math.radians(degree), radius))

        return QgsGeometry.fromPolylineXY(outer_ring)
